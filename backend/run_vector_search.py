#!/usr/bin/env python3
"""One-off vector search: makine mühendisi görev yetkileri."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.rag.vector_store import VectorStoreManager

vs = VectorStoreManager()
vs.create_or_load()

results = vs.search_with_score("makine mühendisi görev yetkileri", k=5)
for doc, score in results:
    title = doc.metadata.get('title', '')[:50]
    art = doc.metadata.get('article_number', '')
    length = len(doc.page_content)
    preview = doc.page_content[:100].replace('\n', ' ')
    print(f"score={score:.3f} | Madde={art} | {length} chars | {preview}")
