"""
Main FastAPI application
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.limiter import limiter
from app.api import chat, documents, feedback, auth
from app.api.documents import chroma_debug
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

# Rate limiting (slowapi): 429 döner, limit aşılırsa
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware (for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include routers
app.include_router(chat.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

# ChromaDB teşhis (0 doküman sorunu) — hem /api/documents/chroma-debug hem bu yol
app.add_api_route("/api/chroma-debug", chroma_debug, methods=["GET"], tags=["debug"])


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
        from sqlalchemy import text
        from app.database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
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


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def api_health_check():
    return await health_check()


# Tek port: frontend build varsa SPA olarak serve et (/admin, / vb. index.html döner)
_frontend_build = Path(__file__).resolve().parent.parent.parent / "frontend" / "build"
if _frontend_build.exists() and (_frontend_build / "index.html").exists():
    app.mount("/static", StaticFiles(directory=str(_frontend_build / "static")), name="static")

    @app.get("/{full_path:path}", tags=["frontend"])
    async def serve_spa(full_path: str):
        """SPA fallback: /admin, / vb. tüm yollarda index.html döner."""
        return FileResponse(_frontend_build / "index.html")
else:
    @app.get("/", tags=["root"])
    async def root():
        return {"message": "SUBU Mevzuat Chatbot API", "version": settings.app_version, "docs": "/docs", "health": "/health"}


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=getattr(settings, "port", 8000),
        reload=settings.debug
    )
