# Enterprise Insight Copilot — Multi-Agent BI & Reporting System

An end-to-end blueprint you can build from. Business-problem framing, architecture, agent design, cost controls, folder structure, code skeletons, and a build roadmap.

---

## 1. The business problem

**Who:** a retail/CPG merchandising or FP&A team (works equally for supply chain, insurance claims, or field-audit teams — swap the domain nouns).

**The pain today:**
- Analysts pull sales/inventory numbers from a SQL warehouse by hand.
- Supplier contracts, compliance certificates, and audit reports arrive as scanned PDFs that someone reads line by line.
- Store/shelf-compliance photos get eyeballed one at a time to spot planogram violations or stock-outs.
- Every week/quarter, someone manually assembles a QBR deck or board report in a fixed corporate PowerPoint template — copy-pasting charts, writing the "so what" narrative, and formatting it to match brand guidelines.

**The cost:** 2–4 analyst-days per report cycle, inconsistent narrative quality, slow turnaround on ad-hoc questions ("why did region X miss target?"), and compliance risk when contract terms or shelf audits aren't reviewed promptly.

**What the system does instead:** a person asks a natural-language question or drops in a set of source documents/images, and a graph of specialist agents pulls the structured data, reads the unstructured documents, analyzes the images, reasons over all three, and emits a finished artifact — a chat answer, a live KPI dashboard, or a fully formatted PPTX/DOCX in the company's own template — with citations back to source rows, pages, and images.

---

## 2. Architecture at a glance

The diagram above is the shape of it. In words:

1. **React frontend** — chat interface, KPI dashboard, template upload, and a "generate report" action. Streams agent progress over WebSocket/SSE so the user sees which agent is working.
2. **FastAPI gateway** — single entry point: auth (OAuth2/JWT), request validation, rate limiting, and the **cost router** (decides which model tier handles the request before it ever reaches an agent).
3. **LangGraph supervisor** — a `StateGraph` that classifies intent and routes to one or more specialist agents, holds conversation/report state, and supports checkpointing so a multi-minute report-generation run can be paused, resumed, or retried.
4. **Specialist agents** (each independently swappable/scalable — see §4):
   - **SQL agent** — natural language → SQL → KPI computation.
   - **Document agent** — RAG over contracts, invoices, compliance PDFs.
   - **Vision agent** — shelf/product/receipt image analysis.
   - **Insight agent** — cross-agent synthesis: trends, anomalies, root causes.
5. **Content generation agent** — renders the insight agent's output into the user's uploaded template (PPTX/DOCX), builds the live dashboard payload, and optionally narrates a summary via TTS.

### Why four frameworks, not one

The brief asks for LangGraph/LangChain, Microsoft Agent Framework, and Google ADK expertise. In a real enterprise these show up for different reasons, not as a single monolith:

| Framework | Where it earns its place here |
|---|---|
| **LangGraph** | The top-level orchestrator. Its explicit state graph + checkpointing is the best fit for a long-running, human-in-the-loop-able "generate my QBR deck" workflow that can pause and resume. |
| **LangChain** | Retrieval chains, prompt templates, and the SQL/vector store integrations that back the SQL and Document agents. |
| **Microsoft Agent Framework** (GA April 2026 — the unification of AutoGen + Semantic Kernel) | Used for the agents that live close to Azure AI Services — e.g. the Document agent calling Azure Document Intelligence / Azure Content Understanding. MAF's handoff and concurrent orchestration patterns are a natural fit for "run three extraction specialists on this contract at once." |
| **Google ADK** | Used for the Vision agent when it's cheaper/better to lean on GCP's Document AI + Vertex vision models (e.g. OCR-heavy receipt/shelf-tag extraction, or when the customer's data already lives in BigQuery/GCS). |

Each non-LangGraph agent is wrapped behind a thin FastAPI (or MCP) service with a stable JSON contract, so the LangGraph supervisor treats them as **tools**, not as competing orchestrators. This also means you can demo the same business problem solved by a single-cloud (all-Azure or all-GCP) variant if a client's governance requires it — swap the tool implementation, keep the graph.

---

## 3. Cost-optimized orchestration

This is where a lot of these systems die in production (token bills). Concrete tactics:

- **Model tiering.** Cheap/small model (e.g. a mini/haiku-class model) for: intent classification, SQL draft generation, document chunk triage. Larger model reserved for: final narrative synthesis and template-aware writing. Route decision happens once, in the gateway, and is logged for cost attribution per request.
- **Prebuilt extraction over LLM vision tokens.** Use Azure Document Intelligence's prebuilt invoice/receipt/layout models and GCP Document AI's specialized parsers for structured extraction (tables, key-value pairs, signatures) instead of paying vision-LLM token rates to "read" a document. Reserve the vision LLM call for genuinely unstructured judgment calls (e.g. "does this shelf photo show a planogram violation?").
- **Semantic caching.** Cache (query embedding → answer) pairs for the SQL and Document agents; a large share of BI questions repeat week to week ("what was last month's sell-through by region").
- **Chunk-level RAG budgets.** Retrieve top-k with a reranker rather than stuffing full documents into context; cap tokens per agent call and fail loudly (not silently truncate) if a request would blow the budget.
- **Batch where latency allows.** Nightly KPI recomputation and embedding refresh go through batch APIs at lower cost; only the interactive chat path pays synchronous pricing.
- **Async workers + queue** (Celery/RQ or Azure/GCP native queues) for report generation so a 5-minute PPTX build doesn't hold an HTTP connection or a GPU-priced agent idle.

---

## 4. Agent design

### 4.1 LangGraph supervisor (orchestrator)
- Graph nodes: `classify_intent → {sql_node, doc_node, vision_node} → insight_node → content_node → END`, with conditional edges for multi-source requests (e.g. "compare Q2 sales to what the supplier contract promised" hits both `sql_node` and `doc_node` concurrently, joins at `insight_node`).
- State object carries: user request, resolved entities (region, SKU, date range), partial agent outputs, citations, template metadata, cost-so-far.
- Checkpointed to Postgres so long report-generation jobs survive a restart and support human-in-the-loop approval before the final deck is emitted.

### 4.2 SQL agent (structured data)
- LangChain SQL toolkit (or a custom text-to-SQL chain) against the warehouse (Postgres/BigQuery/Snowflake).
- Schema-aware prompting (only exposes the relevant tables/views per domain) to control cost and reduce hallucinated columns.
- Computes KPIs (sell-through, sell-in, margin, days-of-inventory, YoY/QoQ deltas) and returns both the numbers and the SQL used, for auditability.

### 4.3 Document agent (unstructured data)
- Ingestion: Azure Document Intelligence (layout + prebuilt models) for scanned contracts/invoices; falls back to GCP Document AI for GCS-resident corpora.
- Chunking + embeddings → vector store (pgvector, Azure AI Search, or Vertex AI Search depending on where the data lives).
- Answers grounded with page-level citations; flags contract clauses relevant to the current KPI conversation (e.g. rebate thresholds tied to a sell-through number the SQL agent just computed).

### 4.4 Vision agent (image analysis)
- Shelf-compliance photos → Azure AI Vision / Custom Vision or GCP Vertex vision models for object detection (facings, out-of-stock gaps) and OCR on shelf tags/receipts.
- Google ADK wraps this as a discrete agent so the vision-heavy workload can run on GCP infra independent of the rest of the stack.
- Structured output (JSON: detected SKUs, confidence, bounding boxes, anomaly flags) — never a free-text description — so downstream agents can reason over it deterministically.

### 4.5 Insight agent (reasoning/synthesis)
- Takes the SQL numbers + document findings + vision flags and produces: trend narrative, anomaly explanation, and a ranked list of "so what" bullets.
- This is the one node where the larger/more expensive model earns its keep — it's doing genuine cross-source reasoning, not extraction.

### 4.6 Content generation agent
- **python-pptx / python-docx** to populate the user's own uploaded template — matching existing slide masters, tables, and chart placeholders rather than generating a generic deck from scratch.
- Charts rendered server-side (matplotlib/plotly → image) or as native editable PPTX charts.
- Optional narrated summary via Azure TTS or GCP Text-to-Speech for an audio recap attached to the deck.

---

## 5. Repository layout

```
enterprise-insight-copilot/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, routers, startup
│   │   ├── api/
│   │   │   ├── chat.py             # /chat (SSE/WebSocket streaming)
│   │   │   ├── reports.py          # /reports (generate, status, download)
│   │   │   └── uploads.py          # template & document upload
│   │   ├── orchestration/
│   │   │   ├── graph.py            # LangGraph StateGraph definition
│   │   │   ├── state.py            # shared TypedDict state schema
│   │   │   └── router.py           # cost-tier model router
│   │   ├── agents/
│   │   │   ├── sql_agent.py
│   │   │   ├── document_agent.py   # LangChain RAG + Azure Doc Intelligence
│   │   │   ├── vision_agent.py     # Google ADK wrapper
│   │   │   ├── insight_agent.py
│   │   │   └── content_agent.py    # pptx/docx/tts generation
│   │   ├── integrations/
│   │   │   ├── azure_doc_intelligence.py
│   │   │   ├── gcp_document_ai.py
│   │   │   ├── azure_speech.py
│   │   │   └── ms_agent_framework_client.py
│   │   ├── models/                 # pydantic schemas
│   │   └── core/                   # config, auth, logging, cost tracking
│   ├── workers/                    # Celery/RQ tasks for async report jobs
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── AgentTimeline.tsx   # live "which agent is working" view
│   │   │   ├── KpiDashboard.tsx
│   │   │   └── TemplateUploader.tsx
│   │   ├── hooks/useAgentStream.ts # SSE/WebSocket hook
│   │   └── App.tsx
│   └── package.json
├── infra/
│   ├── docker-compose.yml
│   └── terraform/                  # Azure + GCP resource definitions
└── README.md
```

---

## 6. Key code skeletons

### 6.1 LangGraph supervisor (`orchestration/graph.py`)

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional

class CopilotState(TypedDict):
    user_query: str
    intent: str
    sql_result: Optional[dict]
    doc_result: Optional[dict]
    vision_result: Optional[dict]
    insight: Optional[str]
    template_path: Optional[str]
    output_path: Optional[str]
    cost_usd: float

def classify_intent(state: CopilotState) -> CopilotState:
    # cheap-tier model call: routes to one or more of sql/doc/vision
    ...

def route_after_classify(state: CopilotState) -> list[str]:
    targets = []
    if "sql" in state["intent"]:
        targets.append("sql_node")
    if "doc" in state["intent"]:
        targets.append("doc_node")
    if "vision" in state["intent"]:
        targets.append("vision_node")
    return targets or ["insight_node"]

graph = StateGraph(CopilotState)
graph.add_node("classify_intent", classify_intent)
graph.add_node("sql_node", run_sql_agent)
graph.add_node("doc_node", run_document_agent)
graph.add_node("vision_node", run_vision_agent)
graph.add_node("insight_node", run_insight_agent)
graph.add_node("content_node", run_content_agent)

graph.set_entry_point("classify_intent")
graph.add_conditional_edges("classify_intent", route_after_classify,
                             ["sql_node", "doc_node", "vision_node", "insight_node"])
for n in ["sql_node", "doc_node", "vision_node"]:
    graph.add_edge(n, "insight_node")
graph.add_edge("insight_node", "content_node")
graph.add_edge("content_node", END)

app_graph = graph.compile(checkpointer=postgres_checkpointer)
```

### 6.2 FastAPI streaming endpoint (`api/chat.py`)

```python
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

router = APIRouter()

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def event_generator():
        async for event in app_graph.astream(
            {"user_query": request.query, "cost_usd": 0.0},
            config={"configurable": {"thread_id": request.session_id}},
        ):
            yield {"event": "agent_update", "data": event}
    return EventSourceResponse(event_generator())
```

### 6.3 Vision agent via Google ADK (`agents/vision_agent.py`)

```python
from google.adk.agents import Agent
from app.integrations.gcp_document_ai import extract_document_fields

vision_agent = Agent(
    name="shelf_vision_agent",
    model="gemini-2.5-flash",   # cheap-tier for triage; escalate on low confidence
    instruction="Detect shelf compliance issues and extract SKU/price tags from the image.",
    tools=[extract_document_fields],
)

async def run_vision_agent(state: CopilotState) -> CopilotState:
    result = await vision_agent.run_async(state["image_refs"])
    state["vision_result"] = result.structured_output
    return state
```

### 6.4 Document agent using Microsoft Agent Framework + Azure Document Intelligence

```python
from agent_framework import ChatAgent
from app.integrations.azure_doc_intelligence import analyze_layout

doc_agent = ChatAgent(
    name="contract_agent",
    chat_client=foundry_chat_client,
    instructions="Extract clauses and answer questions about supplier contracts.",
    tools=[analyze_layout, vector_search_tool],
)
```

### 6.5 React streaming hook (`hooks/useAgentStream.ts`)

```typescript
export function useAgentStream(sessionId: string) {
  const [timeline, setTimeline] = useState<AgentEvent[]>([]);

  const send = (query: string) => {
    const es = new EventSource(`/api/chat/stream?session_id=${sessionId}&q=${encodeURIComponent(query)}`);
    es.addEventListener("agent_update", (e) => {
      setTimeline((prev) => [...prev, JSON.parse(e.data)]);
    });
    es.onerror = () => es.close();
  };

  return { timeline, send };
}
```

---

## 7. Build roadmap

| Phase | Scope | Outcome |
|---|---|---|
| 1 — Foundations (1–2 wk) | FastAPI skeleton, auth, Postgres + pgvector, React shell, single SQL agent | User can ask a KPI question in chat and get a grounded number |
| 2 — Documents (1–2 wk) | Azure Document Intelligence ingestion, RAG pipeline, citations | User can ask questions across contracts/reports |
| 3 — Vision (1 wk) | Google ADK vision agent, structured extraction contract | Shelf/receipt photos analyzed and queryable |
| 4 — Orchestration (1–2 wk) | LangGraph supervisor wiring all agents, checkpointing, streaming UI | Multi-source questions routed and synthesized automatically |
| 5 — Content generation (1–2 wk) | Template-aware PPTX/DOCX builder, dashboard payloads, optional TTS narration | One click produces a finished, on-brand report |
| 6 — Cost & hardening (ongoing) | Model tiering, semantic cache, usage dashboards, load testing | Predictable per-request cost, production-ready |

---

## 8. What to demo first

For a portfolio/interview-ready version, the tightest end-to-end slice is: **Phase 1 + Phase 2 + a hardcoded PPTX template in Phase 5** — i.e. "ask a KPI question that also needs a contract clause, get a two-slide deck back." That alone showcases LangGraph orchestration, RAG, cost-aware routing, and template-based generation without needing every specialist agent built out.
