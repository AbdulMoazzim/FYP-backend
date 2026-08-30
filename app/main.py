"""
Application entrypoint.

Run with:  uvicorn app.main:app --reload
Docs at:   http://localhost:8000/docs
"""
from fastapi import FastAPI

from app.database import Base, engine
from app.routers import projects, requirements, events

# Creates tables that don't exist yet. Fine for this milestone;
# switch to Alembic migrations once the schema needs to evolve
# without dropping data (see README).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Multi-Agent Scrum Platform — Backend (Milestone 1)",
    description=(
        "Stores requirements and emits events for them. This is the "
        "foundation the Event Processing Engine / Agent Orchestrator "
        "will build on in later milestones."
    ),
    version="0.1.0",
)

app.include_router(projects.router)
app.include_router(requirements.router)
app.include_router(events.router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
