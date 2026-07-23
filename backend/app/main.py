from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from .database import engine, Base, SessionLocal
from . import models, schemas


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="SATCO Platform API",
    version="0.1.0"
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "message": "SATCO Platform API is running",
        "status": "ok"
    }


@app.post("/projects", response_model=schemas.ProjectResponse)
def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db)
):

    new_project = models.Project(
        name=project.name,
        customer=project.customer
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project


@app.get("/projects", response_model=list[schemas.ProjectResponse])
def get_projects(
    db: Session = Depends(get_db)
):

    projects = db.query(models.Project).all()

    return projects