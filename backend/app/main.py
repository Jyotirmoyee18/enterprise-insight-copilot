from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, reports, uploads

app = FastAPI(title="Enterprise Insight Copilot", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
