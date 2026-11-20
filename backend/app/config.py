"""Application configuration loaded from environment variables / .env file."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings object. All values can be overridden via environment
    variables or a `.env` file placed in the `backend/` directory."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ------------------------------------------------------------------ app
    app_name: str = "CareerPilot AI"
    app_version: str = "1.0.0"
    api_prefix: str = "/api"
    debug: bool = False

    # --------------------------------------------------------------- gemini
    # Primary AI provider (per project spec). Get a key at
    # https://aistudio.google.com/apikey and put it in backend/.env
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_temperature: float = 0.2
    ai_max_output_tokens: int = 8192
    ai_request_timeout_seconds: int = 120

    # ------------------------------------------------------ AI bridge (fallback)
    # Optional local OpenAI-style bridge (mini-services/ai-bridge) that wraps
    # the sandbox LLM. Used ONLY when GEMINI_API_KEY is not configured so the
    # application stays fully functional in demo environments.
    ai_bridge_url: str = "http://127.0.0.1:8010"
    ai_bridge_enabled: bool = True
    ai_bridge_timeout_seconds: int = 120

    # ----------------------------------------------------------------- cors
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # -------------------------------------------------------------- uploads
    max_upload_size_mb: int = 5
    min_resume_text_chars: int = 30

    # ------------------------------------------------------------- scraping
    scrape_timeout_seconds: int = 15
    max_redirects: int = 5
    max_content_bytes: int = 2_000_000
    scrape_user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) CareerPilotAI/1.0 (+job-description-analysis)"
    )

    # ----------------------------------------------- scoring weights (sum=1)
    weight_technical_skills: float = 0.40
    weight_education: float = 0.15
    weight_experience: float = 0.20
    weight_project_relevance: float = 0.25

    # ------------------------------------------------------------- database
    # Note: named CP_DATABASE_URL to avoid clashing with the sandbox's
    # Prisma-style DATABASE_URL env var.
    cp_database_url: str = "sqlite:///./career_pilot.db"

    # ------------------------------------------------------------ interview
    default_questions_per_category: int = 5
    max_questions_per_category: int = 10

    @property
    def allowed_origin_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
