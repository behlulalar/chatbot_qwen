"""
Example usage of the chatbot components.

This file demonstrates how to use different parts of the system
programmatically (without API).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# ============================================================================
# Example 1: Direct RAG Query (No API)
# ============================================================================
def example_direct_rag():
    """Use chatbot directly without API."""
    print("Example 1: Direct RAG Usage")
    print("=" * 80)
    
    from app.llm import ResponseGenerator
    
    # Initialize
    generator = ResponseGenerator()
    
    # Ask question
    question = "Akademik personele ödül nasıl verilir?"
    response = generator.generate_response(question)
    
    print(f"\nSoru: {question}")
    print(f"\nCevap: {response['answer']}")
    print(f"\nKaynak sayısı: {len(response['sources'])}")
    print(f"Maliyet: ${response['metadata']['cost']:.4f}")


# ============================================================================
# Example 2: Custom Vector Search
# ============================================================================
def example_vector_search():
    """Search vector store directly."""
    print("\nExample 2: Vector Search")
    print("=" * 80)
    
    from app.rag import VectorStoreManager
    
    # Initialize
    manager = VectorStoreManager()
    manager.create_or_load()
    
    # Search
    query = "staj süresi"
    results = manager.search_with_score(query, k=3)
    
    print(f"\nArama: '{query}'")
    print(f"\nSonuçlar:")
    for i, (doc, score) in enumerate(results, 1):
        print(f"\n{i}. Score: {score:.3f}")
        print(f"   Kaynak: {doc.metadata['title'][:50]}...")
        print(f"   Madde: {doc.metadata['article_number']}")
        print(f"   İçerik: {doc.page_content[:100]}...")


# ============================================================================
# Example 3: Process Single PDF
# ============================================================================
def example_process_pdf():
    """Process a single PDF file."""
    print("\nExample 3: PDF Processing")
    print("=" * 80)
    
    from app.converter import PDFProcessor
    
    processor = PDFProcessor()
    
    # Get first PDF
    pdf_path = "data/raw_pdfs/AKADEMİK VE İDARİ PERSONEL ÖDÜL YÖNERGESİ.pdf"
    
    print(f"\nProcessing: {pdf_path}")
    
    result = processor.process_pdf(pdf_path, "Test Yönergesi")
    
    print(f"\nSayfa sayısı: {result['statistics']['total_pages']}")
    print(f"Madde sayısı: {result['statistics']['total_articles']}")
    print(f"\nİlk 3 madde:")
    for i, article in enumerate(result['articles'][:3], 1):
        print(f"  {i}. Madde {article['article_number']}: {article['article_title'][:50]}...")


# ============================================================================
# Example 4: Database Query
# ============================================================================
def example_database_query():
    """Query database directly."""
    print("\nExample 4: Database Query")
    print("=" * 80)
    
    from app.database import SessionLocal
    from app.models import Document, DocumentStatus
    
    db = SessionLocal()
    
    # Get all processed documents
    docs = db.query(Document).filter(
        Document.status == DocumentStatus.PROCESSED
    ).all()
    
    print(f"\nİşlenmiş doküman sayısı: {len(docs)}")
    print(f"\nİlk 5 doküman:")
    for i, doc in enumerate(docs[:5], 1):
        print(f"  {i}. {doc.title[:50]}...")
        print(f"     Sayfa: {doc.page_count}, Madde: ?")
    
    db.close()


# ============================================================================
# Example 5: Custom Prompt
# ============================================================================
def example_custom_prompt():
    """Use custom prompt with LLM."""
    print("\nExample 5: Custom Prompt")
    print("=" * 80)
    
    from app.llm import OpenAIHandler
    
    handler = OpenAIHandler()
    
    # Custom messages
    messages = [
        {"role": "system", "content": "Sen yardımcı bir asistansın."},
        {"role": "user", "content": "2+2 kaç eder?"}
    ]
    
    response = handler.chat_completion(messages)
    
    print(f"\nCevap: {response['content']}")
    print(f"Tokens: {response['total_tokens']}")
    print(f"Maliyet: ${response['cost']:.4f}")


# ============================================================================
# Main
# ============================================================================
def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("SUBU CHATBOT - EXAMPLE USAGE")
    print("=" * 80)
    
    examples = {
        "1": ("Direct RAG Query", example_direct_rag),
        "2": ("Vector Search", example_vector_search),
        "3": ("PDF Processing", example_process_pdf),
        "4": ("Database Query", example_database_query),
        "5": ("Custom Prompt", example_custom_prompt),
    }
    
    print("\nChoose example:")
    for key, (name, _) in examples.items():
        print(f"{key}. {name}")
    print("0. Run all")
    
    choice = input("\nEnter choice: ").strip()
    
    if choice == "0":
        for name, func in examples.values():
            try:
                func()
            except Exception as e:
                print(f"\n❌ Error in {name}: {e}")
    elif choice in examples:
        name, func = examples[choice]
        try:
            func()
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Invalid choice")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
