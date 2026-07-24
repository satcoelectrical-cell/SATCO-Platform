from fastapi import FastAPI

from app.core.database import Base
from app.core.database import engine

# Register models
from app.models import contact
from app.models import customer
from app.models import project

from app.api.v1.routers.contacts import router as contact_router
from app.api.v1.routers.customers import router as customer_router
from app.api.v1.routers.projects import router as project_router

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


@app.get("/")
def root():
    return {
        "message": "SATCO Platform API is running",
        "status": "ok",
    }
