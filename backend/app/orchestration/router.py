"""
Cost-tier router. Kept deliberately tiny and centralized: every place that
needs a model asks for a *tier* (see llm_client.call_llm), and this module
is the one place tier-to-model policy would be tuned in production (e.g.
"route to cheap tier unless the request touches >2 data sources").
"""


def classify_intent_tier() -> str:
    return "cheap"  # intent classification never needs the large model


def synthesis_tier(state: dict) -> str:
    sources_used = sum(
        bool(state.get(k)) for k in ("sql_result", "doc_result", "vision_result")
    )
    # Single-source questions are usually simple enough for the cheap tier;
    # true cross-source synthesis gets the large model.
    return "large" if sources_used >= 2 else "cheap"
