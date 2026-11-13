"""Report download endpoint -- serves the PPTX produced by content_agent."""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

REPORTS_DIR = Path(__file__).resolve().parents[2] / "data" / "reports"

router = APIRouter()


@router.get("/reports/{session_id}")
async def get_report(session_id: str):
    path = REPORTS_DIR / f"report_{session_id}.pptx"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found -- generate it via /chat first")
    return FileResponse(path, filename=path.name)
