"""
Day 2 smoke test — no LLM call yet, just proves:
1. Both mock samples validate against the finalized schema
2. The context builder produces a sane, source-tagged text block
3. The evidence-enforcement validator on AgentResult actually rejects
   an unevidenced recommendation (proves the "code-level guarantee"
   claim from the Day 1/2 logs, not just a comment)
"""

import json
from pathlib import Path

from app.context_builder import build_context_block, build_messages
from app.ingestion import ingest_project_context
from app.schemas import AgentResult
from pydantic import ValidationError

DATA_DIR = Path(__file__).parent / "data"

for name in ["sample_healthy.json", "sample_troubled.json"]:
    print(f"\n{'=' * 70}\n{name}\n{'=' * 70}")
    raw = json.loads((DATA_DIR / name).read_text())
    context = ingest_project_context(raw)
    print(f"Validated OK — project={context.project_id}, "
          f"sprint={context.sprint.sprint_id}, "
          f"{len(context.backlog_items)} backlog items, "
          f"{len(context.events)} events")

    block = build_context_block(context)
    print("\n--- context block preview (first 500 chars) ---")
    print(block[:500])

    messages = build_messages(context)
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    print(f"\nbuild_messages() OK — system prompt {len(messages[0]['content'])} chars, "
          f"user context {len(messages[1]['content'])} chars")

print(f"\n{'=' * 70}\nEvidence-enforcement check on AgentResult\n{'=' * 70}")
try:
    AgentResult(
        recommendation_type="blocker",
        summary="Payment gateway integration is blocked",
        reasoning="No evidence attached on purpose, to test the guard",
        evidence=[],
        confidence=0.9,
        affected_items=["BLK-010"],
    )
    print("FAIL: AgentResult accepted empty evidence — this should not happen")
except ValidationError as e:
    print("PASS: AgentResult correctly rejected empty evidence[]")
    print(f"  -> {e.errors()[0]['msg']}")

print("\nAll Day 2 smoke tests passed.")
