"""
Central application configuration.

Everything here is read from environment variables (via a .env file in
development). Nothing secret is ever hardcoded — see .env.example at the
project root for the full list of variables Talkify understands.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "Talkify 2.0"
    ENVIRONMENT: str = "development"  # development | production
    DEBUG: bool = True

    # --- Security ---
    SECRET_KEY: str = "change-me-in-production"  # override via .env
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"

    # --- Database ---
    # Defaults to a local SQLite file so the project runs with zero setup.
    # Set DATABASE_URL to a postgresql+psycopg://... URL for real deployment.
    DATABASE_URL: str = "sqlite:///./talkify.db"

    # --- Storage ---
    UPLOAD_DIR: str = "./storage/uploads"
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: tuple[str, ...] = (".pdf", ".docx", ".txt", ".md", ".csv")

    # --- RAG / ML ---
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384  # matches all-MiniLM-L6-v2
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_SEMANTIC: int = 8
    TOP_K_KEYWORD: int = 8
    TOP_K_FINAL: int = 5
    SEMANTIC_WEIGHT: float = 0.7
    KEYWORD_WEIGHT: float = 0.3
    VECTOR_INDEX_DIR: str = "./storage/vector_indexes"

    # Get a free key at https://console.groq.com — leave blank to run in
    # extractive fallback mode (retrieval + citations, no LLM generation).
    # NOTE: as of late 2026 Groq moved llama-3.1-8b-instant to an
    # Enterprise/contact-sales tier — a normal developer API key will get
    # a permission error calling it. openai/gpt-oss-20b is fast, cheap,
    # and available on the standard developer tier as of this writing.
    # Groq's model lineup changes often — if this default ever fails,
    # check https://console.groq.com/docs/models for a current model ID.
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"

    # --- CORS ---
    # Both localhost and 127.0.0.1 are included because browsers treat them
    # as different origins even though they're the same machine — if your
    # frontend URL bar ever shows 127.0.0.1 instead of localhost (or vice
    # versa), only having one of these here would cause CORS failures.
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:3000", "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Settings are cached so the .env file is only parsed once per process."""
    return Settings()


settings = get_settings()
