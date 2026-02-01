"""
Rebuild vector store from scratch.

This script:
1. Deletes old vector store
2. Loads all JSONs
3. Creates fresh vector store
"""
import sys
from pathlib import Path
import shutil

sys.path.insert(0, str(Path(__file__).parent))

from app.rag import DocumentLoader, MevzuatChunker, VectorStoreManager
from app.config import settings

print("=" * 80)
print("REBUILDING VECTOR STORE")
print("=" * 80)

# Step 1: Delete old vector store
chroma_path = Path(settings.chroma_persist_directory)
if chroma_path.exists():
    print(f"\n🗑️  Deleting old vector store: {chroma_path}")
    shutil.rmtree(chroma_path)
    print("✅ Deleted!")
else:
    print(f"\n📁 No existing vector store found")

# Step 2: Load documents
print("\n📂 Loading JSON documents...")
loader = DocumentLoader()
documents = loader.load_all()
print(f"✅ Loaded {len(documents)} documents")

# Print some document titles
print("\n📋 Sample documents:")
titles = set()
for doc in documents[:20]:
    title = doc.metadata.get('title', 'Unknown')
    if title not in titles:
        titles.add(title)
        print(f"  - {title[:60]}...")

# Step 3: Chunk documents
print(f"\n✂️  Chunking {len(documents)} documents...")
chunker = MevzuatChunker()
chunks = chunker.chunk_documents(documents)
print(f"✅ Created {len(chunks)} chunks")

# Step 4: Create vector store
print(f"\n🔮 Creating vector store...")
print(f"   Location: {chroma_path}")
print(f"   Batch size: 100")
print(f"   This may take 5-10 minutes...")

vector_manager = VectorStoreManager()
vector_manager.create_or_load()
vector_manager.add_documents(chunks)

# Step 5: Verify
print("\n✅ Vector store created!")
stats = vector_manager.get_collection_stats()
print(f"\n📊 Final Statistics:")
print(f"   Total chunks: {stats.get('document_count', 0)}")
print(f"   Collection: {stats.get('collection_name', 'N/A')}")

print("\n" + "=" * 80)
print("DONE! Vector store is ready.")
print("=" * 80)
print("\n🚀 Next steps:")
print("   1. Restart backend: python run_server.py")
print("   2. Test query: 'lisans bölümünden mezun olma şartları'")
