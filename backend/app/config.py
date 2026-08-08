"""
Centralized application configuration.
Loaded once and imported everywhere as `settings`.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Groq LLM
    groq_api_key: str = "changeme"
    groq_model: str = "llama-3.3-70b-versatile"

    # Database
    database_url: str = "postgresql://legal_user:legal_pass@localhost:5432/legal_intelligence_db"

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # App behavior
    app_env: str = "development"
    max_upload_mb: int = 15
    chunk_size: int = 800
    chunk_overlap: int = 120
    top_k_retrieval: int = 5
    cors_origins: str = "http://localhost:8501,http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
