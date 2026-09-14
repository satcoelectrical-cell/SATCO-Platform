import json
from dataclasses import replace
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.ai.standards_intelligence import (
    MAX_INPUT_BYTES,
    MAX_SUGGESTIONS,
    compose_envelope,
    validate_output,
)
from app.adapters.standard_source_object_store import StandardSourceObjectStore
from app.adapters.standard_source_providers import ProviderFragment
from app.adapters.supporting_file_object_store import InMemoryPrivateSupportingFileObjectStore
from app.models.technical_report_command import (
    ReviseTechnicalReportStandardsBasis,
    TechnicalReportActor,
    TechnicalReportCommandMetadata,
    TechnicalReportStandardBasisSelection,
    TechnicalReportValidationError,
)
from app.exceptions.technical_report import TechnicalReportHistoricalBasisIncomplete
from app.schemas.standards import SourceSnapshotCreate, StandardsIntelligenceRunCreate
from app.repositories.standards_repository import StandardsRepository
from app.services.standards_service import StandardsError, StandardsService

def test_suggestion_limit_fails_closed():
    at_limit = {"suggestions":[{"handle":"h","rationale_code":"c","advisory":f"review {item}"} for item in range(MAX_SUGGESTIONS)]}
    assert len(validate_output(json.dumps(at_limit).encode(), known_handles={"h"}, known_codes={"c"}).suggestions) == 12
    payload = {"suggestions":[{"handle":"h","rationale_code":"c","advisory":"review"}] * (MAX_SUGGESTIONS + 1)}
    with pytest.raises(ValueError): validate_output(json.dumps(payload).encode(), known_handles={"h"}, known_codes={"c"})


def test_ai_context_accepts_exact_32768_bytes_and_rejects_plus_one():
    overhead = len(compose_envelope(handles=("",), rationale_codes=("eligible",), purpose="x"))
    exact = compose_envelope(handles=("x" * (MAX_INPUT_BYTES - overhead),), rationale_codes=("eligible",), purpose="x")
    assert len(exact) == 32768
    with pytest.raises(ValueError, match="CONTEXT_LIMIT"):
        compose_envelope(handles=("x" * (MAX_INPUT_BYTES - overhead + 1),), rationale_codes=("eligible",), purpose="x")


def test_context_identifier_and_retrieval_fragment_limits_are_exact():
    snapshots = [uuid4() for _ in range(8)]
    assertions = [uuid4() for _ in range(32)]
    assert len(StandardsIntelligenceRunCreate(purpose="bounded", snapshot_ids=snapshots, assertion_ids=assertions).assertion_ids) == 32
    assert len(SourceSnapshotCreate(edition_id=uuid4(), provider_id="registry_metadata", purpose="reference_only", fragments=[{"location": f"c-{item}"} for item in range(8)]).fragments) == 8
    with pytest.raises(ValidationError):
        StandardsIntelligenceRunCreate(purpose="bounded", snapshot_ids=snapshots, assertion_ids=assertions + [uuid4()])
    with pytest.raises(ValidationError):
        SourceSnapshotCreate(edition_id=uuid4(), provider_id="registry_metadata", purpose="reference_only", fragments=[{"location": f"c-{item}"} for item in range(9)])


def test_report_basis_selection_accepts_16_and_rejects_17_without_truncation():
    organization_id = uuid4()
    metadata = TechnicalReportCommandMetadata(
        actor=TechnicalReportActor(actor_id=1, organization_id=organization_id),
        rationale="Human reviewed bounded basis",
        correlation_id=uuid4(), idempotency_id=uuid4(), command_id=uuid4(),
    )
    selections = tuple(TechnicalReportStandardBasisSelection(
        authorized_handle=f"handle-{item}", materiality="reference_only",
        selection_rationale="Human selected reference",
    ) for item in range(17))
    accepted = ReviseTechnicalReportStandardsBasis(
        metadata=metadata, report_id=uuid4(), expected_version=1,
        expected_draft_revision_id=uuid4(), selections=selections[:16],
    )
    assert len(accepted.selections) == 16
    with pytest.raises(TechnicalReportValidationError, match="1..16"):
        ReviseTechnicalReportStandardsBasis(
            metadata=metadata, report_id=uuid4(), expected_version=1,
            expected_draft_revision_id=uuid4(), selections=selections,
        )


def test_source_bytes_accept_exact_item_and_aggregate_limits_and_reject_plus_one(
    db_session, admin_user
):
    from tests.test_standards_migrations import _foundation_fixture

    fixture = _foundation_fixture(db_session, admin_user)
    fragments = {
        f"clause-{item}": ProviderFragment(
            f"clause-{item}", b"x" * 8192, "text/plain", f"v{item}", f"{item + 1:064x}"
        ) for item in range(4)
    }
    fragments["too-large"] = ProviderFragment(
        "too-large", b"x" * 8193, "text/plain", "v-large", "f" * 64
    )
    fragments["aggregate-plus-one"] = ProviderFragment(
        "aggregate-plus-one", b"x", "text/plain", "v-plus", "e" * 64
    )

    class BoundaryProvider:
        provider_id = "test_provider"
        adapter_policy_id = "boundary_fixture_v1"
        adapter_policy_version = "1"

        def retrieve(self, *, location, purpose, provider_token=None):
            return fragments[location]

    service = StandardsService(
        db_session, StandardsRepository(db_session),
        providers={"test_provider": BoundaryProvider()},
        objects=StandardSourceObjectStore(InMemoryPrivateSupportingFileObjectStore()),
    )
    status, body = service.create_source_snapshots(
        actor_id=fixture["actor"], organization_id=fixture["organization"],
        project_id=fixture["project"],
        data=SourceSnapshotCreate(
            edition_id=fixture["edition"], provider_id="test_provider",
            purpose="material_support",
            fragments=[{"location": f"clause-{item}"} for item in range(4)],
        ), idempotency_key="ret-exact-32768",
    )
    assert status == 201 and len(body["items"]) == 4
    with pytest.raises(StandardsError, match="RESOURCE_LIMIT_EXCEEDED"):
        service.create_source_snapshots(
            actor_id=fixture["actor"], organization_id=fixture["organization"],
            project_id=fixture["project"],
            data=SourceSnapshotCreate(
                edition_id=fixture["edition"], provider_id="test_provider",
                purpose="material_support", fragments=[{"location": "too-large"}],
            ), idempotency_key="ret-8193",
        )
    with pytest.raises(StandardsError, match="RESOURCE_LIMIT_EXCEEDED"):
        service.create_source_snapshots(
            actor_id=fixture["actor"], organization_id=fixture["organization"],
            project_id=fixture["project"],
            data=SourceSnapshotCreate(
                edition_id=fixture["edition"], provider_id="test_provider",
                purpose="material_support",
                fragments=[{"location": f"clause-{item}"} for item in range(4)]
                + [{"location": "aggregate-plus-one"}],
            ), idempotency_key="ret-32769",
        )


def test_report_provenance_accepts_32_and_rejects_33_without_partial_revision():
    from tests.test_technical_report_standards import _Standards, _metadata, _stack

    class ManyStandards(_Standards):
        def resolve_selection(self, _actor, _scope, handle, materiality, assertion_id, _now):
            assert handle.startswith("handle-") and materiality == "material_support"
            source = SimpleNamespace(**{
                **vars(self.source), "id": uuid4(), "source_location": f"clause-{handle}"
            })
            return (
                source, self.edition, self.identity, self.standing, self.rights,
                self.applicability, None, None, None,
            )

    def arrange(retained_count):
        service, uow, actor, report = _stack(standards=ManyStandards())
        original = report.provenance[0]
        retained = tuple(replace(original, entry_id=uuid4(), ordinal=item) for item in range(retained_count))
        object.__setattr__(report, "_provenance", retained)
        selections = tuple(TechnicalReportStandardBasisSelection(
            authorized_handle=f"handle-{item}", materiality="material_support",
            selection_rationale="Human selected material basis",
        ) for item in range(16))
        command = ReviseTechnicalReportStandardsBasis(
            metadata=_metadata(actor), report_id=report.id, expected_version=report.version,
            expected_draft_revision_id=report.draft_revision_id, selections=selections,
        )
        return service, uow, report, command

    service, _, report, command = arrange(16)
    response = service.attach_standards_basis(command)
    assert len(response.report.provenance) == 32

    service, uow, report, command = arrange(17)
    version = report.version
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete, match="provenance limit exceeded"):
        service.attach_standards_basis(command)
    assert report.version == version
    assert uow.commits == 1  # draft creation only; rejected revision did not commit
