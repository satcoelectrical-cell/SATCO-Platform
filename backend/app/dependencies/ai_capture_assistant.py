"""Request-scoped composition root for PATCH-035."""

from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Depends
from sqlalchemy.orm import Session

from app.adapters.ai_capture_assistant import CanonicalCaptureAdviceSource
from app.adapters.ai_capture_audit import SharedAICaptureAuditRecorder
from app.ai.capture_assistant import ProviderNeutralCaptureAssistant
from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.dependencies.auth import AuthenticatedOrganizationContext, get_current_user_organization_context
from app.models.engineering_experience_capture_command import EngineeringExperienceCaptureActor
from app.ports.ai_capture_assistant import CopilotActor
from app.repositories.engineering_experience_capture_unit_of_work import SqlAlchemyEngineeringExperienceCaptureUnitOfWork
from app.services.ai_capture_assistant_service import AICaptureAssistantService
from app.services.engineering_experience_capture_service import EngineeringExperienceCaptureService


class _UtcClock:
    def now(self):
        return datetime.now(timezone.utc)


class _UnavailableProvider:
    def propose(self, _request):
        from app.exceptions.ai_capture_assistant import AICaptureProviderUnavailable
        raise AICaptureProviderUnavailable()


@dataclass(frozen=True, slots=True)
class AICaptureAssistantApplication:
    service: AICaptureAssistantService
    actor: CopilotActor


def get_ai_capture_assistant_service(db: Session = Depends(get_db)):
    captures = EngineeringExperienceCaptureService(
        uow_factory=lambda: SqlAlchemyEngineeringExperienceCaptureUnitOfWork(SessionLocal)
    )
    provider = _UnavailableProvider()
    if settings.COPILOT_ENABLED and settings.COPILOT_PROVIDER_ENDPOINT and settings.COPILOT_PROVIDER_API_KEY:
        provider = ProviderNeutralCaptureAssistant(
            endpoint=settings.COPILOT_PROVIDER_ENDPOINT,
            api_key=settings.COPILOT_PROVIDER_API_KEY,
            timeout_seconds=settings.COPILOT_PROVIDER_TIMEOUT_SECONDS,
        )
    return AICaptureAssistantService(
        source=CanonicalCaptureAdviceSource(captures), provider=provider,
        audit=SharedAICaptureAuditRecorder(db), clock=_UtcClock(),
        enabled=settings.COPILOT_ENABLED,
    )


def get_ai_capture_assistant_application(
    context: AuthenticatedOrganizationContext = Depends(get_current_user_organization_context),
    service: AICaptureAssistantService = Depends(get_ai_capture_assistant_service),
):
    return AICaptureAssistantApplication(
        service, CopilotActor(context.user.id, context.organization_id)
    )
