"""Focused B3-052-MAJ-01 binding, readiness, and transition proof."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.models.audit_log import AuditLog
from app.models.engineering_context import (
    EngineeringContext, EngineeringContextFact,
    EngineeringContextSourceReference, EngineeringContextSubjectReference,
)
from app.models.engineering_deliverable import (
    EngineeringDeliverable, EngineeringDeliverableIdempotency,
    EngineeringDeliverableOutbox,
    EngineeringDeliverableRevision,
)
from app.models.discipline_package import (
    ProjectPackageConfigurationHead, ProjectPackageConfigurationRevision,
    ProjectPackageConfigurationSelection,
)
from app.models.evidence import Evidence
from app.models.evidence_command import EvidenceOutbox
from app.models.package_input_binding import (
    EngineeringContextPackageInputBinding, EvidencePackageInputBinding,
)
from app.adapters.engineering_deliverable import SqlAlchemyDeliverableAuthorization
from app.repositories.engineering_deliverable_unit_of_work import (
    SqlAlchemyEngineeringDeliverableUnitOfWork,
)
from app.schemas.discipline_package_operations import (
    PackageContextBindingRequest, PackageEvidenceBindingRequest,
    PackageCaptureCreateRequest, PackageObjectCreateRequest, PackageTransitionRequest,
)
from app.schemas.engineering_deliverable import (
    DeliverableActor, DeliverableMutationSuccess, TransitionRevisionRequest,
)
from app.services.engineering_deliverable_service import EngineeringDeliverableService
from app.services.electrical_package_service import (
    PackageConflict, PackageDeclarationMismatch, PackageProtectedNotFound,
)
from app.services.instrumentation_package_service import InstrumentationPackageService
from app.services.package_declaration_binding_service import PackageDeclarationBindingService
from test_patch_052_batch_3 import ORG_ID, _factory, _instrumentation_scope


def _object(db_session, engineer_user, project, workspace, kind="transmitter"):
    return InstrumentationPackageService(_factory(db_session)).create_object(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        data=PackageObjectCreateRequest(
            declaration_id=f"instrumentation.object.{kind}",
            primary_identifier_display_value=f"FT-{uuid4().hex[:8]}",
            rationale="Binding fixture",
        ), correlation_id=uuid4(), idempotency_key=uuid4(),
    )[0]


def _context(db_session, engineer_user, project, workspace, obj):
    now = datetime.now(timezone.utc)
    row = EngineeringContext(
        context_key=str(uuid4()), kind="qualified_fact", scope="workspace",
        project_id=project.id, workspace_id=workspace.id,
        owner_id=engineer_user.id, steward_id=engineer_user.id,
        created_by_id=engineer_user.id, authority="engineer_verified_fact",
        lifecycle="current", version=1, created_at=now, updated_at=now,
    )
    db_session.add(row); db_session.flush()
    db_session.add(EngineeringContextFact(context_id=row.id, statement="Verified basis"))
    subject = EngineeringContextSubjectReference(
        context_id=row.id, subject_kind="engineering_object",
        subject_engineering_object_id=obj.id,
    )
    db_session.add(subject); db_session.flush()
    return row, subject


def _evidence(db_session, engineer_user, project, workspace, *, source_kind="engineering_record",
              deliverable_id=None, revision_id=None):
    now = datetime.now(timezone.utc)
    row = Evidence(
        organization_id=ORG_ID, project_id=project.id, workspace_id=workspace.id,
        lifecycle="current", source_kind=source_kind,
        source_reference=str(deliverable_id or uuid4()),
        source_revision=str(revision_id or uuid4()), source_standing="current",
        supported_fact="Human-verified package basis", creator_id=engineer_user.id,
        version=2, created_at=now, updated_at=now,
    )
    db_session.add(row); db_session.flush()
    db_session.add(EvidenceOutbox(
        event_id=uuid4(), aggregate_id=row.id, aggregate_version=2,
        event_type="EvidenceLifecycleTransitioned", payload={"lifecycle": "current"},
        occurred_at=now,
    ))
    db_session.flush()
    return row


def _deliverable(db_session, engineer_user, project, workspace):
    now = datetime.now(timezone.utc)
    row = EngineeringDeliverable(
        organization_id=ORG_ID, project_id=project.id, workspace_id=workspace.id,
        code=f"INS-{uuid4().hex[:8]}", title="Instrument index",
        discipline="instrumentation", deliverable_type="instrument_index",
        external_authority="spreadsheet", standing="planned",
        current_revision_sequence=1, version=1,
        created_by_id=engineer_user.id, updated_by_id=engineer_user.id,
        created_at=now, updated_at=now,
        origin_package_key="instrumentation",
        origin_project_configuration_revision=1,
        origin_declaration_id="instrumentation.deliverable.instrument_index",
    )
    db_session.add(row); db_session.flush()
    revision = EngineeringDeliverableRevision(
        deliverable_id=row.id, organization_id=ORG_ID, project_id=project.id,
        sequence=1, external_label="Rev A", standing="draft", version=1,
        rationale="Initial external revision", created_by_id=engineer_user.id,
        created_at=now, transitioned_by_id=engineer_user.id, transitioned_at=now,
    )
    db_session.add(revision); db_session.flush()
    return row, revision


def _bind_context(
    service, actor, project, workspace, context, subject, input_id,
    *, expected_configuration_revision=1, idempotency_key=None,
):
    return service.bind_context(
        actor_id=actor.id, organization_id=ORG_ID, project_id=project.id,
        workspace_id=workspace.id,
        data=PackageContextBindingRequest(
            input_declaration_id=input_id, context_id=context.id,
            context_subject_reference_id=subject.id, expected_context_version=context.version,
            expected_configuration_revision=expected_configuration_revision,
            rationale="Bind exact Context input",
        ), correlation_id=uuid4(), idempotency_key=idempotency_key or uuid4(),
    )


def _bind_evidence(
    service, actor, project, workspace, evidence, input_id, *, idempotency_key=None,
):
    return service.bind_evidence(
        actor_id=actor.id, organization_id=ORG_ID, project_id=project.id,
        workspace_id=workspace.id,
        data=PackageEvidenceBindingRequest(
            input_declaration_id=input_id, evidence_id=evidence.id,
            expected_evidence_version=evidence.version,
            expected_configuration_revision=1, rationale="Bind exact Evidence input",
        ), correlation_id=uuid4(), idempotency_key=idempotency_key or uuid4(),
    )


def test_context_exact_binding_multiple_explicit_and_stale_version(
    db_session, engineer_user,
):
    project, workspace = _instrumentation_scope(db_session, engineer_user)
    obj = _object(db_session, engineer_user, project, workspace)
    context, subject = _context(db_session, engineer_user, project, workspace, obj)
    service = PackageDeclarationBindingService(_factory(db_session), package_key="instrumentation")

    first_key = uuid4()
    first = _bind_context(
        service, engineer_user, project, workspace, context, subject,
        "instrumentation.measurement_service.input", idempotency_key=first_key,
    )
    replay = _bind_context(
        service, engineer_user, project, workspace, context, subject,
        "instrumentation.measurement_service.input", idempotency_key=first_key,
    )
    assert replay == first
    with pytest.raises(PackageConflict):
        _bind_context(
            service, engineer_user, project, workspace, context, subject,
            "instrumentation.loop_basis.input", idempotency_key=first_key,
        )
    second = _bind_context(service, engineer_user, project, workspace, context, subject,
                           "instrumentation.signal_basis.input")
    assert first.context_declaration_id == "instrumentation.measurement_service.context"
    assert second.context_declaration_id == "instrumentation.signal_basis.context"
    assert db_session.query(EngineeringContextPackageInputBinding).count() == 2
    assert db_session.query(AuditLog).filter_by(action="PackageContextInputBound").count() == 2
    assert db_session.query(EngineeringDeliverableIdempotency).filter_by(
        operation="instrumentation_ctx_binding",
    ).count() == 2

    with pytest.raises(PackageDeclarationMismatch):
        _bind_context(service, engineer_user, project, workspace, context, subject,
                      "electrical.protection_basis.input")
    request = PackageContextBindingRequest(
        input_declaration_id="instrumentation.loop_basis.input", context_id=context.id,
        context_subject_reference_id=subject.id, expected_context_version=1,
        expected_configuration_revision=2, rationale="Reject stale configuration",
    )
    with pytest.raises(PackageConflict):
        service.bind_context(
            actor_id=engineer_user.id, organization_id=ORG_ID,
            project_id=project.id, workspace_id=workspace.id, data=request,
            correlation_id=uuid4(), idempotency_key=uuid4(),
        )

    context.version = 2; db_session.flush()
    result = service.evaluate_context(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        expected_configuration_revision=1, object_ids=(obj.id,),
        correlation_id=uuid4(),
    )
    measurement = next(r for r in result.context_results
                       if r.input_declaration_id == "instrumentation.measurement_service.input")
    assert measurement.status == "STALE"
    assert result.status == "FINDINGS"


def test_legacy_unbound_capture_not_context_and_binding_guards(
    db_session, engineer_user,
):
    project, workspace = _instrumentation_scope(db_session, engineer_user)
    obj = _object(db_session, engineer_user, project, workspace)
    context, subject = _context(db_session, engineer_user, project, workspace, obj)
    evidence = _evidence(db_session, engineer_user, project, workspace)
    capture = InstrumentationPackageService(_factory(db_session)).create_capture(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        data=PackageCaptureCreateRequest(
            declaration_id="instrumentation.measurement_service.input",
            engineering_object_id=obj.id, source_kind="observation",
            original_content="Capture is provenance, not Context",
            rationale="Prove that Capture cannot satisfy a Context input",
        ), correlation_id=uuid4(), idempotency_key=uuid4(),
    )
    assert capture.engineering_object_id == obj.id
    assert db_session.query(EngineeringContextPackageInputBinding).count() == 0
    assert db_session.query(EvidencePackageInputBinding).count() == 0

    service = PackageDeclarationBindingService(_factory(db_session), package_key="instrumentation")
    evaluation = service.evaluate_context(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        expected_configuration_revision=1, object_ids=(obj.id,), correlation_id=uuid4(),
    )
    assert evaluation.status == "FINDINGS"
    assert all(item.context_id is None for item in evaluation.context_results)

    _bind_context(service, engineer_user, project, workspace, context, subject,
                  "instrumentation.measurement_service.input")
    _bind_evidence(service, engineer_user, project, workspace, evidence,
                   "instrumentation.measurement_process_basis_evidence.input")
    context_binding = db_session.query(EngineeringContextPackageInputBinding).one()
    evidence_binding = db_session.query(EvidencePackageInputBinding).one()
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.execute(text(
                "UPDATE engineering_context_package_input_bindings SET input_declaration_id='instrumentation.loop_basis.input'"
            ))
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.delete(evidence_binding); db_session.flush()
    assert context_binding.input_declaration_id == "instrumentation.measurement_service.input"


def test_configuration_change_requires_an_explicit_new_binding_and_order_is_stable(
    db_session, engineer_user,
):
    project, workspace = _instrumentation_scope(db_session, engineer_user)
    obj = _object(db_session, engineer_user, project, workspace)
    context, subject = _context(db_session, engineer_user, project, workspace, obj)
    service = PackageDeclarationBindingService(_factory(db_session), package_key="instrumentation")
    _bind_context(service, engineer_user, project, workspace, context, subject,
                  "instrumentation.measurement_service.input")

    predecessor = db_session.get(ProjectPackageConfigurationRevision, (project.id, 1))
    predecessor_selection = db_session.get(
        ProjectPackageConfigurationSelection, (project.id, 1, "instrumentation"),
    )
    head = db_session.get(ProjectPackageConfigurationHead, project.id)
    db_session.add(ProjectPackageConfigurationRevision(
        project_id=project.id, configuration_revision=2, organization_id=ORG_ID,
        observed_registry_digest=predecessor.observed_registry_digest,
        profile_id=predecessor.profile_id, profile_digest=predecessor.profile_digest,
        rationale="Explicit retained configuration revision",
    ))
    db_session.flush()
    db_session.add(ProjectPackageConfigurationSelection(
        project_id=project.id, configuration_revision=2,
        package_key="instrumentation", package_version="1.0.0",
        descriptor_digest=predecessor_selection.descriptor_digest,
    ))
    db_session.flush()
    head.current_revision = 2
    head.configuration_version += 1
    workspace.bound_project_configuration_revision = 2
    workspace.version += 1
    db_session.commit()

    result = service.evaluate_context(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        expected_configuration_revision=2, object_ids=(obj.id,),
        correlation_id=uuid4(),
    )
    assert result.status == "FINDINGS"
    assert result.required_input_ids == (
        "instrumentation.measurement_service.input",
        "instrumentation.operating_range.input",
        "instrumentation.design_conditions.input",
        "instrumentation.signal_basis.input",
        "instrumentation.loop_basis.input",
    )
    assert all(item.status == "MISSING" for item in result.context_results)

    rebound = _bind_context(
        service, engineer_user, project, workspace, context, subject,
        "instrumentation.measurement_service.input",
        expected_configuration_revision=2,
    )
    assert rebound.project_configuration_revision == 2
    assert {row.project_configuration_revision for row in db_session.query(
        EngineeringContextPackageInputBinding
    )} == {1, 2}


def test_resource_bounds_and_binding_transaction_rollback(
    db_session, engineer_user, monkeypatch,
):
    project, workspace = _instrumentation_scope(db_session, engineer_user)
    obj = _object(db_session, engineer_user, project, workspace)
    context, subject = _context(db_session, engineer_user, project, workspace, obj)
    service = PackageDeclarationBindingService(_factory(db_session), package_key="instrumentation")
    with pytest.raises(PackageDeclarationMismatch):
        service.evaluate_context(
            actor_id=engineer_user.id, organization_id=ORG_ID,
            project_id=project.id, workspace_id=workspace.id,
            expected_configuration_revision=1,
            object_ids=tuple(uuid4() for _ in range(65)), correlation_id=uuid4(),
        )
    evidence = _evidence(db_session, engineer_user, project, workspace)
    _bind_evidence(
        service, engineer_user, project, workspace, evidence,
        "instrumentation.measurement_process_basis_evidence.input",
    )
    deliverable, revision = _deliverable(
        db_session, engineer_user, project, workspace,
    )
    empty_selection = service.readiness(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        deliverable_id=deliverable.id, revision_id=revision.id,
        expected_configuration_revision=1, object_ids=(),
        evidence_ids=(evidence.id,), correlation_id=uuid4(),
    )
    assert empty_selection.status == "FINDINGS"
    assert empty_selection.findings == ("required_binding_missing",)

    def fail_audit(*args, **kwargs):
        raise RuntimeError("forced atomic rollback")

    monkeypatch.setattr(service, "_audit", fail_audit)
    with pytest.raises(RuntimeError, match="forced atomic rollback"):
        _bind_context(service, engineer_user, project, workspace, context, subject,
                      "instrumentation.measurement_service.input")
    assert db_session.query(EngineeringContextPackageInputBinding).count() == 0
    assert db_session.query(AuditLog).filter_by(action="PackageContextInputBound").count() == 0
    assert db_session.query(EngineeringDeliverableIdempotency).filter_by(
        operation="instrumentation_ctx_binding",
    ).count() == 0


def test_exact_readiness_unrelated_evidence_and_positive_transition(
    db_session, engineer_user,
):
    project, workspace = _instrumentation_scope(db_session, engineer_user)
    obj = _object(db_session, engineer_user, project, workspace)
    service = PackageDeclarationBindingService(_factory(db_session), package_key="instrumentation")
    for name in ("measurement_service", "signal_basis", "loop_basis"):
        context, subject = _context(db_session, engineer_user, project, workspace, obj)
        _bind_context(service, engineer_user, project, workspace, context, subject,
                      f"instrumentation.{name}.input")
    evidence = _evidence(db_session, engineer_user, project, workspace)
    unrelated = _evidence(db_session, engineer_user, project, workspace)
    stale = _evidence(db_session, engineer_user, project, workspace)
    _bind_evidence(service, engineer_user, project, workspace, evidence,
                   "instrumentation.measurement_process_basis_evidence.input")
    _bind_evidence(service, engineer_user, project, workspace, stale,
                   "instrumentation.measurement_process_basis_evidence.input")
    stale.version = 3
    db_session.flush()
    deliverable, revision = _deliverable(db_session, engineer_user, project, workspace)

    missing = service.readiness(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        deliverable_id=deliverable.id, revision_id=revision.id,
        expected_configuration_revision=1, object_ids=(obj.id,),
        evidence_ids=(unrelated.id,), correlation_id=uuid4(),
    )
    assert missing.status == "FINDINGS" and not missing.transition_allowed
    assert {r.evidence_requirement_id for r in missing.evidence_results} == {
        "instrumentation.measurement_process_basis_evidence"
    }
    stale_result = service.readiness(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        deliverable_id=deliverable.id, revision_id=revision.id,
        expected_configuration_revision=1, object_ids=(obj.id,),
        evidence_ids=(stale.id,), correlation_id=uuid4(),
    )
    assert stale_result.evidence_results[0].status == "STALE"

    ready = service.readiness(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        deliverable_id=deliverable.id, revision_id=revision.id,
        expected_configuration_revision=1, object_ids=(obj.id,),
        evidence_ids=(evidence.id,), correlation_id=uuid4(),
    )
    assert ready.status == "PASS" and ready.transition_allowed
    transition_request = PackageTransitionRequest(
        target_standing="ready_for_review", expected_deliverable_version=1,
        expected_revision_version=1, expected_configuration_revision=1,
        object_ids=(obj.id,), evidence_ids=(evidence.id,),
        rationale="Exact package gate passed",
    )
    transition_key = uuid4()
    transitioned = service.transition(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        deliverable_id=deliverable.id, revision_id=revision.id,
        data=transition_request, correlation_id=uuid4(),
        idempotency_key=transition_key,
    )
    assert transitioned.status == "PASS"
    assert transitioned.deliverable_version == 2 and transitioned.revision_version == 2
    replay = service.transition(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        deliverable_id=deliverable.id, revision_id=revision.id,
        data=transition_request, correlation_id=uuid4(),
        idempotency_key=transition_key,
    )
    assert replay == transitioned
    assert db_session.scalar(select(EngineeringDeliverableOutbox).where(
        EngineeringDeliverableOutbox.deliverable_id == deliverable.id,
        EngineeringDeliverableOutbox.event_type == "PackageDeliverableRevisionTransitioned",
    )) is not None


def test_authorization_precedes_declaration_and_protected_source_is_hidden(
    db_session, engineer_user, admin_user,
):
    project, workspace = _instrumentation_scope(db_session, engineer_user)
    obj = _object(db_session, engineer_user, project, workspace)
    context, subject = _context(db_session, engineer_user, project, workspace, obj)
    db_session.add(EngineeringContextSourceReference(
        context_id=context.id, source_kind="engineer_input", source_key="protected",
        source_owner_id=admin_user.id, revision="1",
        confidentiality="restricted", applicability="Restricted fixture",
    ))
    db_session.flush()

    # The protected Context is rejected before the deliberately wrong input can
    # be resolved, so declaration existence is not disclosed.
    service = PackageDeclarationBindingService(_factory(db_session), package_key="instrumentation")
    with pytest.raises(PackageProtectedNotFound):
        service.bind_context(
            actor_id=engineer_user.id, organization_id=ORG_ID,
            project_id=project.id, workspace_id=workspace.id,
            data=PackageContextBindingRequest(
                input_declaration_id="electrical.protection_basis.input",
                context_id=context.id, context_subject_reference_id=subject.id,
                expected_context_version=1, expected_configuration_revision=1,
                rationale="Must remain protected",
            ), correlation_id=uuid4(), idempotency_key=uuid4(),
        )

    # A foreign tenant is likewise rejected before declaration resolution.
    with pytest.raises(PackageProtectedNotFound):
        service.bind_context(
            actor_id=engineer_user.id, organization_id=uuid4(),
            project_id=project.id, workspace_id=workspace.id,
            data=PackageContextBindingRequest(
                input_declaration_id="electrical.protection_basis.input",
                context_id=context.id, context_subject_reference_id=subject.id,
                expected_context_version=1, expected_configuration_revision=1,
                rationale="Must remain tenant protected",
            ), correlation_id=uuid4(), idempotency_key=uuid4(),
        )


def test_protected_bound_context_blocks_evaluation_without_package_disclosure(
    db_session, engineer_user, admin_user,
):
    project, workspace = _instrumentation_scope(db_session, engineer_user)
    obj = _object(db_session, engineer_user, project, workspace)
    context, subject = _context(db_session, engineer_user, project, workspace, obj)
    service = PackageDeclarationBindingService(
        _factory(db_session), package_key="instrumentation",
    )
    _bind_context(
        service, engineer_user, project, workspace, context, subject,
        "instrumentation.measurement_service.input",
    )
    db_session.add(EngineeringContextSourceReference(
        context_id=context.id, source_kind="engineer_input",
        source_key="became-protected", source_owner_id=admin_user.id,
        revision="1", confidentiality="restricted",
        applicability="Protected after binding",
    ))
    db_session.flush()
    with pytest.raises(PackageProtectedNotFound):
        service.evaluate_context(
            actor_id=engineer_user.id, organization_id=ORG_ID,
            project_id=project.id, workspace_id=workspace.id,
            expected_configuration_revision=1, object_ids=(obj.id,),
            correlation_id=uuid4(),
        )


def test_unrelated_object_context_does_not_satisfy_selected_object_readiness(
    db_session, engineer_user,
):
    project, workspace = _instrumentation_scope(db_session, engineer_user)
    selected = _object(db_session, engineer_user, project, workspace)
    unrelated = _object(db_session, engineer_user, project, workspace)
    service = PackageDeclarationBindingService(
        _factory(db_session), package_key="instrumentation",
    )
    for name in ("measurement_service", "signal_basis", "loop_basis"):
        context, subject = _context(
            db_session, engineer_user, project, workspace, unrelated,
        )
        _bind_context(
            service, engineer_user, project, workspace, context, subject,
            f"instrumentation.{name}.input",
        )
    evidence = _evidence(db_session, engineer_user, project, workspace)
    _bind_evidence(
        service, engineer_user, project, workspace, evidence,
        "instrumentation.measurement_process_basis_evidence.input",
    )
    deliverable, revision = _deliverable(
        db_session, engineer_user, project, workspace,
    )
    result = service.readiness(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        deliverable_id=deliverable.id, revision_id=revision.id,
        expected_configuration_revision=1, object_ids=(selected.id,),
        evidence_ids=(evidence.id,), correlation_id=uuid4(),
    )
    assert result.status == "FINDINGS"
    assert {row.subject_id for row in result.context_results} == {str(selected.id)}
    assert all(row.status == "MISSING" for row in result.context_results)


def test_post_preauthorization_revocation_is_rechecked_under_package_locks(
    db_session, engineer_user, monkeypatch,
):
    project, workspace = _instrumentation_scope(db_session, engineer_user)
    obj = _object(db_session, engineer_user, project, workspace)
    context, subject = _context(db_session, engineer_user, project, workspace, obj)
    service = PackageDeclarationBindingService(
        _factory(db_session), package_key="instrumentation",
    )
    original = service._preauthorize

    def authorize_then_revoke(**kwargs):
        original(**kwargs)
        db_session.execute(text(
            "UPDATE users SET is_active=false, auth_version=auth_version+1 "
            "WHERE id=:actor_id"
        ), {"actor_id": engineer_user.id})
        db_session.flush()

    monkeypatch.setattr(service, "_preauthorize", authorize_then_revoke)
    with pytest.raises(PackageProtectedNotFound):
        _bind_context(
            service, engineer_user, project, workspace, context, subject,
            "instrumentation.measurement_service.input",
        )
    assert db_session.query(EngineeringContextPackageInputBinding).count() == 0
    assert db_session.query(AuditLog).filter_by(
        action="PackageContextInputBound",
    ).count() == 0


def test_issue_requires_exact_human_review_evidence_for_reviewed_revision(
    db_session, engineer_user,
):
    project, workspace = _instrumentation_scope(db_session, engineer_user)
    deliverable, revision = _deliverable(
        db_session, engineer_user, project, workspace,
    )
    # Human review remains an owner transition; the package service does not
    # manufacture the reviewed state.
    revision.standing = "ready_for_review"
    revision.version = 2
    deliverable.standing = "ready_for_review"
    deliverable.version = 2
    db_session.flush()
    owner_service = EngineeringDeliverableService(
        uow_factory=lambda: SqlAlchemyEngineeringDeliverableUnitOfWork(db_session),
        authorization=SqlAlchemyDeliverableAuthorization(db_session),
    )
    reviewed = owner_service.transition_revision(
        project_id=project.id, deliverable_id=deliverable.id,
        revision_id=revision.id,
        data=TransitionRevisionRequest(
            expected_deliverable_version=2, expected_revision_version=2,
            target_standing="reviewed", rationale="Human review completed",
        ),
        actor=DeliverableActor(
            actor_id=engineer_user.id, organization_id=ORG_ID,
        ),
        idempotency_key=uuid4(),
    )
    assert isinstance(reviewed, DeliverableMutationSuccess)
    db_session.refresh(deliverable)
    db_session.refresh(revision)
    assert revision.standing == "reviewed"

    service = PackageDeclarationBindingService(
        _factory(db_session), package_key="instrumentation",
    )
    wrong = _evidence(
        db_session, engineer_user, project, workspace,
        source_kind="human_review", deliverable_id=deliverable.id,
        revision_id=uuid4(),
    )
    exact = _evidence(
        db_session, engineer_user, project, workspace,
        source_kind="human_review", deliverable_id=deliverable.id,
        revision_id=revision.id,
    )
    fourth_input = "instrumentation.deliverable_review_evidence.input"
    _bind_evidence(service, engineer_user, project, workspace, wrong, fourth_input)
    _bind_evidence(service, engineer_user, project, workspace, exact, fourth_input)

    mismatch = service.readiness(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        deliverable_id=deliverable.id, revision_id=revision.id,
        expected_configuration_revision=1, object_ids=(),
        evidence_ids=(wrong.id,), correlation_id=uuid4(),
    )
    assert mismatch.status == "FINDINGS"
    assert mismatch.findings == ("human_review_revision_mismatch",)

    exact_readiness = service.readiness(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        deliverable_id=deliverable.id, revision_id=revision.id,
        expected_configuration_revision=1, object_ids=(),
        evidence_ids=(exact.id,), correlation_id=uuid4(),
    )
    assert exact_readiness.status == "PASS"
    assert exact_readiness.required_input_ids == (fourth_input,)
    issued = service.transition(
        actor_id=engineer_user.id, organization_id=ORG_ID,
        project_id=project.id, workspace_id=workspace.id,
        deliverable_id=deliverable.id, revision_id=revision.id,
        data=PackageTransitionRequest(
            target_standing="issued",
            expected_deliverable_version=deliverable.version,
            expected_revision_version=revision.version,
            expected_configuration_revision=1, object_ids=(),
            evidence_ids=(exact.id,), rationale="Issue exact reviewed revision",
        ), correlation_id=uuid4(), idempotency_key=uuid4(),
    )
    assert issued.status == "PASS"
    db_session.refresh(revision)
    assert revision.standing == "issued"

def test_evidence_binding_is_exact_and_legacy_evidence_stays_unbound(
    db_session, engineer_user,
):
    project, workspace = _instrumentation_scope(db_session, engineer_user)
    legacy = _evidence(db_session, engineer_user, project, workspace)
    selected = _evidence(db_session, engineer_user, project, workspace)
    service = PackageDeclarationBindingService(
        _factory(db_session), package_key="instrumentation",
    )
    key = uuid4()
    result = _bind_evidence(
        service, engineer_user, project, workspace, selected,
        "instrumentation.measurement_process_basis_evidence.input",
        idempotency_key=key,
    )
    assert _bind_evidence(
        service, engineer_user, project, workspace, selected,
        "instrumentation.measurement_process_basis_evidence.input",
        idempotency_key=key,
    ) == result
    assert result.evidence_id == selected.id
    assert result.evidence_requirement_id == (
        "instrumentation.measurement_process_basis_evidence"
    )
    assert db_session.query(EvidencePackageInputBinding).filter_by(
        evidence_id=legacy.id,
    ).count() == 0
    with pytest.raises(PackageDeclarationMismatch):
        _bind_evidence(
            service, engineer_user, project, workspace, selected,
            "electrical.voltage_source_basis_evidence.input",
        )


def test_evidence_binding_cardinality_is_bounded_by_the_exact_input(
    db_session, engineer_user,
):
    project, workspace = _instrumentation_scope(db_session, engineer_user)
    service = PackageDeclarationBindingService(
        _factory(db_session), package_key="instrumentation",
    )
    input_id = "instrumentation.measurement_process_basis_evidence.input"
    for _ in range(8):
        evidence = _evidence(db_session, engineer_user, project, workspace)
        _bind_evidence(service, engineer_user, project, workspace, evidence, input_id)
    ninth = _evidence(db_session, engineer_user, project, workspace)
    with pytest.raises(PackageDeclarationMismatch):
        _bind_evidence(service, engineer_user, project, workspace, ninth, input_id)
    assert db_session.query(EvidencePackageInputBinding).filter_by(
        input_declaration_id=input_id,
    ).count() == 8


def test_m2_subject_kind_domain_closes_the_governance_blocker(db_session):
    definition = db_session.scalar(text(
        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
        "WHERE conname='ck_engineering_context_subject_refs_kind'"
    ))
    assert "engineering_object" in definition
    descriptor = PackageDeclarationBindingService(
        _factory(db_session), package_key="instrumentation",
    ).descriptor
    assert {
        declaration.allowed_subject_kind_ids
        for declaration in descriptor.contributions.context_contributions
    } == {("engineering_object",)}


def test_subject_kind_domain_preserves_existing_values_and_rejects_unknown(
    db_session, engineer_user,
):
    project, workspace = _instrumentation_scope(db_session, engineer_user)
    obj = _object(db_session, engineer_user, project, workspace)
    context, object_subject = _context(
        db_session, engineer_user, project, workspace, obj,
    )
    db_session.add_all((
        EngineeringContextSubjectReference(
            context_id=context.id, subject_kind="project",
            subject_project_id=project.id,
        ),
        EngineeringContextSubjectReference(
            context_id=context.id, subject_kind="workspace",
            subject_workspace_id=workspace.id,
        ),
        EngineeringContextSubjectReference(
            context_id=context.id, subject_kind="discipline",
            discipline="instrumentation",
        ),
    ))
    db_session.flush()
    assert object_subject.subject_kind == "engineering_object"
    assert {row.subject_kind for row in db_session.query(
        EngineeringContextSubjectReference
    ).filter_by(context_id=context.id)} == {
        "project", "workspace", "discipline", "engineering_object",
    }
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(EngineeringContextSubjectReference(
                context_id=context.id, subject_kind="future_subject_kind",
            ))
            db_session.flush()


def test_binding_and_context_evaluation_routes_use_the_authorized_workspace_package(
    client, db_session, engineer_user, engineer_headers, monkeypatch,
):
    from app.api.v1.routers import discipline_package_operations as routes

    project, workspace = _instrumentation_scope(db_session, engineer_user)
    obj = _object(db_session, engineer_user, project, workspace)
    context, subject = _context(db_session, engineer_user, project, workspace, obj)
    evidence = _evidence(db_session, engineer_user, project, workspace)
    monkeypatch.setattr(routes, "SessionLocal", _factory(db_session))
    base = (
        f"/projects/{project.id}/discipline-packages/"
        f"workspaces/{workspace.id}"
    )
    headers = {
        **engineer_headers,
        "X-Correlation-ID": str(uuid4()),
        "Idempotency-Key": str(uuid4()),
    }
    context_response = client.post(
        f"{base}/context-bindings", headers=headers, json={
            "input_declaration_id": "instrumentation.measurement_service.input",
            "context_id": context.id,
            "context_subject_reference_id": subject.id,
            "expected_context_version": 1,
            "expected_configuration_revision": 1,
            "rationale": "Bind through public package route",
        },
    )
    assert context_response.status_code == 201
    assert context_response.json()["context_declaration_id"] == (
        "instrumentation.measurement_service.context"
    )
    evidence_response = client.post(
        f"{base}/evidence-bindings",
        headers={**headers, "Idempotency-Key": str(uuid4())},
        json={
            "input_declaration_id": (
                "instrumentation.measurement_process_basis_evidence.input"
            ),
            "evidence_id": str(evidence.id),
            "expected_evidence_version": 2,
            "expected_configuration_revision": 1,
            "rationale": "Bind Evidence through public package route",
        },
    )
    assert evidence_response.status_code == 201
    evaluation = client.get(
        f"{base}/context-evaluation",
        headers={**engineer_headers, "X-Correlation-ID": str(uuid4())},
        params={
            "expected_configuration_revision": 1,
            "object_ids": str(obj.id),
        },
    )
    assert evaluation.status_code == 200
    assert evaluation.json()["status"] == "FINDINGS"
    assert any(
        row["status"] == "SATISFIED"
        and row["input_declaration_id"]
        == "instrumentation.measurement_service.input"
        for row in evaluation.json()["context_results"]
    )
