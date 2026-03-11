"""
Configuration management using Pydantic Settings.
Loads environment variables from .env file.
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = Field(default="SUBU Mevzuat Chatbot", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=True, alias="DEBUG")
    port: int = Field(default=8000, alias="PORT")
    
    # Database
    database_url: str = Field(..., alias="DATABASE_URL")
    
    # OpenAI / LLM
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")  # Ollama için herhangi bir değer yeterli
    llm_base_url: Optional[str] = Field(default=None, alias="LLM_BASE_URL")  # Ollama: http://localhost:11434/v1
    
    # Directories
    chroma_persist_directory: str = Field(default="./data/chroma_db", alias="CHROMA_PERSIST_DIRECTORY")
    download_directory: str = Field(default="./data/raw_pdfs", alias="DOWNLOAD_DIRECTORY")
    archive_directory: str = Field(default="./data/archive", alias="ARCHIVE_DIRECTORY")
    json_directory: str = Field(default="./data/processed_json", alias="JSON_DIRECTORY")
    
    # Scraper
    qdms_url: str = Field(default="https://hukuk.subu.edu.tr/yonergeler", alias="QDMS_URL")
    qdms_yonetmelikler_url: str = Field(default="https://hukuk.subu.edu.tr/yonetmelikler-0", alias="QDMS_YONETMELIKLER_URL")
    update_interval: int = Field(default=24, alias="UPDATE_INTERVAL")
    
    # LLM
    model_name: str = Field(default="gpt-4o-mini", alias="MODEL_NAME")
    temperature: float = Field(default=0.1, alias="TEMPERATURE")
    max_tokens: int = Field(default=1200, alias="MAX_TOKENS")
    
    # Embeddings
    embedding_model: str = Field(default="bge-m3", alias="EMBEDDING_MODEL")
    chunk_size: int = Field(default=800, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=150, alias="CHUNK_OVERLAP")
    
    # Cache Settings (Performance Optimization)
    redis_enabled: bool = Field(default=False, alias="REDIS_ENABLED")
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    query_cache_ttl: int = Field(default=3600, alias="QUERY_CACHE_TTL")
    response_cache_ttl: int = Field(default=1800, alias="RESPONSE_CACHE_TTL")
    
    # Admin Auth (env: ADMIN_SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD)
    admin_secret_key: str = Field(default="change-me-in-production", alias="ADMIN_SECRET_KEY")
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="admin123", alias="ADMIN_PASSWORD")

    # CORS Settings
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:80",
        alias="CORS_ORIGINS"
    )
    
    def get_cors_origins(self) -> list:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance (loads DATABASE_URL, OPENAI_API_KEY from .env)
settings = Settings()  # type: ignore[call-arg]


def resolve_json_directory(override: Optional[str] = None) -> Path:
    """
    JSON klasörünü cwd'den bağımsız bulur.
    Zaten mutlak path verilmişse olduğu gibi döner.
    """
    base = override or settings.json_directory
    p = Path(base)
    if p.is_absolute():
        return p.resolve()
    rel = base.strip("./") or "data/processed_json"
    backend_root = Path(__file__).resolve().parent.parent
    candidates = [
        backend_root / rel,
        Path.cwd() / rel,
        Path.cwd() / "backend" / rel,
    ]
    for c in candidates:
        if c.exists():
            return c.resolve()
    return candidates[0].resolve()


def resolve_chroma_directory(override: Optional[str] = None) -> Path:
    """
    ChromaDB klasörünü cwd'den bağımsız bulur.
    """
    base = override or settings.chroma_persist_directory
    p = Path(base)
    if p.is_absolute():
        return p.resolve()
    rel = base.strip("./") or "data/chroma_db"
    backend_root = Path(__file__).resolve().parent.parent
    candidates = [
        backend_root / rel,
        Path.cwd() / rel,
        Path.cwd() / "backend" / rel,
    ]
    for c in candidates:
        if c.exists():
            return c.resolve()
    return (backend_root / rel).resolve()
