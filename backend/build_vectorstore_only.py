#!/usr/bin/env python3
"""
Sadece mevcut JSON dosyalarından vektör mağazası oluşturur (scraping yok).

Sunucuda scraping çalışmıyorsa veya sadece örnek veri varsa bu script ile
vector store'u doldurup döküman sayısının 0'dan çıkmasını ve chatbot'un
cevap verebilmesini sağlayabilirsiniz.

Kullanım:
    cd backend && source venv/bin/activate && python build_vectorstore_only.py
    python build_vectorstore_only.py --rebuild   # Mevcut vector store'u siler, tüm JSON'lardan yeniden oluşturur
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.rag.document_loader import DocumentLoader
from app.rag.chunker import MevzuatChunker
from app.rag.vector_store import VectorStoreManager


def _resolve_path(relative_path: str) -> Path:
    p = Path(relative_path)
    if p.is_absolute():
        return p
    return (Path(__file__).resolve().parent / relative_path).resolve()


def main():
    parser = argparse.ArgumentParser(description="JSON dosyalarından vector store oluşturur.")
    parser.add_argument("--rebuild", action="store_true", help="Mevcut vector store'u silip sıfırdan oluştur")
    args = parser.parse_args()

    json_dir = _resolve_path(settings.json_directory.replace("./", ""))
    json_dir.mkdir(parents=True, exist_ok=True)

    json_files = list(json_dir.glob("*.json"))
    if not json_files:
        print("Uyarı: data/processed_json içinde .json dosyası yok.")
        print("Örnek veri için backend/data/processed_json/sample_mevzuat.json kullanılabilir.")
        sys.exit(1)

    if args.rebuild:
        chroma_dir = _resolve_path(settings.chroma_persist_directory.replace("./", ""))
        if chroma_dir.exists():
            print("Mevcut vector store siliniyor...")
            shutil.rmtree(chroma_dir)
            chroma_dir.mkdir(parents=True, exist_ok=True)

    print("JSON dosyalarından vector store oluşturuluyor...")
    loader = DocumentLoader(str(json_dir))
    documents = loader.load_all()
    if not documents:
        print("Yüklenecek döküman yok.")
        sys.exit(1)

    chunker = MevzuatChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap
    )
    chunks = chunker.chunk_documents(documents)
    print(f"  {len(documents)} döküman, {len(chunks)} chunk.")

    vector_store = VectorStoreManager()
    vector_store.initialize_embeddings()
    vector_store.create_or_load()

    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        vector_store.add_documents(batch)
        print(f"  Eklenen: {min(i + batch_size, len(chunks))}/{len(chunks)}")

    stats = vector_store.get_collection_stats()
    print(f"Tamamlandı. Vector store: {stats.get('document_count', 0)} kayıt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
