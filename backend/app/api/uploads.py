"""Template/document upload endpoint. Stores files under data/uploads and
returns a path the /chat endpoint can reference as template_path."""
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "data" / "uploads"

router = APIRouter()


@router.post("/uploads/template")
async def upload_template(file: UploadFile):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / f"{uuid.uuid4().hex}_{file.filename}"
    dest.write_bytes(await file.read())
    return {"template_path": str(dest)}
