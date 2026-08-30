"""
Minimal Project endpoints.

A Requirement always belongs to a Project, so this router exists
mainly to let you create a project to attach requirements to. Full
project management (members, sprints, dashboard) is out of scope
for this milestone.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=schemas.ProjectOut, status_code=201)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    return crud.create_project(db, project)


@router.get("", response_model=list[schemas.ProjectOut])
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.list_projects(db, skip=skip, limit=limit)


@router.get("/{project_id}", response_model=schemas.ProjectOut)
def get_project(project_id: UUID, db: Session = Depends(get_db)):
    db_project = crud.get_project(db, str(project_id))
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project
