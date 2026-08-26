from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.routers.contacts import router as contact_router
from app.api.v1.routers.customers import router as customer_router
from app.api.v1.routers.projects import router as project_router
from app.api.v1.routers.search import router as search_router
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.audit_logs import router as audit_router
from app.api.v1.routers.engineering_workspaces import (
    router as engineering_workspace_router,
)
from app.api.v1.routers.engineering_objects import (
    router as engineering_object_router,
)
from app.api.v1.routers.evidence import router as evidence_router
from app.api.v1.routers.engineering_relationships import (
    router as engineering_relationship_router,
)
from app.api.v1.routers.engineering_experience_captures import (
    router as engineering_experience_capture_router,
)
from app.api.v1.routers.engineering_journal import (
    router as engineering_journal_router,
)
from app.api.v1.routers.technical_reports import router as technical_report_router
from app.api.v1.routers.engineering_knowledge_graph import (
    router as engineering_knowledge_graph_router,
)
from app.api.v1.routers.organizational_memory import (
    router as organizational_memory_router,
)
from app.api.v1.routers.ai_capture_assistant import router as ai_capture_assistant_router
from app.api.v1.routers.onboarding import router as onboarding_router
from app.api.v1.routers.operations import router as operations_router
from app.api.v1.routers.supporting_files import router as supporting_file_router
from app.api.v1.routers.project_foundation import router as project_foundation_router
from app.api.v1.routers.engineering_execution_plan import router as engineering_execution_plan_router
from app.api.v1.routers.engineering_deliverables import router as engineering_deliverable_router
from app.api.v1.routers.project_controls import router as project_control_router
from app.api.v1.routers.project_context import router as project_context_router
from app.api.v1.routers.project_completeness import router as project_completeness_router
from app.core.config import settings
from app.core.operations import (
    GovernedWriteBlocked,
    readiness_snapshot,
    operational_mode,
    validate_production_settings,
    ensure_governed_write_allowed,
)

from app.exceptions.handlers import register_exception_handlers


app = FastAPI(
    title="SATCO Platform API",
    version="0.1.0",
)

if settings.SATCO_ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            value.strip()
            for value in settings.SATCO_TRUSTED_HOSTS.split(",")
            if value.strip()
        ],
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            value.strip()
            for value in settings.SATCO_ALLOWED_ORIGINS.split(",")
            if value.strip()
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization", "Content-Type", "Idempotency-Key",
            "X-Correlation-ID",
        ],
    )


register_exception_handlers(app)


@app.on_event("startup")
def validate_production_startup() -> None:
    validate_production_settings(settings)
    operational_mode(settings)


@app.middleware("http")
async def governed_write_gate(request: Request, call_next):
    try:
        ensure_governed_write_allowed(settings, request.method)
    except GovernedWriteBlocked:
        return JSONResponse(status_code=503, content={"outcome": "unavailable"})
    return await call_next(request)


app.include_router(project_router)
app.include_router(contact_router)
app.include_router(customer_router)
app.include_router(search_router)
app.include_router(auth_router)
app.include_router(audit_router)
app.include_router(engineering_workspace_router)
app.include_router(engineering_object_router)
app.include_router(evidence_router)
app.include_router(engineering_relationship_router)
app.include_router(engineering_experience_capture_router)
app.include_router(engineering_journal_router)
app.include_router(technical_report_router)
app.include_router(engineering_knowledge_graph_router)
app.include_router(organizational_memory_router)
app.include_router(ai_capture_assistant_router)
app.include_router(onboarding_router)
app.include_router(operations_router)
app.include_router(supporting_file_router)
app.include_router(project_foundation_router)
app.include_router(engineering_execution_plan_router)
app.include_router(engineering_deliverable_router)
app.include_router(project_control_router)
app.include_router(project_context_router)
app.include_router(project_completeness_router)


@app.get("/health/live")
def health_live():
    return {"status": "alive"}


@app.get("/health/ready")
def health_ready():
    snapshot = readiness_snapshot(settings)
    if snapshot.ready:
        return {"status": "ready"}
    return JSONResponse(status_code=503, content={"status": "not_ready"})


@app.get("/")
def root():
    return {
        "message": "SATCO Platform API is running",
        "status": "ok",
    }
