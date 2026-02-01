"""
Rebuild vector store from scratch.

This script deletes the existing vector store and rebuilds it from processed JSON files.
"""
import shutil
import os
from pathlib import Path

# Paths
CHROMA_DB_PATH = "./data/chroma_db"
PROCESSED_JSON_PATH = "./data/processed_json"

def main():
    print("=" * 60)
    print("VECTOR STORE REBUILD TOOL")
    print("=" * 60)
    
    # Check if processed JSON files exist
    if not os.path.exists(PROCESSED_JSON_PATH):
        print(f"❌ Error: {PROCESSED_JSON_PATH} not found!")
        return
    
    json_files = list(Path(PROCESSED_JSON_PATH).glob("*.json"))
    print(f"\n📁 Found {len(json_files)} JSON files")
    
    # List YAZ OKULU
    yaz_okulu_files = [f for f in json_files if "YAZ" in f.name.upper()]
    print(f"📄 YAZ OKULU files: {len(yaz_okulu_files)}")
    for f in yaz_okulu_files:
        print(f"   - {f.name}")
    
    # Check if vector store exists
    if os.path.exists(CHROMA_DB_PATH):
        print(f"\n🗑️  Deleting existing vector store: {CHROMA_DB_PATH}")
        shutil.rmtree(CHROMA_DB_PATH)
        print("✅ Deleted!")
    else:
        print(f"\n📭 No existing vector store found at {CHROMA_DB_PATH}")
    
    # Now rebuild
    print("\n🔨 Rebuilding vector store...")
    print("⏳ This will take a few minutes...")
    
    from app.rag import VectorStoreManager, DocumentLoader
    
    # Initialize
    vsm = VectorStoreManager(CHROMA_DB_PATH)
    loader = DocumentLoader(PROCESSED_JSON_PATH)
    
    # Load all documents
    print("\n📖 Loading documents from JSON files...")
    all_documents = []
    
    for json_file in json_files:
        print(f"   Loading: {json_file.name}...", end=" ")
        try:
            docs = loader.load_single(json_file)
            all_documents.extend(docs)
            print(f"✅ ({len(docs)} chunks)")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n📊 Total chunks loaded: {len(all_documents)}")
    
    # Add to vector store
    print("\n💾 Adding to vector store...")
    batch_size = 50
    total_batches = (len(all_documents) + batch_size - 1) // batch_size
    
    for i in range(0, len(all_documents), batch_size):
        batch = all_documents[i:i + batch_size]
        batch_num = i // batch_size + 1
        print(f"   Batch {batch_num}/{total_batches} ({len(batch)} chunks)...", end=" ")
        try:
            vsm.add_documents(batch)
            print("✅")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ VECTOR STORE REBUILT SUCCESSFULLY!")
    print("=" * 60)
    
    # Verify YAZ OKULU is in there
    print("\n🔍 Verifying YAZ OKULU YÖNERGESİ...")
    results = vsm.search_with_score("yaz okulu yönergesi", k=3)
    
    print(f"Found {len(results)} results:")
    for i, (doc, score) in enumerate(results, 1):
        title = doc.metadata.get('title', 'Unknown')
        print(f"   [{i}] score={score:.3f} | {title}")
    
    yaz_okulu_found = any("YAZ OKULU" in doc.metadata.get('title', '') for doc, _ in results)
    
    if yaz_okulu_found:
        print("\n✅ YAZ OKULU YÖNERGESİ FOUND IN VECTOR STORE!")
    else:
        print("\n❌ WARNING: YAZ OKULU YÖNERGESİ NOT FOUND!")
    
    print("\n🎉 Done! You can now restart the backend.")


if __name__ == "__main__":
    main()
