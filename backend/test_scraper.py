"""
Test script for QDMS Scraper.

This script:
1. Tests link extraction from QDMS website
2. Downloads PDFs
3. Saves results to database

Usage:
    python test_scraper.py
"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.scraper import QDMSScraper, LinkTracker
from app.database import SessionLocal, init_db
from app.config import settings
import json


def test_link_extraction():
    """Test 1: Extract QDMS links without downloading."""
    print("=" * 60)
    print("TEST 1: Link Extraction")
    print("=" * 60)
    
    scraper = QDMSScraper(headless=True)
    links = scraper.extract_qdms_links()
    
    print(f"\n✅ Found {len(links)} QDMS links\n")
    
    if links:
        print("First 5 links:")
        for i, link in enumerate(links[:5], 1):
            print(f"{i}. {link['title']}")
            print(f"   URL: {link['url']}\n")
        
        # Save to JSON for inspection
        output_file = Path("./data/discovered_links.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(links, f, indent=2, ensure_ascii=False)
        print(f"💾 All links saved to: {output_file}")
    else:
        print("⚠️ No links found. Check if the website structure has changed.")
    
    return links


def test_download():
    """Test 2: Download first PDF as a test."""
    print("\n" + "=" * 60)
    print("TEST 2: PDF Download")
    print("=" * 60)
    
    scraper = QDMSScraper(headless=True)
    links = scraper.extract_qdms_links()
    
    if not links:
        print("⚠️ No links to download")
        return None
    
    # Download only first PDF for testing
    first_link = links[0]
    print(f"\nDownloading test PDF: {first_link['title']}")
    
    result = scraper.download_pdf(first_link['url'], first_link['title'])
    
    if result:
        print(f"✅ Downloaded successfully!")
        print(f"   File: {result['filename']}")
        print(f"   Size: {result['file_size']} bytes")
        print(f"   Hash: {result['file_hash'][:16]}...")
    else:
        print("❌ Download failed")
    
    return result


def test_full_workflow():
    """Test 3: Full workflow with database."""
    print("\n" + "=" * 60)
    print("TEST 3: Full Workflow (Scrape + Download + Database)")
    print("=" * 60)
    
    # Initialize database
    print("\n1. Initializing database...")
    try:
        init_db()
        print("✅ Database tables created")
    except Exception as e:
        print(f"⚠️ Database init warning: {e}")
    
    # Scrape and download
    print("\n2. Scraping and downloading PDFs...")
    scraper = QDMSScraper(headless=True)
    results = scraper.scrape_and_download_all()
    
    print(f"✅ Downloaded {len(results)} PDFs")
    
    # Save to database
    print("\n3. Saving to database...")
    db = SessionLocal()
    try:
        tracker = LinkTracker(db)
        stats = tracker.sync_documents(results)
        
        print(f"\n📊 Database Sync Stats:")
        print(f"   New documents: {stats['new']}")
        print(f"   Updated documents: {stats['updated']}")
        print(f"   Unchanged: {stats['unchanged']}")
        print(f"   Failed: {stats['failed']}")
        
        print("\n✅ Full workflow completed!")
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def main():
    """Main test runner."""
    print("\n" + "=" * 60)
    print("SUBU CHATBOT - SCRAPER TEST")
    print("=" * 60)
    print(f"\nTarget URL: {settings.qdms_url}")
    print(f"Download Directory: {settings.download_directory}\n")
    
    # Create directories
    Path(settings.download_directory).mkdir(parents=True, exist_ok=True)
    Path("./logs").mkdir(exist_ok=True)
    Path("./data").mkdir(exist_ok=True)
    
    print("Choose test to run:")
    print("1. Link Extraction Only (fast)")
    print("2. Download Single PDF (medium)")
    print("3. Full Workflow - All PDFs + Database (slow)")
    print("0. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        test_link_extraction()
    elif choice == "2":
        test_download()
    elif choice == "3":
        test_full_workflow()
    elif choice == "0":
        print("Exiting...")
        return
    else:
        print("Invalid choice. Running link extraction by default...")
        test_link_extraction()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
