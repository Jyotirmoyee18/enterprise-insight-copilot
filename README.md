# Enterprise Insight Copilot

A multi-agent business-intelligence and reporting system: ask a natural-language
question that spans structured sales data, unstructured contracts/compliance
docs, and shelf-audit images, and get back a synthesized answer plus a
generated PPTX report — orchestrated end to end with LangGraph.

Full design rationale, architecture, and roadmap: see `project_blueprint.md`
(or ask the assistant that generated this for the write-up again).

**This scaffold runs with zero cloud credentials.** Azure Document
Intelligence, GCP Document AI/Vertex vision, and any LLM provider are all
wired as clearly-marked integration points with deterministic offline
fallbacks (see `backend/app/integrations/` and `backend/app/core/llm_client.py`),
so you can clone this, run two commands, and see the whole pipeline work —
then swap in real credentials incrementally, agent by agent.

## Quick start

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app/db/seed.py          # creates a sample sales/inventory SQLite DB
cp .env.example .env           # add real API keys/credentials here later
uvicorn app.main:app --reload --port 8000
```

Try it without the frontend:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo","query":"How did the Northeast region do in 2026 Q2 versus target, and are there any contract terms or shelf issues I should know about?"}'
```

Run the smoke tests:

```bash
pytest tests/test_graph.py -v
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the Vite dev server proxies `/api` to the
backend on port 8000.

### Docker

```bash
cd infra
docker compose up --build
```

## What's real vs. stubbed in this scaffold

| Piece | Status |
|---|---|
| LangGraph supervisor graph, conditional routing, fan-out/fan-in | **Real** — `orchestration/graph.py` |
| SQL agent (SQLite, entity extraction, KPI computation) | **Real** — runs real queries against seeded data |
| Document agent (TF-IDF retrieval, citations) | **Real** retrieval logic, over a small **stand-in corpus** (swap for Azure Document Intelligence output — see `integrations/azure_doc_intelligence.py`) |
| Vision agent | **Real** structured-output contract, over **stand-in detections** (swap for GCP Document AI/Vertex — see `integrations/gcp_document_ai.py`) |
| Insight agent | **Real** cross-source prompt assembly + cost-tier routing; calls a real LLM if `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` is set, otherwise a deterministic template fallback |
| Content agent | **Real** — generates an actual `.pptx` file via `python-pptx`, either from scratch or by filling an uploaded template |
| Microsoft Agent Framework / Google ADK wrappers | **Sketched**, not imported by the graph (see comments in `agents/vision_agent.py` and the architecture doc) — they need live Azure/GCP projects to run; the scaffold shows exactly where they plug in |
| Cost tracking | **Real** — every LLM call records estimated `$` and model/tier used, returned in the API response |

## Repository layout

See `project_blueprint.md` §5 for the full annotated tree.

## Next steps to make this production-grade

1. Swap the stub corpora in `integrations/` for live Azure Document Intelligence
   and GCP Document AI calls once you have credentials.
2. Replace SQLite with your real warehouse (Postgres/Snowflake/BigQuery) and
   widen `sql_agent.py`'s query templates or move to a full LangChain SQL toolkit.
3. Add a Postgres checkpointer to the LangGraph compile step for durable,
   resumable multi-minute report jobs.
4. Wire the Microsoft Agent Framework and Google ADK sketches into live
   agents once each cloud project is provisioned.
5. Add auth (OAuth2/JWT) to the FastAPI gateway — currently open for local dev.
