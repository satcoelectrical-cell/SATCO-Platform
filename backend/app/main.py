from fastapi import FastAPI

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

from app.exceptions.handlers import register_exception_handlers


app = FastAPI(
    title="SATCO Platform API",
    version="0.1.0",
)


register_exception_handlers(app)


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


@app.get("/")
def root():
    return {
        "message": "SATCO Platform API is running",
        "status": "ok",
    }
