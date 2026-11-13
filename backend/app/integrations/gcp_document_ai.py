"""
GCP Document AI / Vertex vision integration point.

Real implementation (when GCP_PROJECT_ID + GOOGLE_APPLICATION_CREDENTIALS are
set) would call Document AI for OCR-heavy shelf-tag/receipt extraction:

    from google.cloud import documentai_v1 as documentai
    client = documentai.DocumentProcessorServiceClient()
    name = client.processor_path(project_id, location, processor_id)
    result = client.process_document(request={"name": name, "raw_document": {...}})
    # -> result.document.entities / .pages[].tokens

and/or a Vertex AI vision model for object detection on shelf photos
(facings, gaps, misplaced SKUs).

Not wired to live GCP here (needs credentials + real images). Returns a
structured, deterministic stand-in so vision_agent.py's downstream logic
(anomaly flags, confidence, bounding info) is exercised end-to-end offline.
"""
import hashlib

from app.core.config import settings


def analyze_shelf_image(image_ref: str) -> dict:
    if settings.gcp_document_ai_processor_id:
        raise NotImplementedError(
            "Real GCP Document AI credentials detected -- wire up "
            "DocumentProcessorServiceClient.process_document here."
        )

    # Deterministic stand-in: hash the image reference so the same input
    # always yields the same mocked detections (useful for demos/tests).
    seed = int(hashlib.sha256(image_ref.encode()).hexdigest(), 16) % 1000
    out_of_stock = seed % 4 == 0
    planogram_violation = seed % 5 == 0

    return {
        "image_ref": image_ref,
        "detected_skus": ["SKU-1001", "SKU-1003"] if not out_of_stock else ["SKU-1003"],
        "out_of_stock_flag": out_of_stock,
        "planogram_violation": planogram_violation,
        "confidence": round(0.82 + (seed % 15) / 100, 2),
    }
