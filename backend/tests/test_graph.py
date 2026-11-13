"""
Smoke test for the full LangGraph pipeline. Runs with zero API keys (uses
the deterministic template-engine fallback in llm_client), so it's safe for
CI.

Run: pytest backend/tests/test_graph.py -v
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.seed import seed
from app.orchestration.graph import copilot_graph


def test_full_pipeline_runs_end_to_end():
    seed()

    async def run():
        state = {
            "session_id": "test-session",
            "user_query": (
                "How did the Northeast region do in 2026 Q2 versus target, and are "
                "there any contract terms or shelf issues I should know about?"
            ),
            "cost_usd": 0.0,
            "model_trace": [],
        }
        return await copilot_graph.ainvoke(state)

    final = asyncio.run(run())

    assert final["sql_result"]["rows"], "SQL agent should return at least one row"
    assert final["doc_result"]["citations"], "Document agent should retrieve citations"
    assert final["insight"], "Insight agent should produce a synthesized insight"
    assert final["output_path"].endswith(".pptx"), "Content agent should produce a .pptx"
    assert Path(final["output_path"]).exists(), "Report file should actually be written to disk"


def test_single_source_query_skips_unused_agents():
    async def run():
        state = {
            "session_id": "test-session-2",
            "user_query": "What was West region revenue in 2026 Q1?",
            "cost_usd": 0.0,
            "model_trace": [],
        }
        return await copilot_graph.ainvoke(state)

    final = asyncio.run(run())
    assert final["intent"] == ["sql"]
    assert final.get("doc_result") is None
    assert final.get("vision_result") is None


if __name__ == "__main__":
    test_full_pipeline_runs_end_to_end()
    test_single_source_query_skips_unused_agents()
    print("All tests passed.")
