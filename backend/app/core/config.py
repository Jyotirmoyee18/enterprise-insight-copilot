"""Central configuration, loaded from environment variables (.env)."""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Model tiering — see orchestration/router.py for how these get used
    cheap_model_provider: str = os.getenv("CHEAP_MODEL_PROVIDER", "none")
    cheap_model_name: str = os.getenv("CHEAP_MODEL_NAME", "gpt-4o-mini")
    large_model_provider: str = os.getenv("LARGE_MODEL_PROVIDER", "none")
    large_model_name: str = os.getenv("LARGE_MODEL_NAME", "gpt-4o")

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    azure_doc_intelligence_endpoint: str = os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT", "")
    azure_doc_intelligence_key: str = os.getenv("AZURE_DOC_INTELLIGENCE_KEY", "")
    azure_speech_key: str = os.getenv("AZURE_SPEECH_KEY", "")
    azure_speech_region: str = os.getenv("AZURE_SPEECH_REGION", "")

    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "")
    gcp_document_ai_processor_id: str = os.getenv("GCP_DOCUMENT_AI_PROCESSOR_ID", "")

    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/warehouse.db")

    @property
    def has_real_llm(self) -> bool:
        return self.cheap_model_provider != "none" or self.large_model_provider != "none"


settings = Settings()
