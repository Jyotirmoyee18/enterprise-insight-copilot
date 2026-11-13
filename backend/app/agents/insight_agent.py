"""
Insight agent -- cross-source synthesis (the one node where the large/
expensive model tier earns its keep: genuine reasoning across SQL, document,
and vision outputs rather than extraction).
"""
from app.core.llm_client import call_llm
from app.orchestration.router import synthesis_tier

SYSTEM_PROMPT = (
    "You are a retail merchandising analyst. Given structured sales data, "
    "supplier-contract excerpts, and shelf-audit findings, write a concise, "
    "specific insight: 1) the headline number, 2) why it matters (tie to "
    "contract terms or shelf findings if relevant), 3) one recommended action. "
    "Keep it under 120 words. Do not invent numbers not present in the data."
)


async def run_insight_agent(state: dict) -> dict:
    prompt = _build_prompt(state)
    tier = synthesis_tier(state)
    result = await call_llm(prompt, tier=tier, system=SYSTEM_PROMPT)

    state["insight"] = result.text
    state["cost_usd"] = state.get("cost_usd", 0.0) + result.estimated_cost_usd
    state["model_trace"] = state.get("model_trace", []) + [
        {"node": "insight_agent", "provider": result.provider, "model": result.model}
    ]
    return state


def _build_prompt(state: dict) -> str:
    parts = [f"User question: {state['user_query']}"]

    sql = state.get("sql_result")
    if sql and sql.get("rows"):
        parts.append("Sales data:")
        for r in sql["rows"]:
            parts.append(
                f"  - {r['region']} {r['quarter']}: revenue ${r['revenue']:,.0f} "
                f"vs target ${r['target']:,.0f} ({r['attainment_pct']}% attainment, {r['yoy_or_qoq_flag']})"
            )

    doc = state.get("doc_result")
    if doc and doc.get("citations"):
        parts.append("Relevant contract/compliance passages:")
        for c in doc["citations"]:
            parts.append(f"  - [{c['doc_id']} p.{c['page']}] {c['text']}")

    vision = state.get("vision_result")
    if vision and vision.get("detections"):
        parts.append("Shelf-audit findings:")
        for d in vision["detections"]:
            parts.append(
                f"  - {d['image_ref']}: out_of_stock={d['out_of_stock_flag']}, "
                f"planogram_violation={d['planogram_violation']} (confidence {d['confidence']})"
            )

    return "\n".join(parts)
