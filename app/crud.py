"""
Database access functions.

The key piece of business logic for this milestone lives here:
`create_requirement` writes the Requirement row AND emits a matching
Event row in the same DB transaction, so a requirement can never
exist without a corresponding "requirement_created" event (and vice
versa on update/delete). This mirrors the FYP's event-driven design,
where the Agent Orchestrator reacts to rows in the events table.
"""
import json
from typing import Optional

from sqlalchemy.orm import Session

from app import models, schemas


# ---------- Project ----------

def create_project(db: Session, project: schemas.ProjectCreate) -> models.Project:
    db_project = models.Project(name=project.name, description=project.description)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_project(db: Session, project_id: str) -> Optional[models.Project]:
    return db.query(models.Project).filter(models.Project.id == project_id).first()


def list_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Project).offset(skip).limit(limit).all()


# ---------- Requirement ----------

def create_requirement(
    db: Session, requirement: schemas.RequirementCreate
) -> models.Requirement:
    db_requirement = models.Requirement(
        project_id=str(requirement.project_id),
        title=requirement.title,
        description=requirement.description,
    )
    db.add(db_requirement)
    db.flush()  # assigns db_requirement.id without committing yet

    db_event = models.Event(
        project_id=db_requirement.project_id,
        requirement_id=db_requirement.id,
        event_type=models.EventType.requirement_created,
        payload=json.dumps(
            {
                "title": db_requirement.title,
                "description": db_requirement.description,
                "status": db_requirement.status.value,
            }
        ),
    )
    db.add(db_event)

    db.commit()
    db.refresh(db_requirement)
    return db_requirement


def get_requirement(db: Session, requirement_id: str) -> Optional[models.Requirement]:
    return (
        db.query(models.Requirement)
        .filter(models.Requirement.id == requirement_id)
        .first()
    )


def list_requirements(
    db: Session, project_id: Optional[str] = None, skip: int = 0, limit: int = 100
):
    query = db.query(models.Requirement)
    if project_id:
        query = query.filter(models.Requirement.project_id == project_id)
    return query.offset(skip).limit(limit).all()


def update_requirement(
    db: Session, requirement_id: str, updates: schemas.RequirementUpdate
) -> Optional[models.Requirement]:
    db_requirement = get_requirement(db, requirement_id)
    if not db_requirement:
        return None

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_requirement, field, value)

    db.flush()

    db_event = models.Event(
        project_id=db_requirement.project_id,
        requirement_id=db_requirement.id,
        event_type=models.EventType.requirement_updated,
        payload=json.dumps(update_data, default=str),
    )
    db.add(db_event)

    db.commit()
    db.refresh(db_requirement)
    return db_requirement


def delete_requirement(db: Session, requirement_id: str) -> bool:
    db_requirement = get_requirement(db, requirement_id)
    if not db_requirement:
        return False

    db_event = models.Event(
        project_id=db_requirement.project_id,
        requirement_id=None,  # requirement is about to be removed
        event_type=models.EventType.requirement_deleted,
        payload=json.dumps({"deleted_requirement_id": requirement_id}),
    )
    db.add(db_event)
    db.delete(db_requirement)
    db.commit()
    return True


# ---------- Event ----------

def get_event(db: Session, event_id: str) -> Optional[models.Event]:
    return db.query(models.Event).filter(models.Event.id == event_id).first()


def list_events(
    db: Session,
    project_id: Optional[str] = None,
    requirement_id: Optional[str] = None,
    event_type: Optional[models.EventType] = None,
    skip: int = 0,
    limit: int = 100,
):
    query = db.query(models.Event)
    if project_id:
        query = query.filter(models.Event.project_id == project_id)
    if requirement_id:
        query = query.filter(models.Event.requirement_id == requirement_id)
    if event_type:
        query = query.filter(models.Event.event_type == event_type)
    return query.order_by(models.Event.created_at.desc()).offset(skip).limit(limit).all()
