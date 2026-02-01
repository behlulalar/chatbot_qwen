"""
Link Tracker - Manages document tracking and change detection.

This module:
1. Stores QDMS links in database
2. Detects changes by comparing hashes
3. Manages document lifecycle (new, updated, archived)
"""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus
from app.utils.logger import setup_logger

logger = setup_logger("link_tracker", "./logs/link_tracker.log")


class LinkTracker:
    """
    Tracks QDMS documents and detects changes.
    
    Usage:
        tracker = LinkTracker(db_session)
        tracker.sync_documents(scraped_results)
    """
    
    def __init__(self, db: Session):
        """
        Initialize tracker with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def sync_documents(self, scraped_results: List[Dict]) -> Dict[str, int]:
        """
        Sync scraped documents with database.
        
        This method:
        - Adds new documents
        - Updates existing documents if hash changed
        - Marks unchanged documents as checked
        
        Args:
            scraped_results: List of download results from scraper
        
        Returns:
            Statistics dictionary with counts
        """
        stats = {
            "new": 0,
            "updated": 0,
            "unchanged": 0,
            "failed": 0
        }
        
        logger.info(f"Syncing {len(scraped_results)} documents with database")
        
        for result in scraped_results:
            try:
                # Check if document exists
                existing_doc = self.db.query(Document).filter(
                    Document.qdms_link == result['url']
                ).first()
                
                if existing_doc:
                    # Document exists - check for changes
                    if existing_doc.pdf_hash != result['file_hash']:
                        # Hash changed - document was updated
                        logger.info(f"Document updated: {result['title']}")
                        self._update_document(existing_doc, result)
                        stats["updated"] += 1
                    else:
                        # No changes
                        existing_doc.last_checked_at = datetime.now()
                        stats["unchanged"] += 1
                else:
                    # New document
                    logger.info(f"New document: {result['title']}")
                    self._create_document(result)
                    stats["new"] += 1
                
                self.db.commit()
            
            except Exception as e:
                logger.error(f"Error syncing document {result.get('title')}: {e}", exc_info=True)
                self.db.rollback()
                stats["failed"] += 1
        
        logger.info(f"Sync complete: {stats}")
        return stats
    
    def _create_document(self, result: Dict) -> Document:
        """Create new document record."""
        doc = Document(
            title=result['title'],
            qdms_link=result['url'],
            pdf_hash=result['file_hash'],
            pdf_path=result['filepath'],
            file_size=result['file_size'],
            status=DocumentStatus.DOWNLOADED,
            last_checked_at=datetime.now()
        )
        self.db.add(doc)
        return doc
    
    def _update_document(self, doc: Document, result: Dict):
        """Update existing document with new data."""
        # Archive old version info
        logger.info(f"Old hash: {doc.pdf_hash}, New hash: {result['file_hash']}")
        
        # Update with new data
        doc.pdf_hash = result['file_hash']
        doc.pdf_path = result['filepath']
        doc.file_size = result['file_size']
        doc.status = DocumentStatus.DOWNLOADED
        doc.last_checked_at = datetime.now()
        doc.updated_at = datetime.now()
        
        # Clear old processing data (will be reprocessed)
        doc.json_path = None
        doc.processed_at = None
    
    def get_documents_to_process(self) -> List[Document]:
        """
        Get documents that need processing.
        
        Returns:
            List of documents with DOWNLOADED status
        """
        docs = self.db.query(Document).filter(
            Document.status == DocumentStatus.DOWNLOADED
        ).all()
        
        logger.info(f"Found {len(docs)} documents to process")
        return docs
    
    def mark_as_processed(self, doc_id: int, json_path: str, page_count: int):
        """
        Mark document as successfully processed.
        
        Args:
            doc_id: Document ID
            json_path: Path to generated JSON file
            page_count: Number of pages in PDF
        """
        doc = self.db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.status = DocumentStatus.PROCESSED
            doc.json_path = json_path
            doc.page_count = page_count
            doc.processed_at = datetime.now()
            self.db.commit()
            logger.info(f"Marked document {doc_id} as processed")
    
    def mark_as_failed(self, doc_id: int, error_message: str):
        """
        Mark document as failed processing.
        
        Args:
            doc_id: Document ID
            error_message: Error description
        """
        doc = self.db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.status = DocumentStatus.FAILED
            doc.error_message = error_message
            self.db.commit()
            logger.error(f"Marked document {doc_id} as failed: {error_message}")
