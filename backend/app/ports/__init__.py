"""Application-owned ports for infrastructure adapters."""

from app.ports.engineering_object import AuditRecorder
from app.ports.engineering_object import AuthorizationPolicy
from app.ports.engineering_object import Clock
from app.ports.engineering_object import DomainEventRecorder
from app.ports.engineering_object import EngineeringObjectRepository
from app.ports.engineering_object import IdempotencyStore
from app.ports.engineering_object import ReferenceValidator
from app.ports.engineering_object import UnitOfWork
from app.ports.technical_report import TechnicalReportAuthorizationPolicy
from app.ports.technical_report import TechnicalReportClock
from app.ports.technical_report import TechnicalReportDraftAssistant
from app.ports.technical_report import TechnicalReportHistoricalResolver
from app.ports.technical_report import TechnicalReportReferenceValidator
from app.ports.technical_report import TechnicalReportRepository
from app.ports.technical_report import TechnicalReportUnitOfWork

__all__ = [
    "AuditRecorder",
    "AuthorizationPolicy",
    "Clock",
    "DomainEventRecorder",
    "EngineeringObjectRepository",
    "IdempotencyStore",
    "ReferenceValidator",
    "UnitOfWork",
    "TechnicalReportAuthorizationPolicy",
    "TechnicalReportClock",
    "TechnicalReportDraftAssistant",
    "TechnicalReportHistoricalResolver",
    "TechnicalReportReferenceValidator",
    "TechnicalReportRepository",
    "TechnicalReportUnitOfWork",
]
