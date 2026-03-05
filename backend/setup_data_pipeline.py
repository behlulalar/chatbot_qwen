#!/usr/bin/env python3
"""
Data Pipeline Setup Script

This script performs initial setup of the data pipeline:
1. Creates necessary directories
2. Scrapes PDFs from QDMS
3. Processes PDFs to JSON
4. Builds vector store
5. Initializes database

Usage:
    python setup_data_pipeline.py
    
    Or with options:
    python setup_data_pipeline.py --skip-scrape  # Skip scraping if PDFs already exist
    python setup_data_pipeline.py --rebuild      # Force rebuild vector store
"""
import sys
import argparse
from pathlib import Path
from typing import List, Dict
import time

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.database import init_db, SessionLocal
from app.scraper.qdms_scraper import QDMSScraper
from app.scraper.link_tracker import LinkTracker
from app.converter.pdf_processor import PDFProcessor
from app.rag.document_loader import DocumentLoader
from app.rag.chunker import MevzuatChunker
from app.rag.vector_store import VectorStoreManager
from app.utils.logger import setup_logger

logger = setup_logger("setup_pipeline", "./logs/setup_pipeline.log")


class DataPipelineSetup:
    """Setup and initialize the data pipeline."""
    
    def __init__(self, skip_scrape: bool = False, rebuild: bool = False):
        """
        Initialize pipeline setup.
        
        Args:
            skip_scrape: Skip scraping if PDFs already exist
            rebuild: Force rebuild vector store
        """
        self.skip_scrape = skip_scrape
        self.rebuild = rebuild
        
    def create_directories(self):
        """Create necessary directories."""
        logger.info("📁 Creating directories...")
        
        directories = [
            settings.download_directory,
            settings.json_directory,
            settings.archive_directory,
            settings.chroma_persist_directory,
            "./logs"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"  ✓ {directory}")
        
        print("✅ Directories created\n")
    
    def initialize_database(self):
        """Initialize database tables."""
        logger.info("🗄️  Initializing database...")
        
        try:
            init_db()
            logger.info("  ✓ Database tables created")
            print("✅ Database initialized\n")
            return True
        except Exception as e:
            logger.error(f"  ✗ Database initialization failed: {e}")
            print(f"❌ Database initialization failed: {e}\n")
            return False
    
    def scrape_pdfs(self) -> int:
        """Scrape PDFs from QDMS."""
        if self.skip_scrape:
            pdf_count = len(list(Path(settings.download_directory).glob("*.pdf")))
            logger.info(f"⏭️  Skipping scrape - {pdf_count} PDFs already exist")
            print(f"⏭️  Skipping scrape - {pdf_count} PDFs found\n")
            return pdf_count
        
        logger.info("🕷️  Scraping PDFs from QDMS...")
        print("🕷️  Scraping PDFs from QDMS (this may take a few minutes)...")
        
        try:
            scraper = QDMSScraper(headless=True)
            print("  → Extracting and downloading PDFs...")
            results = scraper.scrape_and_download_all()
            logger.info(f"  Found {len(results)} PDF links")
            print(f"  ✓ Downloaded {len(results)} PDFs")
            
            db = SessionLocal()
            try:
                tracker = LinkTracker(db)
                tracker.sync_documents(results)
            finally:
                db.close()
            
            logger.info(f"  ✓ Downloaded {len(results)} PDFs")
            print(f"  ✓ Downloaded {len(results)} PDFs")
            print("✅ Scraping complete\n")
            
            return len(results)
            
        except Exception as e:
            logger.error(f"  ✗ Scraping failed: {e}")
            print(f"❌ Scraping failed: {e}\n")
            return 0
    
    def process_pdfs(self) -> int:
        """Process PDFs to JSON."""
        logger.info("📄 Processing PDFs to JSON...")
        print("📄 Processing PDFs to JSON...")
        
        try:
            processor = PDFProcessor()
            db = SessionLocal()
            try:
                tracker = LinkTracker(db)
                documents = tracker.get_documents_to_process()
                logger.info(f"  Found {len(documents)} documents to process")

                if not documents:
                    print("  ⏭️  No documents to process\n")
                    return 0

                processed_count = 0
                failed_count = 0

                for i, doc in enumerate(documents, 1):
                    try:
                        print(f"  → Processing ({i}/{len(documents)}): {doc.title[:50]}...")

                        pdf_path = Path(doc.pdf_path) if doc.pdf_path else Path(settings.download_directory) / f"{doc.id}.pdf"
                        json_filename = pdf_path.stem + ".json"

                        result = processor.process_pdf(str(pdf_path), doc.title)
                        json_path = processor.save_json(result, json_filename)
                        page_count = result["statistics"]["total_pages"]

                        tracker.mark_as_processed(doc.id, str(json_path), page_count)
                        processed_count += 1
                        logger.info(f"  ✓ {doc.title}")
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"  ✗ Error processing {doc.title}: {e}")
            finally:
                db.close()

            print(f"  ✓ Processed: {processed_count}")
            print(f"  ✗ Failed: {failed_count}")
            print("✅ PDF processing complete\n")
            
            return processed_count
            
        except Exception as e:
            logger.error(f"  ✗ PDF processing failed: {e}")
            print(f"❌ PDF processing failed: {e}\n")
            return 0
    
    def build_vector_store(self) -> bool:
        """Build or update vector store."""
        logger.info("🔍 Building vector store...")
        print("🔍 Building vector store (this may take several minutes)...")
        
        try:
            # Check if rebuild needed
            chroma_path = Path(settings.chroma_persist_directory)
            
            if self.rebuild and chroma_path.exists():
                logger.info("  Rebuilding - clearing existing vector store...")
                print("  → Clearing existing vector store...")
                import shutil
                shutil.rmtree(chroma_path)
                chroma_path.mkdir(parents=True, exist_ok=True)
            
            # Load documents
            print("  → Loading documents...")
            loader = DocumentLoader(settings.json_directory)
            documents = loader.load_all()
            logger.info(f"  Loaded {len(documents)} documents")
            print(f"  ✓ Loaded {len(documents)} documents")
            
            # Chunk documents
            print("  → Chunking documents...")
            chunker = MevzuatChunker(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap
            )
            chunks = chunker.chunk_documents(documents)
            logger.info(f"  Created {len(chunks)} chunks")
            print(f"  ✓ Created {len(chunks)} chunks")
            
            # Create embeddings and store
            print("  → Creating embeddings and storing (this takes time)...")
            vector_store = VectorStoreManager()
            vector_store.initialize_embeddings()
            vector_store.create_or_load()
            
            # Add in batches
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                vector_store.add_documents(batch)
                progress = min(i + batch_size, len(chunks))
                print(f"    Progress: {progress}/{len(chunks)} chunks")
                logger.info(f"  Added batch {i//batch_size + 1}: {progress}/{len(chunks)}")
            
            # Verify
            stats = vector_store.get_collection_stats()
            logger.info(f"  ✓ Vector store built: {stats}")
            print(f"  ✓ Vector store ready: {stats.get('document_count', 0)} documents")
            print("✅ Vector store complete\n")
            
            return True
            
        except Exception as e:
            logger.error(f"  ✗ Vector store build failed: {e}", exc_info=True)
            print(f"❌ Vector store build failed: {e}\n")
            return False
    
    def run_full_setup(self):
        """Run full setup pipeline."""
        print("=" * 60)
        print("🚀 SUBU Chatbot - Data Pipeline Setup")
        print("=" * 60)
        print()
        
        start_time = time.time()
        
        # Step 1: Create directories
        self.create_directories()
        
        # Step 2: Initialize database
        if not self.initialize_database():
            print("⚠️  Database initialization failed - continuing anyway...")
        
        # Step 3: Scrape PDFs
        pdf_count = self.scrape_pdfs()
        if pdf_count == 0:
            print("⚠️  No PDFs downloaded - check your internet connection or QDMS site")
            return False
        
        # Step 4: Process PDFs
        processed = self.process_pdfs()
        if processed == 0:
            print("⚠️  No PDFs processed - check for errors above")
            return False
        
        # Step 5: Build vector store
        if not self.build_vector_store():
            print("⚠️  Vector store build failed - check for errors above")
            return False
        
        # Summary
        elapsed = time.time() - start_time
        print("=" * 60)
        print("🎉 Setup Complete!")
        print("=" * 60)
        print(f"⏱️  Total time: {elapsed:.1f} seconds")
        print(f"📊 Statistics:")
        print(f"   - PDFs scraped: {pdf_count}")
        print(f"   - PDFs processed: {processed}")
        print(f"\n✅ Your chatbot is ready to use!")
        print(f"   Run: python run_server.py")
        print("=" * 60)
        
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup SUBU Chatbot data pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip scraping if PDFs already exist"
    )
    
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force rebuild vector store from scratch"
    )
    
    args = parser.parse_args()
    
    # Run setup
    setup = DataPipelineSetup(
        skip_scrape=args.skip_scrape,
        rebuild=args.rebuild
    )
    
    success = setup.run_full_setup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
