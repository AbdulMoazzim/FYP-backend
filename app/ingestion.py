"""
Context ingestion layer (Day 2).

Takes a raw ProjectContext payload (dict, as received over the API),
validates it against the finalized schema, and normalizes it for
downstream use (context building -> LLM reasoning -> AgentResult).
"""

from datetime import datetime, timezone
from typing import Any, Dict

from pydantic import ValidationError

from .schemas import ProjectContext


class IngestionError(Exception):
    """Raised when a ProjectContext payload fails validation."""

    def __init__(self, message: str, details: Any = None):
        super().__init__(message)
        self.details = details


def ingest_project_context(raw: Dict[str, Any]) -> ProjectContext:
    """
    Validate and normalize a raw ProjectContext dict.

    Rejects payloads missing required fields rather than silently
    defaulting them (per the Day 2 design notes). Pydantic also
    normalizes date strings into real datetime objects here, so
    downstream staleness checks (e.g. "blocked for N days") are plain
    datetime subtraction rather than string parsing.
    """
    try:
        context = ProjectContext.model_validate(raw)
    except ValidationError as exc:
        raise IngestionError(
            "ProjectContext failed validation", details=exc.errors()
        ) from exc

    return context


def days_since(dt: datetime, now: datetime | None = None) -> float:
    """Helper used by blocker/risk detection: how many days old is `dt`."""
    now = now or datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (now - dt).total_seconds() / 86400
