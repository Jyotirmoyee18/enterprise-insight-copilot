"""Shared state schema threaded through every node in the graph."""
from typing import Any, Optional, TypedDict


class CopilotState(TypedDict, total=False):
    session_id: str
    user_query: str
    image_refs: list[str]
    template_path: Optional[str]

    intent: list[str]

    sql_result: Optional[dict[str, Any]]
    doc_result: Optional[dict[str, Any]]
    vision_result: Optional[dict[str, Any]]

    insight: Optional[str]
    output_path: Optional[str]
    narration_path: Optional[str]

    cost_usd: float
    model_trace: list[dict[str, str]]
