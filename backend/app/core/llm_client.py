"""
Thin LLM abstraction used by every agent.

Cost-optimization is enforced HERE, not per-agent: callers ask for a "tier"
(cheap|large), never a specific model name, so swapping providers or
adjusting which tier handles which task is a one-line change in
orchestration/router.py.

If no provider is configured, calls fall back to deterministic
template-based text so the whole pipeline runs end-to-end with zero API
keys -- useful for demos, tests, and CI.
"""
from dataclasses import dataclass

from app.core.config import settings


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str
    tier: str
    estimated_cost_usd: float


# Rough $/1K tokens for cost tracking (illustrative, not billing-accurate)
_COST_PER_1K = {
    "cheap": 0.00025,
    "large": 0.0025,
}


async def call_llm(prompt: str, tier: str = "cheap", system: str | None = None) -> LLMResult:
    provider = (
        settings.cheap_model_provider if tier == "cheap" else settings.large_model_provider
    )
    model = settings.cheap_model_name if tier == "cheap" else settings.large_model_name

    if provider == "none":
        # Deterministic fallback -- no external call, no cost.
        return LLMResult(
            text=_fallback_response(prompt, system),
            provider="fallback",
            model="template-engine",
            tier=tier,
            estimated_cost_usd=0.0,
        )

    if provider == "openai":
        text = await _call_openai(prompt, system, model)
    elif provider == "anthropic":
        text = await _call_anthropic(prompt, system, model)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")

    approx_tokens = (len(prompt) + len(text)) / 4
    cost = (approx_tokens / 1000) * _COST_PER_1K[tier]
    return LLMResult(text=text, provider=provider, model=model, tier=tier, estimated_cost_usd=cost)


async def _call_openai(prompt: str, system: str | None, model: str) -> str:
    import httpx

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={"model": model, "messages": messages, "temperature": 0.2},
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _call_anthropic(prompt: str, system: str | None, model: str) -> str:
    import httpx

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": model,
                "max_tokens": 1024,
                "system": system or "",
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]


def _fallback_response(prompt: str, system: str | None) -> str:
    """Deterministic stand-in so the graph is fully runnable without API keys."""
    if system and "classify" in system.lower():
        return _fallback_classify(prompt)
    return (
        "[template-engine summary] Based on the retrieved data: " + prompt[:280].strip() + "..."
    )


def _fallback_classify(prompt: str) -> str:
    p = prompt.lower()
    intents = []
    if any(k in p for k in ["sales", "revenue", "sell", "kpi", "margin", "inventory", "sku", "region"]):
        intents.append("sql")
    if any(k in p for k in ["contract", "clause", "compliance", "agreement", "invoice", "policy"]):
        intents.append("doc")
    if any(k in p for k in ["photo", "image", "shelf", "planogram", "picture"]):
        intents.append("vision")
    if not intents:
        intents = ["sql"]
    return ",".join(intents)
