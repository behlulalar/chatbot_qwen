"""
Quick test to reprocess a single PDF after parser updates.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.converter import PDFProcessor

# The problematic PDF
pdf_path = "data/raw_pdfs/ACCEPTANCE AND IMPLEMENTATION DIRECTIVE REGARDING VISITING LECTURERS AND RESEARCHERS.pdf"
title = "ACCEPTANCE AND IMPLEMENTATION DIRECTIVE REGARDING VISITING LECTURERS AND RESEARCHERS"

print("=" * 60)
print("Reprocessing PDF with Updated Parser")
print("=" * 60)

processor = PDFProcessor()

try:
    print(f"\nProcessing: {title}")
    result = processor.process_pdf(pdf_path, title)
    
    print(f"\n✅ Processing successful!")
    print(f"\nStatistics:")
    print(f"  Total Articles: {result['statistics']['total_articles']}")
    print(f"  Total Pages: {result['statistics']['total_pages']}")
    
    print(f"\nArticles Found:")
    for i, article in enumerate(result['articles'], 1):
        print(f"\n  {i}. Article {article['article_number']}: {article['article_title'][:60]}...")
        print(f"     Paragraphs: {len(article['paragraphs'])}")
        
        # Show first paragraph
        if article['paragraphs']:
            para = article['paragraphs'][0]
            print(f"     First paragraph content: {para['content'][:100]}...")
            if para['sub_items']:
                print(f"     Sub-items in first paragraph: {len(para['sub_items'])}")
                for sub in para['sub_items'][:3]:
                    print(f"       - {sub['sub_item_id']}) {sub['content'][:60]}...")
    
    # Save updated JSON
    json_path = processor.save_json(result)
    print(f"\n💾 Updated JSON saved to: {json_path}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
