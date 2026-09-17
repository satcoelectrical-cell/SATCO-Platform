from conftest import TEST_DATABASE_REVISION
"""PATCH-054 Batch-4 exact 15-vector Technical Report standards evidence."""

from dataclasses import fields, replace
from datetime import datetime, timezone
import hashlib
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError

from app.ai.technical_report_assistant import safe_report_source_context
from app.api.v1.routers.technical_reports import _provenance_dto
from app.enums.technical_report import (
    TechnicalReportAvailabilityStatus,
    TechnicalReportIntegrityAlgorithm,
    TechnicalReportLifecycle,
    TechnicalReportPurpose,
    TechnicalReportSourceClass,
    TechnicalReportSourceType,
    TechnicalReportVerificationStatus,
)
from app.exceptions.technical_report import (
    TechnicalReportHistoricalBasisIncomplete,
    TechnicalReportIdempotencyConflict,
    TechnicalReportVersionConflict,
)
from app.models.technical_report import TechnicalReport
from app.models.technical_report_command import (
    AcceptExactTechnicalReportDraft,
    AcceptanceConfirmation,
    ContextualLocator,
    CreateTechnicalReportDraft,
    CreateTechnicalReportSuccessor,
    PreliminaryQualification,
    ReviseTechnicalReportDraft,
    ReviseTechnicalReportStandardsBasis,
    StandardHistoricalBasisV1,
    StandardLocator,
    TechnicalReportActor,
    TechnicalReportCommandMetadata,
    TechnicalReportContent,
    TechnicalReportProvenanceEntry,
    TechnicalReportStandardBasisSelection,
    canonical_json,
    standard_basis_digest,
)
from app.services.technical_report_service import TechnicalReportService


NOW = datetime(2026, 9, 12, 8, 0, tzinfo=timezone.utc)
STANDARD_HISTORICAL_BASIS_V1_FIELDS = (
    "schema_version", "basis_id", "materiality", "selection_rationale",
    "standard_identity_id", "issuer", "designation", "title", "identity_digest",
    "standard_edition_id", "edition_designation", "official_publication_identifier",
    "publication_date", "edition_digest", "standing_observation_id", "standing",
    "standing_observation_digest", "standing_acknowledged_by_id",
    "standing_acknowledgement_rationale", "source_snapshot_id", "source_provider_id",
    "source_location", "immutable_provider_token", "provider_version_digest",
    "provider_handle_key_version", "source_availability_status", "byte_count",
    "snapshot_digest", "content_digest", "rights_binding_id", "rights_binding_version",
    "rights_digest", "rights_basis", "rights_status", "evaluated_capabilities",
    "ai_processing_permission", "rights_decided_at", "applicability_id",
    "applicability_revision", "applicability_digest", "applicability_status",
    "applicability_role", "assertion_id", "assertion_kind", "assertion_digest",
    "assertion_origin", "assertion_verification_status", "assertion_verified_by_id",
    "assertion_current_use_eligible", "intelligence_interaction_id",
    "intelligence_provider_id", "intelligence_model", "intelligence_template_digest",
    "intelligence_input_digest", "intelligence_output_digest",
    "intelligence_processor_decision", "selected_by_id", "selected_at",
    "report_revision_id", "accepted_report_id", "accepted_report_version",
    "accepted_at", "basis_digest",
)


class _Clock:
    def now(self):
        return NOW


class _Recorder:
    def __init__(self): self.values = []
    def record(self, value): self.values.extend(value if isinstance(value, tuple) else (value,))


class _Idempotency:
    def __init__(self): self.values = {}; self.pending = {}
    def find(self, key, fingerprint):
        current = self.values.get(key) or self.pending.get(key)
        if current is None: return None
        if current[0] != fingerprint: raise TechnicalReportIdempotencyConflict()
        return current[1] if len(current) == 2 else None
    def reserve(self, key, fingerprint): self.pending[key] = (fingerprint,)
    def record_result(self, key, result): self.values[key] = (self.pending.pop(key)[0], result)


class _Repository:
    def __init__(self): self.values = {}
    def add(self, report): self.values[report.id] = report
    def get_scoped(self, report_id, organization_id):
        report = self.values.get(report_id)
        return report if report is not None and report.organization_id == organization_id else None
    def persist_draft_expected_version(self, report, expected_version):
        return report.version == expected_version + 1
    def persist_acceptance_expected_version(self, report, expected_version):
        return report.version == expected_version + 1
    def list_successors_scoped(self, *_args, **_kwargs):
        return SimpleNamespace(items=(), total=0, page=1, size=20)


class _Authorization:
    def require(self, _request): return None


class _FinalRecheck:
    def __init__(self): self.calls = 0
    def require_current(self, _request): self.calls += 1


class _Standards:
    def __init__(self, *, materiality="material_support", standing="current", applicability=True):
        self.identity = SimpleNamespace(
            id=uuid4(), issuer_display="IEC", issuer_key="iec", designation="60034",
            designation_key="60034", title="Rotating machines", identity_digest="1" * 64,
        )
        self.edition = SimpleNamespace(
            id=uuid4(), edition_designation="2026", edition_key="2026",
            official_publication_identifier="IEC 60034:2026", publication_date=None,
            edition_digest="2" * 64,
        )
        self.standing = SimpleNamespace(id=uuid4(), standing=standing, observation_digest="3" * 64)
        self.rights = SimpleNamespace(
            id=uuid4(), version=1, rights_digest="4" * 64,
            rights_basis="organization_license", rights_status="active",
            allow_metadata_visibility=True, allow_content_storage=True, allow_indexing=True,
            allow_excerpt_display=True, allow_source_retrieval=True,
            allow_derived_retention=True, allow_derived_current_use=True,
            ai_processing_permission="prohibited",
        )
        self.source = SimpleNamespace(
            id=uuid4(), request_purpose=materiality, source_provider_id="licensed_registry",
            source_location="clause 8.2", availability_status="available", byte_count=64,
            snapshot_digest="5" * 64, content_sha256="6" * 64,
            provider_version_digest=None, provider_handle_key_version=None,
            integrity_verified=True,
        )
        self.applicability = (
            SimpleNamespace(
                id=uuid4(), revision=1, applicability_digest="7" * 64,
                status="applicable", applicability_role="design_basis",
            ) if applicability else None
        )
        self.handle = "opaque-authorized-handle"
        self.current_calls = 0
        self.fail_current = False

    def list_candidates(self, _actor, _scope, _now):
        return ((self.source, self.edition, self.identity, self.standing, self.rights),)

    def resolve_selection(self, _actor, _scope, handle, materiality, assertion_id, _now):
        if handle != self.handle or materiality != self.source.request_purpose or assertion_id is not None:
            raise TechnicalReportHistoricalBasisIncomplete()
        return (
            self.source, self.edition, self.identity, self.standing, self.rights,
            self.applicability, None, None, None,
        )

    def require_current(self, _actor, _scope, bases, _now):
        self.current_calls += 1
        if self.fail_current: raise TechnicalReportHistoricalBasisIncomplete()
        assert all(standard_basis_digest(item) == item.basis_digest for item in bases)


class _Uow:
    def __init__(self, standards=None):
        self.technical_reports = _Repository(); self.authorization = _Authorization()
        self.references = SimpleNamespace(validate=lambda _request: None)
        self.historical = SimpleNamespace(resolve=lambda _request: None)
        self.final_recheck = _FinalRecheck(); self.standards = standards or _Standards()
        self.audit = _Recorder(); self.domain_events = _Recorder(); self.rejection_audit = _Recorder()
        self.idempotency = _Idempotency(); self.commits = 0
    def __enter__(self): return self
    def __exit__(self, *_args): return None
    def commit(self): self.commits += 1


def _metadata(actor, rationale="Human governed selection"):
    return TechnicalReportCommandMetadata(actor, rationale, uuid4(), uuid4(), uuid4())


def _content(value="Engineering assessment"):
    return TechnicalReportContent("Motor scope", value, (), "Known uncertainty", (), "Conclusion", ())


def _stack(*, standards=None):
    actor = TechnicalReportActor(7, uuid4()); uow = _Uow(standards)
    service = TechnicalReportService(lambda: uow, _Clock())
    contextual = TechnicalReportProvenanceEntry(
        uuid4(), 0, TechnicalReportSourceClass.CONTEXTUAL_NON_MATERIAL,
        TechnicalReportSourceType.CONTEXTUAL, False, None, "context",
        TechnicalReportVerificationStatus.UNVERIFIED,
        TechnicalReportAvailabilityStatus.AVAILABLE, "Human", (),
        ContextualLocator(uuid4(), "engineering_context"), None, None,
    )
    created = service.create_draft(CreateTechnicalReportDraft(
        _metadata(actor), actor.organization_id, 11, 12, actor.actor_id,
        TechnicalReportPurpose.ENGINEERING_ANALYSIS, _content(),
        PreliminaryQualification(False), (contextual,),
    ))
    return service, uow, actor, uow.technical_reports.values[created.report_id]


def _attach(service, uow, actor, report, *, acknowledgement=None, command=None):
    command = command or ReviseTechnicalReportStandardsBasis(
        _metadata(actor), report.id, report.version, report.draft_revision_id,
        (TechnicalReportStandardBasisSelection(
            uow.standards.handle, uow.standards.source.request_purpose,
            "Selected by the Report owner", acknowledgement,
        ),),
    )
    return service.attach_standards_basis(command), command


def _accept(service, actor, report):
    return service.accept_exact_draft(AcceptExactTechnicalReportDraft(
        _metadata(actor, "Accept exact governed revision"), report.id,
        AcceptanceConfirmation(report.version, report.draft_revision_id, True),
    ))


def _standard_entry(report):
    return next(item for item in report.provenance if isinstance(item.locator, StandardHistoricalBasisV1))


def _legacy_entry():
    locator = StandardLocator("STD", "Issuer", "2020", "1", "legacy text")
    return TechnicalReportProvenanceEntry(
        uuid4(), 0, TechnicalReportSourceClass.STANDARDS_MATERIAL,
        TechnicalReportSourceType.STANDARD, True, None, "legacy basis",
        TechnicalReportVerificationStatus.VERIFIED,
        TechnicalReportAvailabilityStatus.AVAILABLE, "issuer", (), locator,
        TechnicalReportIntegrityAlgorithm.SHA256,
        hashlib.sha256(canonical_json(locator)).hexdigest(),
    )


def test_p054_rpt_01_deterministic_safe_candidates():
    service, uow, actor, report = _stack()
    first = service.standards_candidates(actor, report.id); second = service.standards_candidates(actor, report.id)
    assert first == second and len(first) == 1 and first[0]["materiality"] == "material_support"
    assert first[0]["authorized_handle"] != uow.standards.handle
    assert not ({"content_sha256", "object_key", "provider_handle_ciphertext"} & first[0].keys())


def test_p054_rpt_02_opaque_attachment_is_canonical_revision_and_replay():
    service, uow, actor, report = _stack(); old_revision = report.draft_revision_id
    response, command = _attach(service, uow, actor, report); basis = _standard_entry(report).locator
    assert response.version == 2 and report.draft_revision_id != old_revision
    assert basis.report_revision_id == report.draft_revision_id
    assert basis.standard_identity_id == uow.standards.identity.id
    assert standard_basis_digest(basis) == basis.basis_digest
    assert response.result.events[0].standards_basis_ids == (basis.basis_id,)
    assert tuple(field.name for field in fields(StandardHistoricalBasisV1)) == STANDARD_HISTORICAL_BASIS_V1_FIELDS
    _accept(service, actor, report)
    commits = uow.commits
    retry = replace(command, metadata=replace(
        command.metadata, correlation_id=uuid4(), command_id=uuid4(),
    ))
    replay = service.attach_standards_basis(retry)
    assert replay.result == response.result and uow.commits == commits


def test_p054_rpt_03_raw_and_legacy_standard_submission_rejected():
    actor = TechnicalReportActor(7, uuid4())
    command = CreateTechnicalReportDraft(
        _metadata(actor), actor.organization_id, 11, 12, actor.actor_id,
        TechnicalReportPurpose.ENGINEERING_ANALYSIS, _content(),
        PreliminaryQualification(False), (_legacy_entry(),),
    )
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete): TechnicalReport.create(command, NOW)


def test_p054_rpt_04_legacy_read_is_byte_stable_and_explicitly_unattested():
    entry = _legacy_entry(); before = canonical_json(entry.locator)
    accepted = _provenance_dto(entry); draft = _provenance_dto(entry, legacy_draft=True)
    assert accepted.locator.locator_type == "legacy_unattested_reference"
    assert draft.locator.locator_type == "legacy_conversion_required"
    assert canonical_json(entry.locator) == before


def test_p054_rpt_05_legacy_draft_must_convert_before_revision_or_acceptance():
    service, _uow, actor, report = _stack(); object.__setattr__(report, "_provenance", (_legacy_entry(),))
    revise = ReviseTechnicalReportDraft(
        _metadata(actor), report.id, report.version, report.draft_revision_id,
        _content("Changed"), report.qualification, report.provenance,
    )
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete): service.revise_draft(revise)
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete): _accept(service, actor, report)


def test_p054_rpt_06_acceptance_runs_rechecks_and_freezes_full_basis():
    service, uow, actor, report = _stack(); _attach(service, uow, actor, report)
    result = _accept(service, actor, report); basis = _standard_entry(report).locator
    snapshot_basis = next(
        item.locator for item in report.accepted_snapshot.provenance
        if isinstance(item.locator, StandardHistoricalBasisV1)
    )
    assert report.lifecycle is TechnicalReportLifecycle.ACCEPTED and basis == snapshot_basis
    assert (basis.accepted_report_id, basis.accepted_report_version, basis.accepted_at) == (report.id, result.version, NOW)
    assert uow.standards.current_calls == 1 and uow.final_recheck.calls == 1


def test_p054_rpt_07_stale_material_basis_fails_whole_acceptance():
    service, uow, actor, report = _stack(); _attach(service, uow, actor, report)
    digest = _standard_entry(report).locator.basis_digest; uow.standards.fail_current = True
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete): _accept(service, actor, report)
    assert report.lifecycle is TechnicalReportLifecycle.DRAFT and report.accepted_snapshot is None
    assert _standard_entry(report).locator.basis_digest == digest


def test_p054_rpt_08_stale_report_revision_loses_exact_version_race():
    service, uow, actor, report = _stack(); stale_version, stale_revision = report.version, report.draft_revision_id
    _attach(service, uow, actor, report)
    losing = ReviseTechnicalReportStandardsBasis(
        _metadata(actor), report.id, stale_version, stale_revision,
        (TechnicalReportStandardBasisSelection(uow.standards.handle, "material_support", "Losing command"),),
    )
    with pytest.raises(TechnicalReportVersionConflict): service.attach_standards_basis(losing)


def test_p054_rpt_09_rights_or_applicability_change_fails_final_recheck():
    service, uow, actor, report = _stack(); _attach(service, uow, actor, report)
    uow.standards.fail_current = True
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete): _accept(service, actor, report)
    assert not [event for event in uow.domain_events.values if event.event_type == "TechnicalReportAccepted"]


def test_p054_rpt_10_noncurrent_material_requires_applicability_and_acknowledgement():
    blocked = _Standards(standing="superseded", applicability=False)
    service, uow, actor, report = _stack(standards=blocked)
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete): _attach(service, uow, actor, report)
    permitted = _Standards(standing="superseded", applicability=True)
    service, uow, actor, report = _stack(standards=permitted)
    _attach(service, uow, actor, report, acknowledgement="Reviewed superseded standing")
    basis = _standard_entry(report).locator
    assert basis.standing_acknowledged_by_id == actor.actor_id and basis.applicability_id == permitted.applicability.id


def test_p054_rpt_11_historical_meaning_survives_current_rights_loss_and_tokens_are_masked():
    service, uow, actor, report = _stack(); _attach(service, uow, actor, report); _accept(service, actor, report)
    accepted_digest = report.accepted_snapshot.integrity_digest; uow.standards.fail_current = True
    assert service.get_report(actor, report.id).accepted_snapshot.integrity_digest == accepted_digest
    basis = _standard_entry(report).locator
    context = json.loads(safe_report_source_context(basis)); rendered = _provenance_dto(_standard_entry(report)).locator.model_dump()
    assert "immutable_provider_token" not in context and "immutable_provider_token" not in rendered
    assert context["basis_digest"] == basis.basis_digest


def test_p054_rpt_12_successor_cannot_copy_standard_basis():
    service, uow, actor, report = _stack(); _attach(service, uow, actor, report); _accept(service, actor, report)
    command = CreateTechnicalReportSuccessor(
        _metadata(actor), report.id, report.version, report.workspace_id, report.project_id,
        report.purpose, _content("Successor"), PreliminaryQualification(False), (),
        (_standard_entry(report).entry_id,),
    )
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete): service.create_successor(command)


def test_p054_aud_06_attachment_and_acceptance_events_share_safe_basis_linkage():
    service, uow, actor, report = _stack(); attached, _ = _attach(service, uow, actor, report)
    attached_expected = hashlib.sha256(canonical_json(tuple(
        item.locator.basis_digest for item in attached.report.provenance
        if isinstance(item.locator, StandardHistoricalBasisV1)
    ))).hexdigest()
    accepted = _accept(service, actor, report)
    events = {event.event_type: event for event in uow.domain_events.values}
    assert events["technical_report.standards_basis.attached"].standards_basis_digest == attached_expected
    assert events["technical_report.standards_basis.attached"].standards_basis_ids == tuple(
        item.locator.basis_id for item in attached.report.provenance
        if isinstance(item.locator, StandardHistoricalBasisV1)
    )
    expected = hashlib.sha256(canonical_json(tuple(
        item.locator.basis_digest for item in report.accepted_snapshot.provenance
        if isinstance(item.locator, StandardHistoricalBasisV1)
    ))).hexdigest()
    assert accepted.result.events[0].standards_basis_digest == expected
    assert attached.result.events[0].standards_basis_digest != accepted.result.events[0].standards_basis_digest
    audits = {record.operation: record for record in uow.audit.values}
    assert (
        audits["ReviseTechnicalReportStandardsBasis"].event_id,
        audits["ReviseTechnicalReportStandardsBasis"].standards_basis_digest,
    ) == (
        events["technical_report.standards_basis.attached"].event_id,
        events["technical_report.standards_basis.attached"].standards_basis_digest,
    )
    assert (
        audits["AcceptExactTechnicalReportDraft"].event_id,
        audits["AcceptExactTechnicalReportDraft"].standards_basis_digest,
    ) == (
        events["TechnicalReportAccepted"].event_id,
        events["TechnicalReportAccepted"].standards_basis_digest,
    )
    assert all("immutable_provider_token" not in canonical_json(event).decode() for event in events.values())


def test_p054_db_02_migration_two_exact_columns_validators_and_cutover(db_session):
    inspector = inspect(db_session.get_bind())
    columns = {item["name"] for item in inspector.get_columns("technical_report_provenance_entries")}
    assert {
        "standard_basis_schema_version", "standard_basis", "standard_basis_digest",
        "standards_basis_materiality", "standard_edition_id", "standard_source_snapshot_id",
        "standard_assertion_id", "standard_intelligence_run_id",
    } <= columns
    assert "technical_report_standards_basis" not in inspector.get_table_names()
    triggers = set(db_session.execute(text(
        "SELECT tgname FROM pg_trigger WHERE tgname LIKE 'trg_technical_report_patch054_%'"
    )).scalars())
    assert triggers == {
        "trg_technical_report_patch054_provenance_guard", "trg_technical_report_patch054_root_guard",
        "trg_technical_report_patch054_final_guard",
    }
    assert db_session.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == TEST_DATABASE_REVISION


def test_p054_db_03_final_guards_are_deferred_and_report_cas_is_single_winner(
    db_session, relationship_domain,
):
    assert db_session.execute(text("""
        SELECT tgdeferrable AND tginitdeferred FROM pg_trigger
        WHERE tgname='trg_technical_report_patch054_final_guard'
    """)).scalar_one() is True
    service, uow, actor, report = _stack()
    first = ReviseTechnicalReportStandardsBasis(
        _metadata(actor), report.id, report.version, report.draft_revision_id,
        (TechnicalReportStandardBasisSelection(uow.standards.handle, "material_support", "First winner"),),
    )
    second = replace(first, metadata=_metadata(actor, "Second contender"))
    service.attach_standards_basis(first)
    with pytest.raises(TechnicalReportVersionConflict): service.attach_standards_basis(second)

    # Exercise the same path through the real PostgreSQL UoW, including the
    # M2 validators, deferred accepted-at linkage, CAS, audit, and outbox.
    from sqlalchemy.orm import sessionmaker
    from app.models.technical_report import TechnicalReportProvenanceRecord, TechnicalReportRecord
    from app.models.technical_report_command import TechnicalReportOutboxRecord
    from app.repositories.technical_report_unit_of_work import SqlAlchemyTechnicalReportUnitOfWork

    actor_row = relationship_domain["actors"]["project_owner"]
    project = relationship_domain["project"]
    workspace = relationship_domain["consumer_workspace"]
    ids = {name: uuid4() for name in (
        "identity", "edition", "standing", "rights", "snapshot", "reference_snapshot",
    )}
    db_session.execute(text("""
      INSERT INTO standard_identities(id,catalog_scope,issuer_key,issuer_display,designation,designation_key,title,
        jurisdiction,normalization_version,metadata_source_reference,identity_digest,created_by)
      VALUES (:identity,'global_trusted','iec-real','IEC',:designation,:designation,'Real integration standard','{}',
        'satco_standard_key_nfkc_casefold_v1','catalog',:identity_digest,:actor);
      INSERT INTO standard_editions(id,standard_identity_id,edition_designation,edition_key,edition_disambiguator,
        jurisdiction,metadata_source_reference,edition_digest,created_by)
      VALUES (:edition,:identity,'2026',:designation,'','{}','catalog',:edition_digest,:actor);
      INSERT INTO standard_edition_standing_observations(id,standard_edition_id,standing,observed_effective_at,
        source_reference,source_digest,actor_kind,created_by,observation_digest)
      VALUES (:standing,:edition,'current',now(),'catalog',:standing_digest,'human',:actor,:standing_digest);
      INSERT INTO standard_rights_bindings(id,organization_id,standard_edition_id,source_provider_id,rights_basis,
        rights_status,allow_metadata_visibility,allow_content_storage,allow_indexing,allow_excerpt_display,
        allow_source_retrieval,allow_derived_retention,allow_derived_current_use,ai_processing_permission,
        approved_processor_policy_ids,effective_from,rights_authority_reference,rights_authority_digest,
        reason_code,rights_digest,created_by)
      VALUES (:rights,:organization,:edition,'licensed_registry','organization_license','active',true,true,true,true,
        true,true,true,'prohibited','[]',:effective_from,'rights-record',:rights_digest,
        'created',:rights_digest,:actor);
      INSERT INTO standard_source_snapshots(id,organization_id,project_id,standard_identity_id,standard_edition_id,
        source_provider_id,adapter_policy_id,adapter_policy_version,source_location,availability_status,
        request_purpose,correlation_id,object_key,object_version,content_sha256,byte_count,media_type,
        rights_binding_id,rights_binding_version,rights_digest,evaluated_capabilities,standing_observation_id,
        standing_observation_digest,source_metadata_digest,integrity_verified,integrity_verified_at,snapshot_digest,
        retrieved_at,retrieved_by)
      VALUES (:snapshot,:organization,:project,:identity,:edition,'licensed_registry','policy','1','clause 8.2',
        'available','material_support',:correlation,'standards/real','v1',:content_digest,64,'text/plain',:rights,1,
        :rights_digest,'{}',:standing,:standing_digest,:source_metadata_digest,true,now(),:snapshot_digest,now(),:actor)
    """), {
        **ids, "organization": project.organization_id, "project": project.id,
        "actor": actor_row.id, "designation": f"real-{uuid4().hex}", "correlation": uuid4(),
        "identity_digest": "1" * 64, "edition_digest": "2" * 64,
        "standing_digest": "3" * 64, "rights_digest": "4" * 64,
        "snapshot_digest": "5" * 64, "content_digest": "6" * 64,
        "source_metadata_digest": "7" * 64,
        "effective_from": datetime(2026, 1, 1, tzinfo=timezone.utc),
    })
    db_session.execute(text("""
      INSERT INTO standard_source_snapshots(id,organization_id,project_id,standard_identity_id,standard_edition_id,
        source_provider_id,adapter_policy_id,adapter_policy_version,source_location,availability_status,
        request_purpose,correlation_id,object_key,object_version,provider_handle_ciphertext,
        provider_handle_key_version,provider_version_digest,content_sha256,byte_count,media_type,
        rights_binding_id,rights_binding_version,rights_digest,evaluated_capabilities,standing_observation_id,
        standing_observation_digest,source_metadata_digest,integrity_verified,integrity_verified_at,snapshot_digest,
        retrieved_at,retrieved_by)
      VALUES (:reference_snapshot,:organization,:project,:identity,:edition,'licensed_registry','policy','1',
        'metadata only','rights_restricted','reference_only',:correlation,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,
        :rights,1,:rights_digest,'{}',:standing,:standing_digest,:source_metadata_digest,false,now(),
        :reference_digest,now(),:actor)
    """), {
        **ids, "organization": project.organization_id, "project": project.id,
        "actor": actor_row.id, "correlation": uuid4(), "rights_digest": "4" * 64,
        "standing_digest": "3" * 64, "source_metadata_digest": "8" * 64,
        "reference_digest": "9" * 64,
    })
    db_session.execute(text("SET LOCAL ROLE satco_runtime"))
    assert db_session.execute(text("SELECT current_user")).scalar_one() == "satco_runtime"
    assert db_session.execute(text(
        "SELECT has_column_privilege(current_user,'technical_reports','predecessor_report_id','UPDATE')"
    )).scalar_one() is False
    factory = sessionmaker(
        bind=db_session.get_bind(), expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    real_service = TechnicalReportService(
        lambda: SqlAlchemyTechnicalReportUnitOfWork(factory), _Clock(),
    )
    real_actor = TechnicalReportActor(actor_row.id, project.organization_id)
    context = TechnicalReportProvenanceEntry(
        uuid4(), 0, TechnicalReportSourceClass.CONTEXTUAL_NON_MATERIAL,
        TechnicalReportSourceType.CONTEXTUAL, False, None, "context",
        TechnicalReportVerificationStatus.UNVERIFIED,
        TechnicalReportAvailabilityStatus.AVAILABLE, "Human", (),
        ContextualLocator(uuid4(), "engineering_context"), None, None,
    )
    created = real_service.create_draft(CreateTechnicalReportDraft(
        _metadata(real_actor), project.organization_id, workspace.id, project.id,
        real_actor.actor_id, TechnicalReportPurpose.ENGINEERING_ANALYSIS,
        _content("Real PostgreSQL path"), PreliminaryQualification(False), (context,),
    ))
    candidate = real_service.standards_candidates(real_actor, created.report_id)[0]
    revised = real_service.attach_standards_basis(ReviseTechnicalReportStandardsBasis(
        _metadata(real_actor), created.report_id, created.version,
        created.draft_revision.revision_id,
        (TechnicalReportStandardBasisSelection(
            candidate["authorized_handle"], "material_support", "Real selection",
        ),),
    ))
    accepted = real_service.accept_exact_draft(AcceptExactTechnicalReportDraft(
        _metadata(real_actor), created.report_id,
        AcceptanceConfirmation(revised.version, revised.draft_revision.revision_id, True),
    ))
    db_session.expire_all()
    root = db_session.get(TechnicalReportRecord, created.report_id)
    standard_row = db_session.query(TechnicalReportProvenanceRecord).filter_by(
        technical_report_id=created.report_id, source_type="standard",
    ).one()
    assert root.lifecycle == "accepted" and accepted.version == 3
    assert standard_row.standard_basis["accepted_report_id"] == str(created.report_id)
    assert standard_row.standard_basis["accepted_report_version"] == 3
    assert db_session.query(TechnicalReportOutboxRecord).filter_by(
        aggregate_id=created.report_id,
    ).count() == 3
    from app.models.audit_log import AuditLog
    linked_events = {
        row.event_type: row
        for row in db_session.query(TechnicalReportOutboxRecord).filter(
            TechnicalReportOutboxRecord.aggregate_id == created.report_id,
            TechnicalReportOutboxRecord.event_type.in_((
                "technical_report.standards_basis.attached", "TechnicalReportAccepted",
            )),
        )
    }
    linked_audits = {
        row.action: row
        for row in db_session.query(AuditLog).filter(
            AuditLog.entity_uuid == created.report_id,
            AuditLog.action.in_((
                "ReviseTechnicalReportStandardsBasis", "AcceptExactTechnicalReportDraft",
            )),
        )
    }
    for operation, event_type in (
        ("ReviseTechnicalReportStandardsBasis", "technical_report.standards_basis.attached"),
        ("AcceptExactTechnicalReportDraft", "TechnicalReportAccepted"),
    ):
        event = linked_events[event_type]
        audit = linked_audits[operation]
        assert event.payload["report_id"] == str(created.report_id)
        assert event.payload["draft_revision_id"] == str(revised.draft_revision.revision_id)
        assert event.payload["standards_basis_ids"] == [
            standard_row.standard_basis["basis_id"]
        ]
        assert audit.details["event_id"] == str(event.event_id)
        assert audit.details["standards_basis_digest"] == event.payload["standards_basis_digest"]

    # Exercise the SECURITY DEFINER validator that the runtime acceptance
    # trigger invokes.  Closed top-level provenance shape, acknowledgement
    # identity, and material assertion eligibility must all fail closed even
    # when an attacker recomputes every nested digest.
    db_session.execute(text("RESET ROLE"))
    accepted_standard_entry = next(
        entry for entry in root.accepted_snapshot["provenance"]
        if entry["source_type"] == "standard"
    )

    def database_provenance_valid(entry):
        return db_session.execute(
            text("SELECT technical_report_provenance_json_valid(CAST(:entry AS jsonb))"),
            {"entry": json.dumps(entry)},
        ).scalar_one()

    def redigested_entry(entry, **basis_changes):
        result = json.loads(json.dumps(entry))
        basis = result["locator"]
        basis.update(basis_changes)
        basis.pop("basis_digest", None)
        basis["basis_digest"] = hashlib.sha256(canonical_json(basis)).hexdigest()
        result["integrity_digest"] = hashlib.sha256(canonical_json(basis)).hexdigest()
        return result

    assert database_provenance_valid(accepted_standard_entry) is True
    malformed_entry = json.loads(json.dumps(accepted_standard_entry))
    malformed_entry["unchecked_runtime_key"] = malformed_entry.pop("reliance_role")
    assert database_provenance_valid(malformed_entry) is False
    assert database_provenance_valid(redigested_entry(
        accepted_standard_entry,
        standing_acknowledged_by_id=real_actor.actor_id + 1,
        standing_acknowledgement_rationale="Forged Human acknowledgement",
    )) is False
    assert database_provenance_valid(redigested_entry(
        accepted_standard_entry,
        assertion_id=str(uuid4()), assertion_kind="requirement_statement",
        assertion_digest="a" * 64, assertion_origin="human",
        assertion_verification_status="unverified",
        assertion_verified_by_id=real_actor.actor_id,
        assertion_current_use_eligible=False,
    )) is False
    db_session.execute(text("SET LOCAL ROLE satco_runtime"))

    reference_created = real_service.create_draft(CreateTechnicalReportDraft(
        _metadata(real_actor), project.organization_id, workspace.id, project.id,
        real_actor.actor_id, TechnicalReportPurpose.ENGINEERING_ANALYSIS,
        _content("Runtime reference-only path"), PreliminaryQualification(False),
        (replace(context, entry_id=uuid4()),),
    ))
    reference_candidate = next(
        item for item in real_service.standards_candidates(
            real_actor, reference_created.report_id,
        ) if item["materiality"] == "reference_only"
    )
    reference_revised = real_service.attach_standards_basis(
        ReviseTechnicalReportStandardsBasis(
            _metadata(real_actor), reference_created.report_id, reference_created.version,
            reference_created.draft_revision.revision_id,
            (TechnicalReportStandardBasisSelection(
                reference_candidate["authorized_handle"], "reference_only",
                "Runtime reference selection",
            ),),
        )
    )
    reference_row = db_session.query(TechnicalReportProvenanceRecord).filter_by(
        technical_report_id=reference_revised.report_id, source_type="standard",
    ).one()
    assert reference_row.is_material is False
    assert reference_row.standard_basis["materiality"] == "reference_only"

    with pytest.raises(DBAPIError), db_session.begin_nested():
        db_session.execute(text("""
          UPDATE technical_report_provenance_entries
          SET standard_basis=jsonb_set(
                standard_basis,'{accepted_at}',to_jsonb('2026-01-01T00:00:00.000000Z'::text)
              )
          WHERE id=:id
        """), {"id": standard_row.id})

    # A draft cannot pre-stamp its standards basis even if every embedded and
    # relational digest is recomputed coherently; the deferred final guard
    # checks the owning Report lifecycle at transaction finalization.
    second_created = real_service.create_draft(CreateTechnicalReportDraft(
        _metadata(real_actor), project.organization_id, workspace.id, project.id,
        real_actor.actor_id, TechnicalReportPurpose.ENGINEERING_ANALYSIS,
        _content("Forgery guard draft"), PreliminaryQualification(False), (replace(context, entry_id=uuid4()),),
    ))
    second_candidate = real_service.standards_candidates(real_actor, second_created.report_id)[0]
    second_revised = real_service.attach_standards_basis(ReviseTechnicalReportStandardsBasis(
        _metadata(real_actor), second_created.report_id, second_created.version,
        second_created.draft_revision.revision_id,
        (TechnicalReportStandardBasisSelection(
            second_candidate["authorized_handle"], "material_support", "Forgery guard selection",
        ),),
    ))
    second_row = db_session.query(TechnicalReportProvenanceRecord).filter_by(
        technical_report_id=second_created.report_id, source_type="standard",
    ).one()

    def recomputed_basis(**changes):
        basis = json.loads(json.dumps(second_row.standard_basis))
        basis.update(changes)
        basis.pop("basis_digest", None)
        encoded = json.dumps(
            basis, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
        basis_digest = hashlib.sha256(encoded).hexdigest()
        basis["basis_digest"] = basis_digest
        basis_encoded = json.dumps(
            basis, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
        return {
            "id": second_row.id, "basis": json.dumps(basis),
            "basis_digest": basis_digest,
            "integrity_digest": hashlib.sha256(basis_encoded).hexdigest(),
        }

    # A runtime writer cannot forge a self-consistent digest around semantics
    # that no longer match the authoritative rights row.
    with pytest.raises(DBAPIError) as rights_guard, db_session.begin_nested():
        db_session.execute(text("""
          UPDATE technical_report_provenance_entries
          SET standard_basis=CAST(:basis AS jsonb),
              standard_basis_digest=:basis_digest,
              integrity_digest=:integrity_digest
          WHERE id=:id
        """), recomputed_basis(rights_digest="f" * 64))
    assert rights_guard.value.orig.pgcode == "23514"

    with pytest.raises(DBAPIError) as token_guard, db_session.begin_nested():
        db_session.execute(text("""
          UPDATE technical_report_provenance_entries
          SET standard_basis=CAST(:basis AS jsonb),
              standard_basis_digest=:basis_digest,
              integrity_digest=:integrity_digest
          WHERE id=:id
        """), recomputed_basis(
            immutable_provider_token="Zm9yZ2Vk",
            provider_version_digest="a" * 64,
            provider_handle_key_version="v1",
            content_digest=None,
        ))
    assert token_guard.value.orig.pgcode == "23514"

    with pytest.raises(DBAPIError) as actor_guard, db_session.begin_nested():
        db_session.execute(text("""
          UPDATE technical_report_provenance_entries
          SET standard_basis=CAST(:basis AS jsonb),
              standard_basis_digest=:basis_digest,
              integrity_digest=:integrity_digest
          WHERE id=:id
        """), recomputed_basis(selected_by_id=1.5))
    assert actor_guard.value.orig.pgcode == "23514"

    with pytest.raises(DBAPIError) as acceptance_guard, db_session.begin_nested():
        forged_acceptance = recomputed_basis(
            accepted_report_id=str(second_created.report_id),
            accepted_report_version=second_revised.version,
            accepted_at="2026-09-12T08:00:00.000000Z",
        )
        db_session.execute(text("""
          UPDATE technical_report_provenance_entries
          SET standard_basis=CAST(:basis AS jsonb),
              standard_basis_digest=:basis_digest,
              integrity_digest=:integrity_digest
          WHERE id=:id
        """), forged_acceptance)
        db_session.execute(text("SET CONSTRAINTS trg_technical_report_patch054_final_guard IMMEDIATE"))
    assert acceptance_guard.value.orig.pgcode == "23514"

    with pytest.raises(DBAPIError), db_session.begin_nested():
        db_session.execute(text("""
          INSERT INTO technical_report_provenance_entries(
            id,technical_report_id,ordinal,source_class,source_type,is_material,
            reliance_role,verification_status,availability_status,origin_attribution,
            limitations,integrity_algorithm,integrity_digest,
            minimal_historical_representation,standard_identity,issuing_authority,
            edition,clause_or_location
          ) VALUES (
            :id,:report_id,2,'standards_material','standard',true,'legacy','verified',
            'available','legacy issuer','[]','sha256',:digest,
            jsonb_build_object(
              'standard_identity','STD','issuing_authority','Issuer','edition','2020',
              'clause_or_location','1','minimal_representation','legacy text','retrieved_at',null
            ),'STD','Issuer','2020','1'
          )
        """), {
            "id": uuid4(), "report_id": second_created.report_id,
            "digest": hashlib.sha256(canonical_json(StandardLocator(
                "STD", "Issuer", "2020", "1", "legacy text",
            ))).hexdigest(),
        })

    # Identity retirement is authoritative for both new candidate selection
    # and final acceptance of an attached-but-not-yet-accepted basis.
    db_session.execute(text("RESET ROLE"))
    db_session.execute(text(
        "UPDATE standard_identities SET retired_from_new_selection=true WHERE id=:id"
    ), {"id": ids["identity"]})
    db_session.execute(text("SET LOCAL ROLE satco_runtime"))
    assert real_service.standards_candidates(real_actor, second_created.report_id) == ()
    with pytest.raises(TechnicalReportHistoricalBasisIncomplete):
        real_service.accept_exact_draft(AcceptExactTechnicalReportDraft(
            _metadata(real_actor), second_created.report_id,
            AcceptanceConfirmation(
                second_revised.version, second_revised.draft_revision.revision_id, True,
            ),
        ))
