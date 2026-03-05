#!/usr/bin/env python3
"""
One-off script: similarity search in vector store for "geçme notu" and "bağıl değerlendirme".
Shows title, article_number, and score for each result.
Run from backend: python vector_store_search.py
"""
import sys
from pathlib import Path

# Ensure backend is on path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import resolve_chroma_directory
from app.rag import VectorStoreManager


def run_search(manager: VectorStoreManager, query: str, k: int = 5):
    print(f"\n{'='*70}")
    print(f"Query: {query!r}  (k={k})")
    print("="*70)
    results = manager.search_with_score(query=query, k=k)
    for i, (doc, score) in enumerate(results, 1):
        title = doc.metadata.get("title", "") or "(no title)"
        article_number = doc.metadata.get("article_number", "") or "(no article_number)"
        print(f"  [{i}] score={score:.4f}  |  title={title[:55]}  |  article_number={article_number}")
    if not results:
        print("  (no results)")
    return results


def main():
    chroma_dir = str(resolve_chroma_directory())
    print(f"Chroma path: {chroma_dir}")
    manager = VectorStoreManager(persist_directory=chroma_dir)
    manager.create_or_load()

    run_search(manager, "geçme notu", k=5)
    run_search(manager, "bağıl değerlendirme", k=5)

    print()


if __name__ == "__main__":
    main()
