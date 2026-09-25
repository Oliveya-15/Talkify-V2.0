from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Talkify"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str
    DATABASE_URL: str
    UPLOAD_DIR: str = "./storage/uploads"
    MAX_UPLOAD_SIZE_MB: int = 25

    # --- Auth Settings ---
    ALGORITHM: str = "HS256" 
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 

    # --- Document Upload Settings ---
    # ADD THIS LINE (Match the extensions your frontend accepts)
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".docx", ".txt", ".md", ".csv"]

    # --- RAG / ML ---
    GEMINI_API_KEY: str = ""
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    
    EMBEDDING_DIM: int = 384
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_SEMANTIC: int = 8
    TOP_K_KEYWORD: int = 8
    TOP_K_FINAL: int = 5
    SEMANTIC_WEIGHT: float = 0.7
    KEYWORD_WEIGHT: float = 0.3
    VECTOR_INDEX_DIR: str = "./storage/vector_indexes"
    EMBEDDING_BATCH_SIZE: int = 20

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()