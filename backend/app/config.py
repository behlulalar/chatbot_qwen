"""
Configuration management using Pydantic Settings.
Loads environment variables from .env file.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = Field(default="SUBU Mevzuat Chatbot", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=True, alias="DEBUG")
    
    # Database
    database_url: str = Field(..., alias="DATABASE_URL")
    
    # OpenAI
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    
    # Directories
    chroma_persist_directory: str = Field(default="./data/chroma_db", alias="CHROMA_PERSIST_DIRECTORY")
    download_directory: str = Field(default="./data/raw_pdfs", alias="DOWNLOAD_DIRECTORY")
    archive_directory: str = Field(default="./data/archive", alias="ARCHIVE_DIRECTORY")
    json_directory: str = Field(default="./data/processed_json", alias="JSON_DIRECTORY")
    
    # Scraper
    qdms_url: str = Field(default="https://hukuk.subu.edu.tr/yonergeler", alias="QDMS_URL")
    update_interval: int = Field(default=24, alias="UPDATE_INTERVAL")
    
    # LLM
    model_name: str = Field(default="gpt-3.5-turbo", alias="MODEL_NAME")
    temperature: float = Field(default=0.1, alias="TEMPERATURE")
    max_tokens: int = Field(default=1000, alias="MAX_TOKENS")
    
    # Embeddings
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    chunk_size: int = Field(default=800, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=150, alias="CHUNK_OVERLAP")
    
    # Cache Settings (Performance Optimization)
    redis_enabled: bool = Field(default=False, alias="REDIS_ENABLED")
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    query_cache_ttl: int = Field(default=3600, alias="QUERY_CACHE_TTL")
    response_cache_ttl: int = Field(default=1800, alias="RESPONSE_CACHE_TTL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
