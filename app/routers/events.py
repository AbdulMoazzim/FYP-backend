"""
Event retrieval API.

Events are created internally (e.g. by crud.create_requirement) —
there is deliberately no POST endpoint here. This router is read-only
so that agents/UI can query "what happened" without being able to
forge history.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import get_db

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=list[schemas.EventOut])
def list_events(
    project_id: Optional[UUID] = None,
    requirement_id: Optional[UUID] = None,
    event_type: Optional[models.EventType] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return crud.list_events(
        db,
        project_id=str(project_id) if project_id else None,
        requirement_id=str(requirement_id) if requirement_id else None,
        event_type=event_type,
        skip=skip,
        limit=limit,
    )


@router.get("/{event_id}", response_model=schemas.EventOut)
def get_event(event_id: UUID, db: Session = Depends(get_db)):
    db_event = crud.get_event(db, str(event_id))
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    return db_event
