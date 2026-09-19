"""
Context/prompt builder

Turns a validated ProjectContext into a compact, source-tagged tex
block that can be handed to the LLM. Design goals:

- Summarize backlog items grouped by status rather than dumping raw
  JSON, to keep the prompt short and easy to reason over.
- Every fact carries its source_ref inline, so the LLM's response can
  point back to a tagged fact instead of inventing a citation.
- Events are included as a separate, capped, most-recent-first list.
"""

from collections import defaultdict
from typing import List

from .ingestion import days_since
from .schemas import BacklogItem, ProjectContext, SprintEvent

MAX_EVENTS_IN_PROMPT = 10


def _format_backlog_item(item: BacklogItem) -> str:
    age_days = round(days_since(item.last_updated), 1)
    points = f", {item.story_points}sp" if item.story_points is not None else ""
    assignee = item.assignee or "unassigned"
    sources = ",".join(item.source_refs)
    return (
        f"[{item.item_id}] \"{item.title}\" "
        f"({item.status.value}, {item.priority} priority, {assignee}{points}, "
        f"last updated {age_days}d ago) source: {sources}"
    )


def _format_event(event: SprintEvent) -> str:
    return (
        f"[{event.event_id}] ({event.type.value}, {event.timestamp.isoformat()}) "
        f"\"{event.raw_text}\" source: {event.source_ref}"
    )


def build_context_block(context: ProjectContext) -> str:
    """Build the full source-tagged text block for a ProjectContext."""

    lines: List[str] = []

    lines.append(f"PROJECT: {context.project_id}")
    lines.append(
        f"SPRINT: {context.sprint.sprint_id} "
        f"({context.sprint.start_date.date()} to {context.sprint.end_date.date()}) "
        f"— goal: {context.sprint.goal}"
    )
    lines.append("")

    by_status = defaultdict(list)
    for item in context.backlog_items:
        by_status[item.status.value].append(item)

    lines.append("BACKLOG ITEMS (grouped by status):")
    for status in ["blocked", "in_progress", "todo", "done"]:
        items = by_status.get(status, [])
        if not items:
            continue
        lines.append(f"  {status.upper()} ({len(items)}):")
        for item in items:
            lines.append(f"    - {_format_backlog_item(item)}")
    lines.append("")

    if context.events:
        recent_events = sorted(
            context.events, key=lambda e: e.timestamp, reverse=True
        )[:MAX_EVENTS_IN_PROMPT]
        lines.append(f"RECENT EVENTS (most recent first, max {MAX_EVENTS_IN_PROMPT}):")
        for event in recent_events:
            lines.append(f"  - {_format_event(event)}")
    else:
        lines.append("RECENT EVENTS: none")

    return "\n".join(lines)


SYSTEM_PROMPT = """You are the Scrum Master Agent in AGILIRO, a multi-agent \
Scrum assistant. You are given a structured summary of a single sprint's \
backlog and recent events, where every fact is tagged with a source \
reference in the form "source: <ref>".

Your job is to identify, from ONLY the facts given:
1. Blockers — things actively stopping progress right now
2. Risks — things that could become a problem if not addressed
3. Sprint planning recommendations — guidance for the next sprint
4. Sprint monitoring recommendations — guidance on this sprint's health

Rules:
- Every recommendation you produce MUST cite at least one source_ref \
taken verbatim from the tagged facts you were given. Never invent a \
source_ref and never omit one.
- Do not speculate about information that was not provided.
- Respond ONLY as a JSON array of objects, each matching this shape:
  {
    "recommendation_type": "blocker | risk | sprint_planning | sprint_monitoring",
    "summary": "one-line human-readable recommendation",
    "reasoning": "why you are suggesting this",
    "evidence": [{"source_ref": "...", "excerpt": "..."}],
    "confidence": 0.0-1.0,
    "affected_items": ["item_id or sprint_id, ..."]
  }
- Return an empty array if nothing meets the bar for a real blocker, \
risk, or recommendation. Do not manufacture findings to fill the list.
"""


def build_messages(context: ProjectContext) -> list[dict]:
    """Assemble the full message list ready for an LLM chat completion call."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_context_block(context)},
    ]
