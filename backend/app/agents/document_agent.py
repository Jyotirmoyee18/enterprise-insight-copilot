"""
Document agent — RAG over unstructured docs (contracts, compliance reports).

Production path: Azure Document Intelligence (layout + prebuilt models)
parses scanned PDFs -> chunks -> embeddings -> vector store (pgvector /
Azure AI Search). See app/integrations/azure_doc_intelligence.py for the
real integration point.

This scaffold ships a small in-memory corpus + TF-IDF retrieval so the RAG
path is fully exercised (retrieval, grounding, citations) without needing
cloud credentials or a vector DB running.
"""
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.integrations.azure_doc_intelligence import get_document_corpus


@dataclass
class Chunk:
    doc_id: str
    page: int
    text: str


def _load_corpus() -> list[Chunk]:
    raw = get_document_corpus()  # stubbed Azure Document Intelligence output
    return [Chunk(doc_id=d["doc_id"], page=d["page"], text=d["text"]) for d in raw]


_CORPUS = _load_corpus()
_VECTORIZER = TfidfVectorizer(stop_words="english")
_MATRIX = _VECTORIZER.fit_transform([c.text for c in _CORPUS])


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    q_vec = _VECTORIZER.transform([query])
    scores = cosine_similarity(q_vec, _MATRIX).flatten()
    ranked = sorted(zip(_CORPUS, scores), key=lambda x: x[1], reverse=True)[:top_k]
    return [
        {"doc_id": c.doc_id, "page": c.page, "text": c.text, "score": round(float(s), 3)}
        for c, s in ranked
        if s > 0
    ]


async def run_document_agent(state: dict) -> dict:
    hits = retrieve(state["user_query"])
    return {"doc_result": {"citations": hits, "summary": _summarize(hits)}}


def _summarize(hits: list[dict]) -> str:
    if not hits:
        return "No relevant contract or compliance passages found for this query."
    lead = hits[0]
    return f"Most relevant passage ({lead['doc_id']}, p.{lead['page']}): {lead['text'][:220]}"
