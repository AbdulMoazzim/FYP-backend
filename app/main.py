"""
Application entrypoint.

Run with:  uvicorn app.main:app --reload
Docs at:   http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
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

# CORS: lets a frontend running on a different origin (e.g. a React
# dev server on localhost:3000, or your deployed frontend's domain)
# call this API from the browser. Without this, the browser blocks
# the requests even though the API itself would happily respond.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(requirements.router)
app.include_router(events.router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}