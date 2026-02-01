"""
Documents API endpoints
"""
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Document, DocumentStatus
from app.schemas.chat import DocumentInfo, DocumentListResponse
from app.utils.logger import setup_logger

logger = setup_logger("api_documents", "./logs/api_documents.log")

router = APIRouter(prefix="/documents", tags=["documents"])


def _resolve_json_directory():
    """Resolve JSON directory path: try cwd (gunicorn), then backend root."""
    from app.config import settings
    base = Path(settings.json_directory)
    if base.is_absolute():
        return base
    # Try current working directory first (e.g. gunicorn started from backend/)
    cwd_base = (Path.cwd() / settings.json_directory).resolve()
    if cwd_base.exists():
        return cwd_base
    # Fallback: backend root (app/api/documents.py -> app -> backend)
    backend_root = Path(__file__).resolve().parent.parent.parent
    return (backend_root / settings.json_directory).resolve()


def _get_document_count_fallback():
    """
    Get document count when DB is empty: try vector store, then JSON directory.
    Uses absolute paths so it works regardless of process cwd.
    """
    # 1) Vector store count (chunk count; if > 0 we use it as "documents" indicator)
    try:
        from app.rag import VectorStoreManager
        manager = VectorStoreManager()
        manager.create_or_load()
        stats = manager.get_collection_stats()
        count = stats.get("document_count")
        if count is not None and count > 0:
            return count
    except Exception as e:
        logger.warning(f"Vector store count fallback failed: {e}")
    # 2) JSON file count
    try:
        base = _resolve_json_directory()
        if base.exists():
            n = len(list(base.glob("*.json")))
            if n > 0:
                return n
    except Exception as e:
        logger.warning(f"JSON dir count fallback failed: {e}")
    return 0


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all documents.
    
    Args:
        status: Filter by status (processed, downloaded, failed)
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
    
    Returns:
        List of documents with metadata
    """
    try:
        query = db.query(Document)
        
        # Filter by status if provided
        if status:
            try:
                status_enum = DocumentStatus(status.lower())
                query = query.filter(Document.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Must be one of: {[s.value for s in DocumentStatus]}"
                )
        
        # Get total count
        total = query.count()
        
        # Fallback: when DB is empty (e.g. manual PDF/JSON upload), use vector store or JSON count
        if total == 0:
            total = _get_document_count_fallback()
        
        # Get paginated results
        documents = query.offset(skip).limit(limit).all()
        
        # Convert to response model
        doc_infos = []
        for doc in documents:
            # Try to get article count from JSON if processed
            article_count = None
            if doc.json_path and doc.status == DocumentStatus.PROCESSED:
                try:
                    import json
                    from pathlib import Path
                    json_path = Path(doc.json_path)
                    if json_path.exists():
                        with open(json_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            article_count = data['statistics']['total_articles']
                except Exception:
                    pass
            
            doc_infos.append(
                DocumentInfo(
                    id=doc.id,
                    title=doc.title,
                    status=doc.status.value,
                    page_count=doc.page_count,
                    article_count=article_count,
                    processed_at=doc.processed_at.isoformat() if doc.processed_at else None
                )
            )
        
        logger.info(f"Retrieved {len(doc_infos)} documents (total: {total})")
        
        return DocumentListResponse(
            total=total,
            documents=doc_infos
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}")
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """
    Get document details by ID.
    
    Args:
        document_id: Document ID
        db: Database session
    
    Returns:
        Document details
    """
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get JSON data if available
        json_data = None
        if doc.json_path:
            try:
                import json
                from pathlib import Path
                json_path = Path(doc.json_path)
                if json_path.exists():
                    with open(json_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
            except Exception as e:
                logger.error(f"Error reading JSON: {e}")
        
        return {
            "id": doc.id,
            "title": doc.title,
            "status": doc.status.value,
            "pdf_path": doc.pdf_path,
            "json_path": doc.json_path,
            "page_count": doc.page_count,
            "file_size": doc.file_size,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
            "json_data": json_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
