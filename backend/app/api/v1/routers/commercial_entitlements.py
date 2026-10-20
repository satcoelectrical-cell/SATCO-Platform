"""PATCH-059 commercial entitlement and seat administration surface."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from sqlalchemy.orm import Session

from app.repositories.commercial_entitlement_unit_of_work import (
    CommercialEntitlementUnitOfWork,
    require_repository,
)
from app.core.database import SessionLocal
from app.core.operations import ProductionConfigurationError
from app.commercial_entitlements.state import (
    CommercialEntitlementState as EffectiveEntitlementState,
    effective_entitlement_state,
)
from app.commercial_entitlements.canonical import (
    canonical_payload_digest,
    parse_envelope,
)
from app.commercial_entitlements.runtime import runtime_trust_store
from app.core.config import settings
from app.core.database import get_db
from app.repositories.commercial_entitlement_repository import (
    CommercialEntitlementRepository,
)
from app.services.commercial_entitlement_service import (
    CommercialEntitlementActivationError,
    activate_entitlement,
    preview_entitlement,
)
from app.services.commercial_seat_service import (
    CommercialSeatError,
    CommercialSeatReason,
    assign_seat,
    list_seat_evaluations,
    release_seat,
    retain_seats,
)
from app.services.audit_service import stage_audit_log
from app.schemas.commercial_entitlement import (
    CommercialEntitlementValidationResponse,
    CommercialEntitlementStatusResponse,
    CommercialSeatListResponse,
    CommercialSeatMutationResponse,
    CommercialSeatResponse,
    CommercialSeatRetainedRequest,
    CommercialSeatRetentionResponse,
)
from app.dependencies.auth import (
    AuthenticatedOrganizationContext,
    AuthenticatedSessionContext,
    get_current_session_context,
    get_current_user_organization_context,
)
from app.permissions.roles import Role
from app.services.browser_auth_security_service import BrowserAuthSecurityService
from app.services.refresh_session_service import RefreshSessionService


router = APIRouter(tags=["Commercial Entitlements"])


@dataclass(frozen=True, slots=True)
class CommercialAdminContext:
    organization: AuthenticatedOrganizationContext
    auth: AuthenticatedSessionContext


def require_commercial_admin(
    context: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
    auth: AuthenticatedSessionContext = Depends(get_current_session_context),
) -> CommercialAdminContext:
    """Resolve the canonical current-Organization commercial administrator.

    Protected-not-found semantics are preserved for role/scope mismatches.
    """

    if context.user.role != Role.ADMIN.value:
        raise HTTPException(
            status_code=404,
            detail="Protected resource not found",
        )

    if auth.user.id != context.user.id:
        raise HTTPException(
            status_code=404,
            detail="Protected resource not found",
        )

    return CommercialAdminContext(
        organization=context,
        auth=auth,
    )


def require_sensitive_commercial_mutation(
    request: Request,
    admin: CommercialAdminContext = Depends(require_commercial_admin),
    db: Session = Depends(get_db),
) -> CommercialAdminContext:
    """Require PATCH-058 browser protections and explicit recent step-up."""

    BrowserAuthSecurityService.require_csrf(request)

    if not RefreshSessionService(db).has_recent_step_up(
        admin.auth.session,
        minutes=10,
    ):
        raise HTTPException(
            status_code=403,
            detail="Recent authentication required",
        )

    return admin



@router.get(
    "/organizations/current/commercial-entitlement",
    response_model=CommercialEntitlementStatusResponse,
    operation_id="get_current_commercial_entitlement",
)
def get_current_commercial_entitlement(
    context: AuthenticatedOrganizationContext = Depends(
        get_current_user_organization_context
    ),
    db: Session = Depends(get_db),
) -> CommercialEntitlementStatusResponse:
    deployment_id = settings.SATCO_DEPLOYMENT_ID.strip()

    if not deployment_id:
        return CommercialEntitlementStatusResponse(
            available=False,
            effective_state=EffectiveEntitlementState.INVALID_OR_UNAVAILABLE.value,
            reason_code="entitlement_missing",
        )

    state = CommercialEntitlementRepository(db).get_state(
        organization_id=context.organization_id,
        deployment_id=deployment_id,
        lock=False,
    )

    if state is None:
        return CommercialEntitlementStatusResponse(
            available=False,
            effective_state=EffectiveEntitlementState.INVALID_OR_UNAVAILABLE.value,
            reason_code="entitlement_missing",
        )

    effective_state = effective_entitlement_state(
        state,
        datetime.now(timezone.utc),
    )

    reason_code = None
    if effective_state is EffectiveEntitlementState.TIME_UNTRUSTED:
        reason_code = "time_untrusted"
    elif effective_state is EffectiveEntitlementState.INVALID_OR_UNAVAILABLE:
        reason_code = "not_yet_valid"
    elif effective_state is EffectiveEntitlementState.GRACE:
        reason_code = "grace"
    elif effective_state is EffectiveEntitlementState.EXPIRED:
        reason_code = "expired"

    return CommercialEntitlementStatusResponse(
        available=effective_state
        not in {
            EffectiveEntitlementState.INVALID_OR_UNAVAILABLE,
            EffectiveEntitlementState.TIME_UNTRUSTED,
        },
        effective_state=effective_state.value,
        entitlement_id=state.entitlement_id,
        revision=state.accepted_revision,
        digest_prefix=state.canonical_payload_digest[:12],
        package_keys=list(state.package_keys),
        seat_capacity=state.seat_capacity,
        valid_until=state.valid_until,
        grace_until=state.grace_until,
        support_until=state.support_until,
        baseline_release_sequence=state.baseline_release_sequence,
        max_release_sequence=state.max_release_sequence,
        reason_code=reason_code,
    )

@router.post(
    "/organizations/current/commercial-entitlement/validate",
    response_model=CommercialEntitlementValidationResponse,
    operation_id="validate_current_commercial_entitlement",
)
async def validate_current_commercial_entitlement(
    request: Request,
    admin: CommercialAdminContext = Depends(
        require_sensitive_commercial_mutation
    ),
    db: Session = Depends(get_db),
) -> CommercialEntitlementValidationResponse:
    """Validate and preview a signed entitlement without activating it."""

    try:
        raw = await request.body()
        envelope = parse_envelope(raw)
    except (UnicodeError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail="Invalid commercial entitlement envelope",
        ) from exc

    try:
        trust_store = runtime_trust_store()
    except ProductionConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail="Commercial entitlement verification unavailable",
        ) from exc

    deployment_id = settings.SATCO_DEPLOYMENT_ID.strip()
    if not deployment_id:
        raise HTTPException(
            status_code=503,
            detail="Commercial entitlement verification unavailable",
        )

    repository = CommercialEntitlementRepository(db)
    current = repository.get_state(
        organization_id=admin.organization.organization_id,
        deployment_id=deployment_id,
        lock=False,
    )

    result = preview_entitlement(
        envelope=envelope,
        trust_store=trust_store,
        current_state=current,
        expected_organization_id=admin.organization.organization_id,
        expected_deployment_id=deployment_id,
        observed_now=datetime.now(timezone.utc),
    )

    return CommercialEntitlementValidationResponse(
        valid=result.valid,
        effect=result.effect,
        entitlement_id=result.entitlement_id,
        revision=result.revision,
        digest_prefix=(
            None
            if result.canonical_payload_digest is None
            else result.canonical_payload_digest[:12]
        ),
        reason_code=result.reason_code,
    )


def _commercial_deployment_id() -> str:
    deployment_id = settings.SATCO_DEPLOYMENT_ID.strip()
    if not deployment_id:
        raise HTTPException(
            status_code=503,
            detail="Commercial entitlement service unavailable",
        )
    return deployment_id


def _raise_seat_error(exc: CommercialSeatError) -> None:
    if exc.reason_code in {
        CommercialSeatReason.MEMBERSHIP_REQUIRED.value,
        CommercialSeatReason.SEAT_REQUIRED.value,
    }:
        raise HTTPException(
            status_code=404,
            detail="Protected resource not found",
        ) from exc

    raise HTTPException(status_code=409, detail=exc.reason_code) from exc


def _seat_audit_details(
    *,
    organization_id,
    deployment_id: str,
    outcome: str,
    consuming_count: int,
    capacity: int,
) -> dict[str, object]:
    return {
        "organization_id": str(organization_id),
        "deployment_id": deployment_id,
        "outcome": outcome,
        "consuming_count": consuming_count,
        "capacity": capacity,
    }


def _activation_audit_action(*, accepted: bool, reason_code: str | None) -> str:
    if accepted:
        return "entitlement_activated"
    if reason_code == "rollback_detected":
        return "rollback_detected"
    if reason_code == "time_untrusted":
        return "time_untrusted"
    if reason_code in {"invalid_signature", "untrusted_key", "revoked_key"}:
        return "entitlement_validation_failed"
    return "entitlement_rejected"


def _stage_activation_audit(
    session,
    *,
    actor_user_id: int,
    organization_id,
    deployment_id: str,
    entitlement_id,
    revision: int,
    digest_prefix: str,
    accepted: bool,
    outcome: str,
    reason_code: str | None,
) -> None:
    stage_audit_log(
        session,
        actor_user_id,
        _activation_audit_action(
            accepted=accepted,
            reason_code=reason_code,
        ),
        "COMMERCIAL_ENTITLEMENT",
        details={
            "organization_id": str(organization_id),
            "deployment_id": deployment_id,
            "entitlement_id": str(entitlement_id),
            "revision": revision,
            "digest_prefix": digest_prefix,
            "outcome": outcome,
            "reason_code": reason_code,
        },
    )


def _record_activation_rejection_audit(
    *,
    admin: CommercialAdminContext,
    deployment_id: str,
    envelope,
    reason_code: str,
) -> None:
    """Persist a bounded rejection after the mutation UoW has rolled back."""

    digest_prefix = canonical_payload_digest(envelope.payload)[:12]
    with SessionLocal() as session:
        _stage_activation_audit(
            session,
            actor_user_id=admin.organization.user.id,
            organization_id=admin.organization.organization_id,
            deployment_id=deployment_id,
            entitlement_id=envelope.payload.entitlement_id,
            revision=envelope.payload.revision,
            digest_prefix=digest_prefix,
            accepted=False,
            outcome="rejected",
            reason_code=reason_code,
        )
        session.commit()


@router.get(
    "/organizations/current/commercial-seats",
    response_model=CommercialSeatListResponse,
    operation_id="list_current_commercial_seats",
)
def list_current_commercial_seats(
    admin: CommercialAdminContext = Depends(require_commercial_admin),
) -> CommercialSeatListResponse:
    deployment_id = _commercial_deployment_id()
    organization_id = admin.organization.organization_id

    try:
        with CommercialEntitlementUnitOfWork(SessionLocal) as uow:
            result = list_seat_evaluations(
                uow,
                organization_id=organization_id,
                deployment_id=deployment_id,
            )
            repository = require_repository(uow)
            users = repository.list_membership_users(
                organization_id=organization_id,
                user_ids=tuple(seat.user_id for seat in result.seats),
            )
            display_names = {user.id: user.full_name for user in users}
    except CommercialSeatError as exc:
        _raise_seat_error(exc)

    return CommercialSeatListResponse(
        capacity=result.capacity,
        consuming_count=result.consuming_count,
        over_capacity=result.over_capacity,
        seats=[
            CommercialSeatResponse(
                user_id=seat.user_id,
                state=seat.effective_state,
                executable=seat.executable,
                display_name=display_names.get(seat.user_id),
            )
            for seat in result.seats
            if seat.effective_state is not None
        ],
    )


@router.post(
    "/organizations/current/commercial-seats/{user_id}",
    response_model=CommercialSeatMutationResponse,
    operation_id="assign_current_commercial_seat",
)
def assign_current_commercial_seat(
    user_id: int = Path(gt=0),
    admin: CommercialAdminContext = Depends(
        require_sensitive_commercial_mutation
    ),
) -> CommercialSeatMutationResponse:
    deployment_id = _commercial_deployment_id()
    organization_id = admin.organization.organization_id

    try:
        with CommercialEntitlementUnitOfWork(SessionLocal) as uow:
            result = assign_seat(
                uow,
                organization_id=organization_id,
                deployment_id=deployment_id,
                user_id=user_id,
                actor_user_id=admin.organization.user.id,
                observed_now=datetime.now(timezone.utc),
            )
            stage_audit_log(
                uow.session,
                admin.organization.user.id,
                "seat_assigned",
                "COMMERCIAL_SEAT",
                user_id,
                _seat_audit_details(
                    organization_id=organization_id,
                    deployment_id=deployment_id,
                    outcome=result.state.value,
                    consuming_count=result.consuming_count,
                    capacity=result.capacity,
                ),
            )
            uow.commit()
    except CommercialSeatError as exc:
        _raise_seat_error(exc)

    return CommercialSeatMutationResponse(
        user_id=result.user_id,
        state=result.state,
        consuming_count=result.consuming_count,
        capacity=result.capacity,
    )


@router.delete(
    "/organizations/current/commercial-seats/{user_id}",
    response_model=CommercialSeatMutationResponse,
    operation_id="release_current_commercial_seat",
)
def release_current_commercial_seat(
    user_id: int = Path(gt=0),
    admin: CommercialAdminContext = Depends(
        require_sensitive_commercial_mutation
    ),
) -> CommercialSeatMutationResponse:
    deployment_id = _commercial_deployment_id()
    organization_id = admin.organization.organization_id

    try:
        with CommercialEntitlementUnitOfWork(SessionLocal) as uow:
            result = release_seat(
                uow,
                organization_id=organization_id,
                deployment_id=deployment_id,
                user_id=user_id,
            )
            stage_audit_log(
                uow.session,
                admin.organization.user.id,
                "seat_released",
                "COMMERCIAL_SEAT",
                user_id,
                _seat_audit_details(
                    organization_id=organization_id,
                    deployment_id=deployment_id,
                    outcome="released",
                    consuming_count=result.consuming_count,
                    capacity=result.capacity,
                ),
            )
            uow.commit()
    except CommercialSeatError as exc:
        _raise_seat_error(exc)

    return CommercialSeatMutationResponse(
        user_id=result.user_id,
        state=None,
        consuming_count=result.consuming_count,
        capacity=result.capacity,
    )


@router.put(
    "/organizations/current/commercial-seats/retained",
    response_model=CommercialSeatRetentionResponse,
    operation_id="retain_current_commercial_seats",
)
def retain_current_commercial_seats(
    request: CommercialSeatRetainedRequest,
    admin: CommercialAdminContext = Depends(
        require_sensitive_commercial_mutation
    ),
) -> CommercialSeatRetentionResponse:
    deployment_id = _commercial_deployment_id()
    organization_id = admin.organization.organization_id

    try:
        with CommercialEntitlementUnitOfWork(SessionLocal) as uow:
            result = retain_seats(
                uow,
                organization_id=organization_id,
                deployment_id=deployment_id,
                retained_user_ids=request.user_ids,
                actor_user_id=admin.organization.user.id,
                observed_now=datetime.now(timezone.utc),
            )
            details = _seat_audit_details(
                organization_id=organization_id,
                deployment_id=deployment_id,
                outcome="resolved" if not result.unresolved else "unresolved",
                consuming_count=result.consuming_count,
                capacity=result.capacity,
            )
            details["retained_count"] = len(request.user_ids)
            stage_audit_log(
                uow.session,
                admin.organization.user.id,
                "seat_retained",
                "COMMERCIAL_SEAT",
                details=details,
            )
            if not result.unresolved:
                stage_audit_log(
                    uow.session,
                    admin.organization.user.id,
                    "over_capacity_resolved",
                    "COMMERCIAL_SEAT",
                    details=details,
                )
            uow.commit()
    except CommercialSeatError as exc:
        _raise_seat_error(exc)

    return CommercialSeatRetentionResponse(
        capacity=result.capacity,
        consuming_count=result.consuming_count,
        over_capacity=result.over_capacity,
        unresolved=result.unresolved,
    )

@router.post(
    "/organizations/current/commercial-entitlement/activate",
    response_model=CommercialEntitlementValidationResponse,
    operation_id="activate_current_commercial_entitlement",
)
async def activate_current_commercial_entitlement(
    request: Request,
    admin: CommercialAdminContext = Depends(
        require_sensitive_commercial_mutation
    ),
) -> CommercialEntitlementValidationResponse:
    """Verify and atomically activate a signed commercial entitlement."""

    try:
        raw = await request.body()
        envelope = parse_envelope(raw)
    except (UnicodeError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail="Invalid commercial entitlement envelope",
        ) from exc

    try:
        trust_store = runtime_trust_store()
    except ProductionConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail="Commercial entitlement verification unavailable",
        ) from exc

    deployment_id = settings.SATCO_DEPLOYMENT_ID.strip()
    if not deployment_id:
        raise HTTPException(
            status_code=503,
            detail="Commercial entitlement verification unavailable",
        )

    activation_error = None
    with CommercialEntitlementUnitOfWork(SessionLocal) as uow:
        try:
            result = activate_entitlement(
                uow=uow,
                envelope=envelope,
                trust_store=trust_store,
                expected_organization_id=admin.organization.organization_id,
                expected_deployment_id=deployment_id,
                actor_user_id=admin.organization.user.id,
                correlation_id=None,
                observed_now=datetime.now(timezone.utc),
            )
        except CommercialEntitlementActivationError as exc:
            activation_error = exc
        else:
            _stage_activation_audit(
                uow.session,
                actor_user_id=admin.organization.user.id,
                organization_id=admin.organization.organization_id,
                deployment_id=deployment_id,
                entitlement_id=result.entitlement_id,
                revision=result.revision,
                digest_prefix=result.canonical_payload_digest[:12],
                accepted=result.accepted,
                outcome=(
                    result.decision.value
                    if result.accepted
                    else "rejected"
                ),
                reason_code=result.reason_code,
            )

            if result.accepted and result.state_advanced:
                repository = require_repository(uow)
                consuming_count = repository.consuming_seats(
                    organization_id=admin.organization.organization_id,
                    deployment_id=deployment_id,
                )
                if consuming_count > envelope.payload.seat_capacity:
                    stage_audit_log(
                        uow.session,
                        admin.organization.user.id,
                        "over_capacity_entered",
                        "COMMERCIAL_SEAT",
                        details=_seat_audit_details(
                            organization_id=(
                                admin.organization.organization_id
                            ),
                            deployment_id=deployment_id,
                            outcome="entered",
                            consuming_count=consuming_count,
                            capacity=envelope.payload.seat_capacity,
                        ),
                    )

            # Rejections such as rollback/conflict/TIME_UNTRUSTED carry
            # durable history and audit evidence in the same transaction.
            uow.commit()

    if activation_error is not None:
        _record_activation_rejection_audit(
            admin=admin,
            deployment_id=deployment_id,
            envelope=envelope,
            reason_code=activation_error.reason_code,
        )
        return CommercialEntitlementValidationResponse(
            valid=False,
            effect="rejected",
            entitlement_id=envelope.payload.entitlement_id,
            revision=envelope.payload.revision,
            digest_prefix=None,
            reason_code=activation_error.reason_code,
        )

    return CommercialEntitlementValidationResponse(
        valid=result.accepted,
        effect=result.decision.value if result.accepted else "rejected",
        entitlement_id=result.entitlement_id,
        revision=result.revision,
        digest_prefix=result.canonical_payload_digest[:12],
        reason_code=result.reason_code,
    )
