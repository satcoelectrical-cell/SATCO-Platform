from fastapi import FastAPI

from app.core.database import Base
from app.core.database import engine

from app.models import contact
from app.models import customer
from app.models import project
from app.models import user

from app.api.v1.routers.contacts import router as contact_router
from app.api.v1.routers.customers import router as customer_router
from app.api.v1.routers.projects import router as project_router
from app.api.v1.routers.search import router as search_router
from app.api.v1.routers.auth import router as auth_router

from app.exceptions.handlers import register_exception_handlers


Base.metadata.create_all(bind=engine)


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


@app.get("/")
def root():
    return {
        "message": "SATCO Platform API is running",
        "status": "ok",
    }
