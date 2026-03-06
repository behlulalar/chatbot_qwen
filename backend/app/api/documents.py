"""
Documents API endpoints
"""
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import resolve_json_directory, resolve_chroma_directory
from app.database import get_db
from app.models import Document, DocumentStatus
from app.schemas.chat import DocumentInfo, DocumentListResponse
from app.utils.logger import setup_logger

logger = setup_logger("api_documents", "./logs/api_documents.log")

router = APIRouter(prefix="/documents", tags=["documents"])


def _chroma_count_from_path(chroma_path: str) -> Optional[int]:
    """ChromaDB klasöründen kayıt sayısını döner; hata olursa None."""
    try:
        import chromadb
        path = Path(chroma_path)
        if not path.exists():
            return None
        client = chromadb.PersistentClient(path=chroma_path)
        for c in client.list_collections():
            n = c.count()
            if n > 0:
                return n
    except Exception as e:
        logger.debug(f"Chroma count from {chroma_path!r} failed: {e}")
    return None


def _get_document_count_fallback():
    """
    Get document count when DB is empty.
    JSON file count represents actual documents; ChromaDB count is chunks (much higher).
    """
    # 1) JSON dosya sayısı (gerçek doküman sayısı)
    for base in [
        resolve_json_directory(),
        Path.home() / "behlul" / "backend" / "data" / "processed_json",
        Path("/home/behlulalar/behlul/backend/data/processed_json"),
    ]:
        try:
            if base.exists():
                n = len(list(base.glob("*.json")))
                if n > 0:
                    return n
        except Exception as e:
            logger.debug(f"JSON dir count from {base!s} failed: {e}")

    # 2) ChromaDB sayımı (son çare, chunk sayısı döner)
    chroma_dir = resolve_chroma_directory()
    n = _chroma_count_from_path(str(chroma_dir))
    if n is not None and n > 0:
        return n

    for extra in [
        Path.home() / "behlul" / "backend" / "data" / "chroma_db",
        Path("/home/behlulalar/behlul/backend/data/chroma_db"),
    ]:
        if extra.exists():
            n = _chroma_count_from_path(str(extra))
            if n is not None and n > 0:
                return n

    return 0


def _chroma_count_and_error(chroma_path: str):
    """ChromaDB sayısı ve varsa hata mesajı döner."""
    try:
        import chromadb
        path = Path(chroma_path)
        if not path.exists():
            return None, f"path does not exist: {chroma_path}"
        client = chromadb.PersistentClient(path=chroma_path)
        colls = client.list_collections()
        for c in colls:
            n = c.count()
            if n > 0:
                return n, None
        return 0, "no collection with count > 0"
    except Exception as e:
        return None, str(e)


@router.get("/chroma-debug")
async def chroma_debug():
    """
    ChromaDB path ve sayımını döner; "0 doküman" sorununda kullanılır.
    """
    chroma_dir = resolve_chroma_directory()
    result = {
        "resolved_path": str(chroma_dir),
        "path_exists": chroma_dir.exists(),
        "count": None,
        "error": None,
    }
    n, err = _chroma_count_and_error(str(chroma_dir))
    if err:
        result["error"] = err
    if n is not None and n > 0:
        result["count"] = n
        return result
    for extra in [
        Path.home() / "behlul" / "backend" / "data" / "chroma_db",
        Path("/home/behlulalar/behlul/backend/data/chroma_db"),
    ]:
        if extra.exists():
            n, err = _chroma_count_and_error(str(extra))
            if err:
                result["error_fallback"] = result.get("error_fallback") or {}
                result["error_fallback"][str(extra)] = err
            if n is not None and n > 0:
                result["count"] = n
                result["used_fallback_path"] = str(extra)
                result["error"] = None
                return result
    return result


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
