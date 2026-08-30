"""
Requirement API.

POST /requirements is the important one: every successful call here
also writes a `requirement_created` Event row (see app/crud.py), which
is the signal the future Agent Orchestrator will react to.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/requirements", tags=["Requirements"])


@router.post("", response_model=schemas.RequirementOut, status_code=201)
def create_requirement(
    requirement: schemas.RequirementCreate, db: Session = Depends(get_db)
):
    project = crud.get_project(db, str(requirement.project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud.create_requirement(db, requirement)


@router.get("", response_model=list[schemas.RequirementOut])
def list_requirements(
    project_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    pid = str(project_id) if project_id else None
    return crud.list_requirements(db, project_id=pid, skip=skip, limit=limit)


@router.get("/{requirement_id}", response_model=schemas.RequirementOut)
def get_requirement(requirement_id: UUID, db: Session = Depends(get_db)):
    db_requirement = crud.get_requirement(db, str(requirement_id))
    if not db_requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return db_requirement


@router.patch("/{requirement_id}", response_model=schemas.RequirementOut)
def update_requirement(
    requirement_id: UUID,
    updates: schemas.RequirementUpdate,
    db: Session = Depends(get_db),
):
    db_requirement = crud.update_requirement(db, str(requirement_id), updates)
    if not db_requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return db_requirement


@router.delete("/{requirement_id}", status_code=204)
def delete_requirement(requirement_id: UUID, db: Session = Depends(get_db)):
    deleted = crud.delete_requirement(db, str(requirement_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Requirement not found")
