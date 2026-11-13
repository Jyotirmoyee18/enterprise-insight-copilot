"""
Azure Document Intelligence integration point.

Real implementation (when AZURE_DOC_INTELLIGENCE_KEY is set) would call:

    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.core.credentials import AzureKeyCredential
    client = DocumentIntelligenceClient(endpoint, AzureKeyCredential(key))
    poller = client.begin_analyze_document("prebuilt-layout", document=file_bytes)
    result = poller.result()
    # -> result.paragraphs / result.tables, each with bounding regions and page numbers

That client call is intentionally not wired up here (needs live credentials
and a document to point at). Instead this returns a small stand-in corpus —
a mocked *output* of that pipeline — so document_agent.py's retrieval and
citation logic can run and be tested end-to-end offline. Swap
`get_document_corpus()` for the real client call + chunker in production.
"""
from app.core.config import settings


def get_document_corpus() -> list[dict]:
    if settings.azure_doc_intelligence_key:
        raise NotImplementedError(
            "Real Azure Document Intelligence credentials detected -- wire up "
            "DocumentIntelligenceClient.begin_analyze_document here."
        )

    # Stand-in extraction output: a few supplier-contract style passages.
    return [
        {
            "doc_id": "supplier-contract-northeast-2026.pdf",
            "page": 3,
            "text": (
                "Section 4.2 Rebate Terms: Supplier shall issue a 3% volume "
                "rebate on Beverages category purchases in any quarter where "
                "sell-through exceeds 95% of the agreed target revenue for "
                "the Northeast region."
            ),
        },
        {
            "doc_id": "supplier-contract-northeast-2026.pdf",
            "page": 5,
            "text": (
                "Section 6.1 Compliance Audit: Retailer agrees to conduct "
                "quarterly shelf-compliance audits confirming planogram "
                "adherence for all Snacks SKUs across West region stores."
            ),
        },
        {
            "doc_id": "vendor-master-agreement.pdf",
            "page": 12,
            "text": (
                "Section 9.4 Inventory Thresholds: Days-of-inventory exceeding "
                "60 for any SKU triggers a mandatory markdown review within "
                "10 business days."
            ),
        },
        {
            "doc_id": "q1-2026-compliance-report.pdf",
            "page": 1,
            "text": (
                "Executive summary: Two Midwest locations were flagged for "
                "planogram violations in the Beverages category during the "
                "Q1 2026 audit cycle; remediation confirmed by Feb 2026."
            ),
        },
    ]
