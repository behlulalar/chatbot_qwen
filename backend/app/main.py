"""
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import chat, documents
from app.schemas.chat import HealthResponse
from app.database import engine, Base
from app.utils.logger import setup_logger

logger = setup_logger("main", "./logs/main.log")

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Mevzuat chatbot API - RAG-based Q&A system for university regulations"
)

# CORS middleware (for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api")
app.include_router(documents.router, prefix="/api")


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "message": "SUBU Mevzuat Chatbot API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint."""
    # Check vector store
    vector_store_status = "unknown"
    try:
        from app.rag import VectorStoreManager
        manager = VectorStoreManager()
        manager.create_or_load()
        stats = manager.get_collection_stats()
        if stats.get("document_count", 0) > 0:
            vector_store_status = "healthy"
        else:
            vector_store_status = "empty"
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
        vector_store_status = "unhealthy"
    
    # Check database
    database_status = "unknown"
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        database_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        database_status = "unhealthy"
    
    return HealthResponse(
        status="healthy" if vector_store_status == "healthy" and database_status == "healthy" else "degraded",
        version=settings.app_version,
        vector_store_status=vector_store_status,
        database_status=database_status
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
