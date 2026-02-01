"""
Test script for PDF Processor.

This script:
1. Tests PDF text extraction
2. Tests article parsing
3. Processes all downloaded PDFs
4. Updates database

Usage:
    python test_pdf_processor.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.converter import PDFProcessor
from app.database import SessionLocal
from app.models import Document, DocumentStatus
from app.scraper import LinkTracker
import json


def test_single_pdf():
    """Test 1: Process a single PDF."""
    print("=" * 60)
    print("TEST 1: Single PDF Processing")
    print("=" * 60)
    
    # Get first downloaded PDF from database
    db = SessionLocal()
    doc = db.query(Document).filter(
        Document.status == DocumentStatus.DOWNLOADED
    ).first()
    
    if not doc:
        print("⚠️ No downloaded PDFs found in database")
        db.close()
        return None
    
    print(f"\nProcessing: {doc.title}")
    print(f"File: {doc.pdf_path}")
    
    processor = PDFProcessor()
    
    try:
        # Process PDF
        result = processor.process_pdf(doc.pdf_path, doc.title)
        
        # Display results
        print(f"\n✅ Processing successful!")
        print(f"\nMetadata:")
        print(f"  Title: {result['metadata']['title']}")
        print(f"  Pages: {result['metadata']['page_count']}")
        print(f"  Filename: {result['metadata']['filename']}")
        
        print(f"\nStatistics:")
        print(f"  Articles found: {result['statistics']['total_articles']}")
        print(f"  Total characters: {result['statistics']['total_characters']}")
        
        if result['articles']:
            print(f"\nFirst 3 articles:")
            for i, article in enumerate(result['articles'][:3], 1):
                print(f"\n  {i}. Madde {article['article_number']}: {article['article_title']}")
                print(f"     Paragraphs: {len(article['paragraphs'])}")
                print(f"     Content preview: {article['content'][:100]}...")
        
        # Save JSON
        json_path = processor.save_json(result)
        print(f"\n💾 JSON saved to: {json_path}")
        
        db.close()
        return result
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.close()
        return None


def test_batch_processing():
    """Test 2: Process all PDFs in batch."""
    print("\n" + "=" * 60)
    print("TEST 2: Batch Processing (All PDFs)")
    print("=" * 60)
    
    db = SessionLocal()
    
    # Get all downloaded PDFs
    docs = db.query(Document).filter(
        Document.status == DocumentStatus.DOWNLOADED
    ).all()
    
    if not docs:
        print("⚠️ No PDFs to process")
        db.close()
        return
    
    print(f"\nFound {len(docs)} PDFs to process")
    
    # Prepare batch
    pdf_paths = [doc.pdf_path for doc in docs]
    titles = [doc.title for doc in docs]
    
    # Process batch
    processor = PDFProcessor()
    results = processor.process_batch(pdf_paths, titles)
    
    # Update database
    print("\nUpdating database...")
    tracker = LinkTracker(db)
    
    success_count = 0
    failed_count = 0
    
    for doc, result in zip(docs, results):
        if result["status"] == "success":
            tracker.mark_as_processed(
                doc.id,
                result["json_path"],
                result["page_count"]
            )
            success_count += 1
        else:
            tracker.mark_as_failed(doc.id, result.get("error", "Unknown error"))
            failed_count += 1
    
    # Display summary
    print(f"\n{'=' * 60}")
    print("BATCH PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Total PDFs: {len(docs)}")
    print(f"✅ Successfully processed: {success_count}")
    print(f"❌ Failed: {failed_count}")
    
    if success_count > 0:
        total_articles = sum(r.get("article_count", 0) for r in results if r["status"] == "success")
        print(f"📊 Total articles extracted: {total_articles}")
    
    db.close()
    print("\n✅ Database updated!")


def inspect_json_sample():
    """Test 3: Inspect a sample JSON output."""
    print("\n" + "=" * 60)
    print("TEST 3: Inspect JSON Sample")
    print("=" * 60)
    
    json_dir = Path("./data/processed_json")
    json_files = list(json_dir.glob("*.json"))
    
    if not json_files:
        print("⚠️ No JSON files found")
        return
    
    # Load first JSON
    sample_file = json_files[0]
    print(f"\nLoading: {sample_file.name}")
    
    with open(sample_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n📄 Document: {data['metadata']['title']}")
    print(f"   Pages: {data['metadata']['page_count']}")
    print(f"   Articles: {data['statistics']['total_articles']}")
    
    if data['articles']:
        article = data['articles'][0]
        print(f"\n📋 Sample Article (Madde {article['article_number']}):")
        print(f"   Title: {article['article_title']}")
        print(f"   Paragraphs: {len(article['paragraphs'])}")
        
        if article['paragraphs']:
            para = article['paragraphs'][0]
            print(f"\n   First Paragraph ({para['paragraph_number']}):")
            print(f"   Content: {para['content'][:200]}...")
            if para['sub_items']:
                print(f"   Sub-items: {len(para['sub_items'])}")


def main():
    """Main test runner."""
    print("\n" + "=" * 60)
    print("SUBU CHATBOT - PDF PROCESSOR TEST")
    print("=" * 60)
    
    print("\nChoose test to run:")
    print("1. Process Single PDF (fast)")
    print("2. Process All PDFs - Batch (slow)")
    print("3. Inspect JSON Sample")
    print("4. Full Workflow (Single → Batch → Inspect)")
    print("0. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        test_single_pdf()
    elif choice == "2":
        test_batch_processing()
    elif choice == "3":
        inspect_json_sample()
    elif choice == "4":
        print("\n🚀 Running full workflow...\n")
        test_single_pdf()
        
        proceed = input("\n\nProceed with batch processing? (y/n): ").strip().lower()
        if proceed == 'y':
            test_batch_processing()
            inspect_json_sample()
    elif choice == "0":
        print("Exiting...")
        return
    else:
        print("Invalid choice. Running single PDF test...")
        test_single_pdf()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
