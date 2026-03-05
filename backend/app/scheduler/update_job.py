"""
Update Scheduler - Periodically checks for document updates.

Runs every 24 hours to:
1. Scrape QDMS website
2. Check for new/updated PDFs
3. Process changed documents
4. Update vector store
"""
from datetime import datetime
from pathlib import Path
from typing import Optional, cast, List
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.scraper import QDMSScraper, LinkTracker
from app.converter import PDFProcessor
from app.rag import DocumentLoader, MevzuatChunker, VectorStoreManager
from app.database import SessionLocal
from app.models import Document, DocumentStatus
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("scheduler", "./logs/scheduler.log")


class UpdateScheduler:
    """
    Manages scheduled document updates.
    
    Features:
    - Periodic scraping
    - Change detection
    - Automatic reprocessing
    - Vector store updates
    
    Usage:
        scheduler = UpdateScheduler()
        scheduler.start()
    """
    
    def __init__(self, interval_hours: Optional[int] = None):
        """
        Initialize scheduler.
        
        Args:
            interval_hours: Check interval in hours (defaults to settings)
        """
        self.interval_hours = interval_hours or settings.update_interval
        self.scheduler = BackgroundScheduler()
        
        logger.info(f"UpdateScheduler initialized: interval={self.interval_hours}h")
    
    def update_job(self):
        """
        Main update job - runs periodically.
        
        This job:
        1. Scrapes QDMS website
        2. Downloads new/updated PDFs
        3. Processes them to JSON
        4. Updates vector store
        """
        job_start = datetime.now()
        logger.info("=" * 80)
        logger.info(f"UPDATE JOB STARTED: {job_start.isoformat()}")
        logger.info("=" * 80)
        
        db = SessionLocal()
        
        try:
            # Step 1: Scrape and download
            logger.info("Step 1: Scraping QDMS website...")
            scraper = QDMSScraper(headless=True)
            results = scraper.scrape_and_download_all()
            
            logger.info(f"Scraping complete: {len(results)} PDFs")
            
            # Step 2: Sync with database
            logger.info("Step 2: Syncing with database...")
            tracker = LinkTracker(db)
            sync_stats = tracker.sync_documents(results)
            
            logger.info(f"Sync stats: {sync_stats}")
            
            # Step 3: Process new/updated documents
            new_or_updated = sync_stats['new'] + sync_stats['updated']
            
            if new_or_updated > 0:
                logger.info(f"Step 3: Processing {new_or_updated} new/updated documents...")
                
                # Get documents to process (only those with pdf_path)
                docs_to_process = [d for d in tracker.get_documents_to_process() if d.pdf_path]
                if not docs_to_process:
                    logger.info("No documents with valid pdf_path to process")
                else:
                    processor = PDFProcessor()
                    pdf_paths = cast(List[str], [d.pdf_path for d in docs_to_process])
                    titles = cast(List[Optional[str]], [d.title for d in docs_to_process])
                    process_results = processor.process_batch(pdf_paths, titles)

                    # Update database
                    for doc, result in zip(docs_to_process, process_results):
                        if result["status"] == "success":
                            tracker.mark_as_processed(
                                doc.id,
                                result["json_path"],
                                result["page_count"]
                            )
                        else:
                            tracker.mark_as_failed(doc.id, result.get("error", "Unknown error"))

                    logger.info(f"Processing complete: {len([r for r in process_results if r['status'] == 'success'])} successful")

                    # Step 4: Update vector store
                    logger.info("Step 4: Updating vector store...")
                    self._update_vector_store(docs_to_process)
                
            else:
                logger.info("No new or updated documents. Skipping processing.")
            
            # Job summary
            job_end = datetime.now()
            duration = (job_end - job_start).total_seconds()
            
            logger.info("=" * 80)
            logger.info(f"UPDATE JOB COMPLETED: {job_end.isoformat()}")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"Summary: {sync_stats['new']} new, {sync_stats['updated']} updated, {sync_stats['unchanged']} unchanged")
            logger.info("=" * 80)
        
        except Exception as e:
            logger.error(f"Error in update job: {e}", exc_info=True)
        
        finally:
            db.close()
    
    def _update_vector_store(self, updated_docs: list):
        """
        Update vector store with new/changed documents.
        
        Args:
            updated_docs: List of Document objects that were updated
        """
        try:
            # Load updated JSONs
            loader = DocumentLoader()
            documents = []
            
            for doc in updated_docs:
                if doc.json_path:
                    try:
                        docs = loader.load_single(Path(doc.json_path))
                        documents.extend(docs)
                    except Exception as e:
                        logger.error(f"Error loading {doc.json_path}: {e}")
            
            if not documents:
                logger.info("No documents to add to vector store")
                return
            
            # Chunk documents
            logger.info(f"Chunking {len(documents)} documents...")
            chunker = MevzuatChunker()
            chunks = chunker.chunk_documents(documents)
            
            # Add to vector store
            logger.info(f"Adding {len(chunks)} chunks to vector store...")
            vector_manager = VectorStoreManager()
            vector_manager.create_or_load()
            vector_manager.add_documents(chunks)
            
            logger.info(f"Vector store updated successfully: {len(chunks)} chunks added")
        
        except Exception as e:
            logger.error(f"Error updating vector store: {e}", exc_info=True)
    
    def start(self):
        """Start the scheduler."""
        # Add job
        self.scheduler.add_job(
            func=self.update_job,
            trigger=IntervalTrigger(hours=self.interval_hours),
            id='update_mevzuat',
            name='Update Mevzuat Documents',
            replace_existing=True
        )
        
        # Start scheduler
        self.scheduler.start()
        
        logger.info(f"Scheduler started: will run every {self.interval_hours} hours")
        logger.info(f"Next run: {self.scheduler.get_jobs()[0].next_run_time}")
    
    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    def run_now(self):
        """Run update job immediately (for testing)."""
        logger.info("Running update job immediately...")
        self.update_job()
