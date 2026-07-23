from fastapi import FastAPI

from .database import engine, Base
from . import models


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="SATCO Platform API",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "SATCO Platform API is running",
        "status": "ok"
    }


@app.get("/projects")
def get_projects():
    return {
        "message": "Projects API is ready"
    }