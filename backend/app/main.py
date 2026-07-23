from fastapi import FastAPI

from .core.database import engine, Base
from . import models

from .api.v1.routers.projects import router as project_router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="SATCO Platform API",
    version="0.1.0"
)


app.include_router(project_router)


@app.get("/")
def root():
    return {
        "message": "SATCO Platform API is running",
        "status": "ok"
    }