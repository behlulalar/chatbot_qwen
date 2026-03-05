#!/usr/bin/env python3
"""
Baştan embed: ChromaDB'yi siler, processed_json'daki tüm JSON'lardan
chunk'ları (MevzuatChunker + _enrich_content ile) oluşturup ChromaDB'ye yazar.

Kullanım:
    cd backend && . venv/bin/activate && python rebuild_embeddings.py
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

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
    json_dir = _resolve_path(settings.json_directory.replace("./", ""))
    chroma_dir = _resolve_path(settings.chroma_persist_directory.replace("./", ""))

    json_dir.mkdir(parents=True, exist_ok=True)
    json_files = list(json_dir.glob("*.json"))
    if not json_files:
        print("Hata: data/processed_json içinde .json dosyası yok.")
        sys.exit(1)

    print("1) Mevcut vector store siliniyor...")
    if chroma_dir.exists():
        shutil.rmtree(chroma_dir)
    chroma_dir.mkdir(parents=True, exist_ok=True)

    print("2) JSON'lar yükleniyor ve chunk'lanıyor (MevzuatChunker + ARAMA_ETİKETLERİ)...")
    loader = DocumentLoader(str(json_dir))
    documents = loader.load_all()
    if not documents:
        print("Yüklenecek döküman yok.")
        sys.exit(1)

    chunker = MevzuatChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chunks = chunker.chunk_documents(documents)
    print(f"   {len(documents)} döküman → {len(chunks)} chunk.")

    print("3) ChromaDB'ye embed ediliyor...")
    vector_store = VectorStoreManager(persist_directory=str(chroma_dir))
    vector_store.initialize_embeddings()
    vector_store.create_or_load()

    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        vector_store.add_documents(batch)
        print(f"   Eklenen: {min(i + batch_size, len(chunks))}/{len(chunks)}")

    stats = vector_store.get_collection_stats()
    print(f"\nTamamlandı. Vector store: {stats.get('document_count', 0)} kayıt.")
    print("Sunucuyu yeniden başlattığınızda BM25 index de bu veriyle oluşturulacak.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
