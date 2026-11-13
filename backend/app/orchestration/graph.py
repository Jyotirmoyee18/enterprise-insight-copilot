"""
LangGraph supervisor -- the top-level orchestrator.

Graph shape:

    classify_intent --(fan-out on intent)--> {sql_node, doc_node, vision_node}
                                                      |
                                                      v
                                                insight_node
                                                      |
                                                      v
                                                content_node --> END

classify_intent is a cheap-tier call (see router.classify_intent_tier);
insight_node's tier is decided dynamically by router.synthesis_tier based
on how many sources actually got used, which is the main cost lever in
this graph.
"""
from langgraph.graph import END, StateGraph

from app.agents.content_agent import run_content_agent
from app.agents.document_agent import run_document_agent
from app.agents.insight_agent import run_insight_agent
from app.agents.sql_agent import run_sql_agent
from app.agents.vision_agent import run_vision_agent
from app.core.llm_client import call_llm
from app.orchestration.router import classify_intent_tier
from app.orchestration.state import CopilotState

CLASSIFY_SYSTEM = (
    "classify the user's request into one or more of: sql, doc, vision. "
    "Respond with a comma-separated list only, e.g. 'sql,doc'."
)


async def classify_intent(state: CopilotState) -> CopilotState:
    result = await call_llm(state["user_query"], tier=classify_intent_tier(), system=CLASSIFY_SYSTEM)
    intents = [i.strip() for i in result.text.split(",") if i.strip() in ("sql", "doc", "vision")]
    state["intent"] = intents or ["sql"]
    state["cost_usd"] = state.get("cost_usd", 0.0) + result.estimated_cost_usd
    state["model_trace"] = state.get("model_trace", []) + [
        {"node": "classify_intent", "provider": result.provider, "model": result.model}
    ]
    return state


def route_after_classify(state: CopilotState) -> list[str]:
    mapping = {"sql": "sql_node", "doc": "doc_node", "vision": "vision_node"}
    targets = [mapping[i] for i in state.get("intent", []) if i in mapping]
    return targets or ["insight_node"]


def build_graph():
    graph = StateGraph(CopilotState)

    graph.add_node("classify_intent", classify_intent)
    graph.add_node("sql_node", run_sql_agent)
    graph.add_node("doc_node", run_document_agent)
    graph.add_node("vision_node", run_vision_agent)
    graph.add_node("insight_node", run_insight_agent)
    graph.add_node("content_node", run_content_agent)

    graph.set_entry_point("classify_intent")
    graph.add_conditional_edges(
        "classify_intent",
        route_after_classify,
        ["sql_node", "doc_node", "vision_node", "insight_node"],
    )
    for node in ("sql_node", "doc_node", "vision_node"):
        graph.add_edge(node, "insight_node")
    graph.add_edge("insight_node", "content_node")
    graph.add_edge("content_node", END)

    return graph.compile()


copilot_graph = build_graph()
