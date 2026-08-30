"""
Pydantic schemas (the API's request/response contracts).

Kept separate from the ORM models so the API shape can evolve
independently of the database schema.

ID fields are typed as `UUID` (not `str`) on *input* schemas so
FastAPI/Pydantic rejects malformed IDs with a clean 422 before they
ever reach the database. Without this, an invalid ID reaches Postgres
as a raw string and blows up as an unhandled 500 (DataError) instead
of a normal validation error.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models import RequirementStatus, EventType


# ---------- Project ----------

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str]
    created_at: datetime


# ---------- Requirement ----------

class RequirementCreate(BaseModel):
    project_id: UUID
    title: str
    description: str


class RequirementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[RequirementStatus] = None


class RequirementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    title: str
    description: str
    status: RequirementStatus
    created_at: datetime


# ---------- Event ----------

class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    requirement_id: Optional[str]
    event_type: EventType
    payload: Optional[str]
    created_at: datetime
