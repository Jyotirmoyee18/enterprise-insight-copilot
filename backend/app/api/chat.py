"""
Chat endpoints.

`/chat` -- synchronous, returns the full final state (good for simple
clients / testing).
`/chat/stream` -- Server-Sent Events, emits one event per graph node as it
completes so the frontend's AgentTimeline can show live progress
("SQL agent done", "Insight agent working...").
"""
import json

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.models.schemas import ChatRequest, ChatResponse
from app.orchestration.graph import copilot_graph

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    initial_state = {
        "session_id": request.session_id,
        "user_query": request.query,
        "image_refs": request.image_refs,
        "template_path": request.template_path,
        "cost_usd": 0.0,
        "model_trace": [],
    }
    final_state = await copilot_graph.ainvoke(initial_state)
    return ChatResponse(**{k: final_state.get(k) for k in ChatResponse.model_fields})


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    initial_state = {
        "session_id": request.session_id,
        "user_query": request.query,
        "image_refs": request.image_refs,
        "template_path": request.template_path,
        "cost_usd": 0.0,
        "model_trace": [],
    }

    async def event_generator():
        async for event in copilot_graph.astream(initial_state):
            for node_name, node_state in event.items():
                yield {
                    "event": "agent_update",
                    "data": json.dumps({"node": node_name, "state_keys": list(node_state.keys())}),
                }
        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(event_generator())
