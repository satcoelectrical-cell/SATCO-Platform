from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.adapters.technical_report_capture_source import TechnicalReportCaptureSourceAdapter
from app.enums.engineering_experience_capture import (
    EngineeringExperienceCaptureLifecycle,
    EngineeringExperienceSourceKind,
)
from app.exceptions.engineering_experience_capture import EngineeringExperienceCaptureProtectedNotFound
from app.exceptions.technical_report import TechnicalReportAuthorizationDenied
from app.models.engineering_experience_capture_command import EngineeringExperienceCaptureActor
from app.models.technical_report_command import historical_basis_digest


ORG = UUID("7e7c9d7a-7693-4f75-9bc5-3ef7bf528281")
CAPTURE = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")


def _item(**changes):
    values = dict(
        id=CAPTURE,
        organization_id=ORG,
        project_id=7,
        workspace_id=9,
        discipline="electrical",
        engineering_object_id=None,
        source_kind=EngineeringExperienceSourceKind.OBSERVATION,
        original_content="Observed intermittent voltage loss at terminal X1.",
        source_reference="field-log-14",
        creator_id=11,
        lifecycle=EngineeringExperienceCaptureLifecycle.CAPTURED,
        version=3,
        created_at=datetime(2026, 8, 20, 9, 0, tzinfo=timezone.utc),
    )
    values.update(changes)
    return SimpleNamespace(**values)


class CaptureService:
    def __init__(self, items=None, error=None):
        self.items = [_item()] if items is None else items
        self.error = error
        self.calls = []

    def list_workspace(self, workspace_id, filters, page, size, actor):
        self.calls.append((workspace_id, filters, page, size, actor))
        if self.error:
            raise self.error
        return SimpleNamespace(items=self.items, total=len(self.items), page=page, size=size)


def test_capture_candidate_is_one_bounded_canonical_call_with_exact_provenance():
    service = CaptureService()
    actor = EngineeringExperienceCaptureActor(11, ORG)
    result = TechnicalReportCaptureSourceAdapter(service).list_candidates(
        actor=actor, project_id=7, workspace_id=9, page=1, size=20
    )

    assert len(service.calls) == 1
    assert result.total == 1 and len(result.items) == 1
    candidate = result.items[0]
    assert candidate.capture_id == CAPTURE
    assert candidate.provenance.locator.original_content.startswith("Observed")
    assert candidate.provenance.integrity_digest == historical_basis_digest(
        candidate.provenance.locator.to_domain()
    )
    again = TechnicalReportCaptureSourceAdapter(CaptureService()).list_candidates(
        actor=actor, project_id=7, workspace_id=9, page=1, size=20
    )
    assert again.items[0].provenance.entry_id == candidate.provenance.entry_id


@pytest.mark.parametrize(
    "changes",
    [
        {"organization_id": uuid4()},
        {"project_id": 8},
        {"workspace_id": 10},
        {"lifecycle": EngineeringExperienceCaptureLifecycle.WITHDRAWN},
    ],
)
def test_candidate_scope_or_lifecycle_mismatch_is_all_or_nothing_protected(changes):
    with pytest.raises(TechnicalReportAuthorizationDenied):
        TechnicalReportCaptureSourceAdapter(CaptureService([_item(**changes)])).list_candidates(
            actor=EngineeringExperienceCaptureActor(11, ORG),
            project_id=7,
            workspace_id=9,
            page=1,
            size=20,
        )


def test_canonical_denial_is_translated_without_detail():
    with pytest.raises(TechnicalReportAuthorizationDenied) as caught:
        TechnicalReportCaptureSourceAdapter(
            CaptureService(error=EngineeringExperienceCaptureProtectedNotFound("secret"))
        ).list_candidates(
            actor=EngineeringExperienceCaptureActor(11, ORG),
            project_id=7,
            workspace_id=9,
            page=1,
            size=20,
        )
    assert "secret" not in str(caught.value)
