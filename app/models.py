"""
ORM models for the three entities this milestone covers:

Project      - a Scrum project that requirements belong to.
Requirement  - a piece of functionality requested for a project.
Event        - an immutable log entry emitted whenever something
               happens in the system (e.g. a requirement is created).
               This is the hook the Agent Orchestrator will later
               listen to.
"""
import enum
import uuid

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    requirements = relationship(
        "Requirement", back_populates="project", cascade="all, delete-orphan"
    )
    events = relationship(
        "Event", back_populates="project", cascade="all, delete-orphan"
    )


class RequirementStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    in_progress = "in_progress"
    done = "done"


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(
        Enum(RequirementStatus), nullable=False, default=RequirementStatus.draft
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="requirements")
    events = relationship(
        "Event", back_populates="requirement", cascade="all, delete-orphan"
    )


class EventType(str, enum.Enum):
    requirement_created = "requirement_created"
    requirement_updated = "requirement_updated"
    requirement_deleted = "requirement_deleted"


class Event(Base):
    """
    An append-only record of something that happened in the platform.

    This is intentionally generic (event_type + payload) rather than
    one table per event kind, since the orchestration layer that
    consumes these events (Objective 2 in the FYP proposal) will need
    to handle many event types beyond just requirements.
    """

    __tablename__ = "events"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    project_id = Column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False)
    requirement_id = Column(
        UUID(as_uuid=False), ForeignKey("requirements.id"), nullable=True
    )
    event_type = Column(Enum(EventType), nullable=False)
    payload = Column(Text, nullable=True)  # JSON-serialized snapshot/details
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="events")
    requirement = relationship("Requirement", back_populates="events")
