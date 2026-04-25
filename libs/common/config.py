from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "legal-ai"
    database_url: str = Field(default="postgresql+asyncpg://legal_ai:legal_ai_password@localhost:5432/legal_ai")
    redis_url: str = Field(default="redis://localhost:6379/0")
    jwt_secret_key: str = Field(default="change-me")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = 60

    auth_service_url: str = Field(default="http://localhost:8001")
    ingestion_service_url: str = Field(default="http://localhost:8002")
    classification_service_url: str = Field(default="http://localhost:8003")
    rag_service_url: str = Field(default="http://localhost:8004")
    compliance_service_url: str = Field(default="http://localhost:8005")
    workflow_service_url: str = Field(default="http://localhost:8006")

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4.1-mini"
    gemini_api_key: str | None = None
    gemini_project_id: str | None = None
    gemini_location: str = "us-central1"
    gemini_model: str = "gemini-1.5-pro"
    llm_provider: str = "vertex"
    embedding_provider: str = "deterministic"
    embedding_dimension: int = 1536
    upload_dir: str = "/tmp/legal_uploads"
    auto_migrate_db: bool = True

    bootstrap_admin_email: str = "admin@example.com"
    bootstrap_admin_password: str = "ChangeMe123!"
    bootstrap_admin_token: str = "bootstrap-admin-token"

    max_upload_size_mb: int = 15


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
