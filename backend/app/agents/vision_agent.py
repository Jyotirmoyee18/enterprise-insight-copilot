"""
Vision agent -- shelf/receipt image analysis.

Production path (see docs): wrapped as a Google ADK `Agent` so the
vision-heavy workload can run close to GCP Document AI / Vertex vision
models, independent of the rest of the (Azure-leaning) document pipeline.
The ADK wrapper is sketched in `_adk_agent_sketch()` below -- it's not
imported by the graph, since it needs a live GCP project to actually run.
Structured JSON output (never free text) is the contract every downstream
agent depends on.
"""
from app.integrations.gcp_document_ai import analyze_shelf_image


async def run_vision_agent(state: dict) -> dict:
    image_refs = state.get("image_refs") or _sample_image_refs_for_demo(state)
    detections = [analyze_shelf_image(ref) for ref in image_refs]

    flags = [d for d in detections if d["out_of_stock_flag"] or d["planogram_violation"]]
    return {
        "vision_result": {
            "detections": detections,
            "flagged_count": len(flags),
            "flagged": flags,
        }
    }


def _sample_image_refs_for_demo(state: dict) -> list[str]:
    """If the user didn't upload images, use a couple of demo refs so the
    node still returns something meaningful when explicitly asked to run."""
    region = (state.get("sql_result") or {}).get("entities", {}).get("region", "West")
    return [f"shelf-audit/{region.lower()}/store-014.jpg", f"shelf-audit/{region.lower()}/store-027.jpg"]


def _adk_agent_sketch():
    """Not called by the graph -- reference sketch of the real Google ADK
    wrapper described in the architecture doc."""
    from google.adk.agents import Agent  # requires `google-adk` + GCP creds

    return Agent(
        name="shelf_vision_agent",
        model="gemini-2.5-flash",
        instruction=(
            "Detect shelf compliance issues (out-of-stock gaps, planogram "
            "violations) and extract SKU/price tags from the image. Return "
            "structured JSON only."
        ),
        tools=[analyze_shelf_image],
    )
