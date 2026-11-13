from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    query: str
    image_refs: Optional[list[str]] = None
    template_path: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    intent: list[str]
    sql_result: Optional[dict] = None
    doc_result: Optional[dict] = None
    vision_result: Optional[dict] = None
    insight: Optional[str] = None
    output_path: Optional[str] = None
    cost_usd: float
    model_trace: list[dict]
