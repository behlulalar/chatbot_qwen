"""
Test script for RAG Pipeline.

This script:
1. Loads JSON documents
2. Chunks them intelligently
3. Creates embeddings
4. Stores in ChromaDB
5. Tests retrieval

Usage:
    python test_rag_pipeline.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.rag import DocumentLoader, MevzuatChunker, VectorStoreManager
from app.config import settings


def test_document_loading():
    """Test 1: Load JSON documents."""
    print("=" * 80)
    print("TEST 1: Document Loading")
    print("=" * 80)
    
    loader = DocumentLoader()
    
    # Get statistics first
    stats = loader.get_statistics()
    print(f"\n📊 JSON Files Statistics:")
    print(f"   Total files: {stats['total_files']}")
    print(f"   Total articles: {stats['total_articles']}")
    print(f"   Total pages: {stats['total_pages']}")
    print(f"   Total size: {stats['total_size_mb']} MB")
    
    # Load all documents
    print(f"\n📥 Loading all documents...")
    documents = loader.load_all()
    
    print(f"\n✅ Loaded {len(documents)} documents")
    
    # Show first 3
    print(f"\nFirst 3 documents:")
    for i, doc in enumerate(documents[:3], 1):
        print(f"\n  {i}. {doc.metadata['title'][:50]}...")
        print(f"     Article: {doc.metadata.get('article_number', 'N/A')}")
        print(f"     Content length: {len(doc.page_content)} chars")
        print(f"     Preview: {doc.page_content[:100]}...")
    
    return documents


def test_chunking(documents):
    """Test 2: Chunk documents."""
    print("\n" + "=" * 80)
    print("TEST 2: Document Chunking")
    print("=" * 80)
    
    chunker = MevzuatChunker()
    
    print(f"\n⚙️ Chunking settings:")
    print(f"   Chunk size: {chunker.chunk_size}")
    print(f"   Chunk overlap: {chunker.chunk_overlap}")
    print(f"   Max chunk size: {chunker.max_chunk_size}")
    
    print(f"\n✂️ Chunking {len(documents)} documents...")
    chunks = chunker.chunk_documents(documents)
    
    # Get statistics
    stats = chunker.get_chunk_statistics(chunks)
    
    print(f"\n✅ Chunking complete!")
    print(f"\n📊 Chunk Statistics:")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Single article chunks: {stats['single_articles']}")
    print(f"   Split article chunks: {stats['chunked_articles']}")
    print(f"   Average chunk size: {stats['avg_chunk_size']} chars")
    print(f"   Min chunk size: {stats['min_chunk_size']} chars")
    print(f"   Max chunk size: {stats['max_chunk_size']} chars")
    
    # Show a chunked article example
    chunked_examples = [c for c in chunks if c.metadata.get('is_chunked')]
    if chunked_examples:
        print(f"\n📄 Example of split article:")
        example = chunked_examples[0]
        print(f"   Title: {example.metadata['title'][:50]}...")
        print(f"   Article: {example.metadata['article_number']}")
        print(f"   Chunk {example.metadata['chunk_index'] + 1} of {example.metadata['total_chunks']}")
    
    return chunks


def test_vector_store_creation(chunks):
    """Test 3: Create vector store."""
    print("\n" + "=" * 80)
    print("TEST 3: Vector Store Creation")
    print("=" * 80)
    
    # Check if OpenAI API key is set
    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        print("\n⚠️ OpenAI API key not set!")
        print("   Please set OPENAI_API_KEY in .env file")
        print("   Example: OPENAI_API_KEY=sk-...")
        return None
    
    print(f"\n🔧 Initializing vector store...")
    print(f"   Persist directory: {settings.chroma_persist_directory}")
    print(f"   Embedding model: {settings.embedding_model}")
    
    manager = VectorStoreManager()
    
    # Initialize embeddings
    print(f"\n🔑 Initializing OpenAI embeddings...")
    manager.initialize_embeddings()
    
    # Create or load vector store
    print(f"\n💾 Creating/loading vector store...")
    vectorstore = manager.create_or_load()
    
    # Get existing stats
    stats = manager.get_collection_stats()
    existing_count = stats.get('document_count', 0)
    
    if existing_count > 0:
        print(f"\n📊 Existing collection found:")
        print(f"   Documents in collection: {existing_count}")
        
        choice = input("\n   Do you want to re-index? (y/n): ").strip().lower()
        if choice == 'y':
            print(f"\n🗑️ Deleting existing collection...")
            manager.delete_collection()
            manager.create_or_load()
        else:
            print(f"\n✅ Using existing collection")
            return manager
    
    # Add documents
    print(f"\n➕ Adding {len(chunks)} chunks to vector store...")
    print(f"   This may take a few minutes...")
    
    try:
        ids = manager.add_documents(chunks, batch_size=100)
        print(f"\n✅ Successfully added {len(ids)} documents!")
        
        # Get updated stats
        stats = manager.get_collection_stats()
        print(f"\n📊 Vector Store Stats:")
        print(f"   Collection: {stats['collection_name']}")
        print(f"   Document count: {stats['document_count']}")
        
        return manager
    
    except Exception as e:
        print(f"\n❌ Error creating vector store: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_retrieval(manager):
    """Test 4: Test semantic search."""
    print("\n" + "=" * 80)
    print("TEST 4: Semantic Search")
    print("=" * 80)
    
    if not manager:
        print("\n⚠️ Vector store not available")
        return
    
    # Test queries
    test_queries = [
        "Akademik personele ödül nasıl verilir?",
        "Lisansüstü öğrencilerin azami süreleri nedir?",
        "Bilimsel araştırma projesi başvurusu nasıl yapılır?"
    ]
    
    print(f"\n🔍 Testing retrieval with sample queries...\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'─' * 80}")
        print(f"Query {i}: {query}")
        print(f"{'─' * 80}")
        
        # Search with scores
        results = manager.search_with_score(query, k=3)
        
        print(f"\nTop 3 Results:")
        for j, (doc, score) in enumerate(results, 1):
            print(f"\n  {j}. Score: {score:.4f}")
            print(f"     Source: {doc.metadata['title'][:50]}...")
            print(f"     Article: {doc.metadata.get('article_number', 'N/A')}")
            print(f"     Content: {doc.page_content[:200]}...")


def main():
    """Main test runner."""
    print("\n" + "=" * 80)
    print("RAG PIPELINE TEST")
    print("=" * 80)
    
    print("\nThis will:")
    print("1. Load all JSON documents")
    print("2. Chunk them intelligently")
    print("3. Create embeddings (requires OpenAI API key)")
    print("4. Store in ChromaDB")
    print("5. Test semantic search")
    
    print("\nChoose test to run:")
    print("1. Document Loading Only (fast)")
    print("2. Document Loading + Chunking (fast)")
    print("3. Full Pipeline: Load + Chunk + Vector Store (slow, needs API key)")
    print("4. Test Retrieval Only (requires existing vector store)")
    print("0. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        test_document_loading()
    
    elif choice == "2":
        docs = test_document_loading()
        test_chunking(docs)
    
    elif choice == "3":
        docs = test_document_loading()
        chunks = test_chunking(docs)
        manager = test_vector_store_creation(chunks)
        
        if manager:
            test_retrieval(manager)
    
    elif choice == "4":
        print("\n🔍 Testing retrieval on existing vector store...")
        manager = VectorStoreManager()
        manager.initialize_embeddings()
        manager.create_or_load()
        test_retrieval(manager)
    
    elif choice == "0":
        print("Exiting...")
        return
    
    else:
        print("Invalid choice. Running document loading test...")
        test_document_loading()
    
    print("\n" + "=" * 80)
    print("Test completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
