#!/usr/bin/env python3
"""
Manuel eklenen PDF ve JSON dosyalarını sisteme yükler:

1. data/raw_pdfs içindeki PDF'leri JSON'a çevirir (henüz JSON'u yoksa)
2. data/processed_json içindeki tüm JSON'lardan vector store'u yeniden oluşturur (LLM bu veriyi kullanır)
3. İsteğe bağlı: Bu dosyaları veritabanına kaydeder (sidebar'da liste görünsün diye)

Sunucuda manuel kopyaladığınız PDF/JSON'ların chatbot tarafından kullanılması için
bu script'i çalıştırın.

Kullanım:
    cd backend && source venv/bin/activate && python load_manual_documents.py
    python load_manual_documents.py --no-db   # Sadece vector store, DB'ye kaydetme
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

backend = Path(__file__).resolve().parent
sys.path.insert(0, str(backend))
os.chdir(backend)  # Relative paths (settings.json_directory vb.) backend'e göre çözülsün

from app.config import settings
from app.database import SessionLocal, init_db
from app.models import Document, DocumentStatus
from app.converter.pdf_processor import PDFProcessor
from app.rag.document_loader import DocumentLoader
from app.rag.chunker import MevzuatChunker
from app.rag.vector_store import VectorStoreManager


def _backend_path(relative: str) -> Path:
    p = Path(relative)
    if p.is_absolute():
        return p
    return (Path(__file__).resolve().parent / relative).resolve()


def main():
    parser = argparse.ArgumentParser(description="Manuel PDF/JSON dosyalarını yükler ve vector store oluşturur.")
    parser.add_argument("--no-db", action="store_true", help="Veritabanına kaydetme, sadece vector store")
    args = parser.parse_args()

    raw_dir = _backend_path(settings.download_directory.replace("./", ""))
    json_dir = _backend_path(settings.json_directory.replace("./", ""))
    chroma_dir = _backend_path(settings.chroma_persist_directory.replace("./", ""))

    raw_dir.mkdir(parents=True, exist_ok=True)
    json_dir.mkdir(parents=True, exist_ok=True)

    # 1) PDF → JSON (henüz JSON'u olmayan PDF'ler)
    pdf_files = list(raw_dir.glob("*.pdf"))
    to_process = []
    for pdf_path in pdf_files:
        json_name = pdf_path.stem + ".json"
        if not (json_dir / json_name).exists():
            to_process.append(str(pdf_path))

    if to_process:
        print(f"  {len(to_process)} PDF JSON'a çevriliyor...")
        processor = PDFProcessor()
        for pdf_path in to_process:
            try:
                data = processor.process_pdf(pdf_path)
                processor.save_json(data)
                print(f"    ✓ {Path(pdf_path).name}")
            except Exception as e:
                print(f"    ✗ {Path(pdf_path).name}: {e}")
    else:
        print("  PDF → JSON: atlanıyor (tüm PDF'lerin JSON'u var veya PDF yok).")

    # 2) Vector store'u tüm JSON'lardan yeniden oluştur
    json_files = list(json_dir.glob("*.json"))
    if not json_files:
        print("Hata: data/processed_json içinde .json dosyası yok.")
        sys.exit(1)

    print(f"  Vector store: {len(json_files)} JSON dosyasından oluşturuluyor...")
    if chroma_dir.exists():
        shutil.rmtree(chroma_dir)
        chroma_dir.mkdir(parents=True, exist_ok=True)

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
    print(f"    {len(documents)} döküman, {len(chunks)} chunk.")

    vector_store = VectorStoreManager()
    vector_store.initialize_embeddings()
    vector_store.create_or_load()
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        vector_store.add_documents(batch)
        print(f"    Eklenen: {min(i + batch_size, len(chunks))}/{len(chunks)}")

    stats = vector_store.get_collection_stats()
    print(f"  Vector store tamamlandı: {stats.get('document_count', 0)} kayıt.")

    # 3) İsteğe bağlı: Veritabanına kaydet
    if not args.no_db:
        init_db()
        db = SessionLocal()
        try:
            existing_links = {r.qdms_link for r in db.query(Document).all()}
            added = 0
            for jpath in json_files:
                try:
                    with open(jpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    title = data.get("metadata", {}).get("title", jpath.stem)
                    qdms_link = f"manual:{jpath.name}"
                    if qdms_link in existing_links:
                        continue
                    doc = Document(
                        title=title[:500],
                        qdms_link=qdms_link,
                        pdf_path=None,
                        json_path=str(jpath),
                        status=DocumentStatus.PROCESSED,
                        page_count=data.get("statistics", {}).get("total_pages"),
                        processed_at=datetime.utcnow(),
                    )
                    db.add(doc)
                    existing_links.add(qdms_link)
                    added += 1
                except Exception as e:
                    print(f"    DB kayıt atlandı {jpath.name}: {e}")
            db.commit()
            print(f"  Veritabanı: {added} döküman eklendi.")
        finally:
            db.close()

    print("Tamamlandı. Backend'i yeniden başlatın: sudo systemctl restart subu-backend")
    return 0


if __name__ == "__main__":
    sys.exit(main())
