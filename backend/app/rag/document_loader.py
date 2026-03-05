"""
Document Loader - Loads processed JSON files for RAG pipeline.

Filtering strategy:
  - Skip empty articles (content = 0 chars)
  - Skip structural/boilerplate articles that never answer user questions
  - Skip very short cross-reference articles (< 30 chars)
  - Add pre-computed normalized metadata for fast runtime filtering
"""
import json
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Optional, Set
from langchain_core.documents import Document

from app.config import settings, resolve_json_directory
from app.utils.logger import setup_logger

logger = setup_logger("document_loader", "./logs/document_loader.log")

_STRUCTURAL_TITLES: Set[str] = {
    "amac", "amaç",
    "kapsam",
    "dayanak",
    "yururluk", "yürürlük",
    "yurutme", "yürütme",
    "kisaltmalar", "kısaltmalar",
}

_SKIP_TITLE_PREFIXES = (
    "aykırı", "hüküm bulunmayan", "huküm bulunmayan",
    "değiştirilen", "geçici madde",
)

MIN_USEFUL_CONTENT_CHARS = 30


def _normalize_for_filter(text: str) -> str:
    """Fast Turkish normalization for filtering decisions."""
    if not text:
        return ""
    _map = {"İ": "I", "ı": "i", "Ğ": "G", "ğ": "g", "Ü": "U", "ü": "u",
            "Ş": "S", "ş": "s", "Ö": "O", "ö": "o", "Ç": "C", "ç": "c"}
    r = text
    for k, v in _map.items():
        r = r.replace(k, v)
    r = r.lower()
    r = unicodedata.normalize("NFD", r)
    return "".join(c for c in r if unicodedata.category(c) != "Mn")


def _should_skip_article(article: Dict) -> bool:
    """Decide whether an article is useful for retrieval."""
    content = article.get("content", "")
    title_raw = article.get("article_title", "")
    char_count = len(content)

    if char_count == 0:
        return True

    title_norm = _normalize_for_filter(title_raw).strip()

    if title_norm in _STRUCTURAL_TITLES and char_count < 500:
        return True

    if title_norm == "tanimlar" and char_count < 200:
        return True

    if any(title_norm.startswith(p) for p in ("aykiri", "hukum bulunmayan", "degistirilen", "gecici madde")):
        if char_count < 200:
            return True

    if char_count < MIN_USEFUL_CONTENT_CHARS:
        return True

    return False


class DocumentLoader:
    """
    Loads processed JSON documents and converts them to LangChain Document format.

    Usage:
        loader = DocumentLoader()
        documents = loader.load_all()
    """

    def __init__(self, json_directory: Optional[str] = None):
        self.json_dir = resolve_json_directory(json_directory) if json_directory else resolve_json_directory()
        if not self.json_dir.exists():
            raise ValueError(f"JSON directory not found: {self.json_dir}")
        logger.info(f"DocumentLoader initialized with directory: {self.json_dir}")

    def load_all(self) -> List[Document]:
        json_files = list(self.json_dir.glob("*.json"))
        logger.info(f"Found {len(json_files)} JSON files to load")

        all_documents: List[Document] = []
        skipped = 0

        for json_file in json_files:
            try:
                docs, s = self._load_single_filtered(json_file)
                all_documents.extend(docs)
                skipped += s
            except Exception as e:
                logger.error(f"Error loading {json_file.name}: {e}")

        logger.info(
            f"Loaded {len(all_documents)} documents from {len(json_files)} files "
            f"(skipped {skipped} useless articles)"
        )
        return all_documents

    def load_single(self, json_path: Path) -> List[Document]:
        docs, _ = self._load_single_filtered(json_path)
        return docs

    def _load_single_filtered(self, json_path: Path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        documents: List[Document] = []
        skipped = 0
        meta_base = data['metadata']
        title = meta_base['title']
        title_norm = _normalize_for_filter(title)

        if not data['articles'] or data['articles'][0]['article_number'] == "0":
            doc = Document(
                page_content=data['full_text'],
                metadata={
                    "source": meta_base['filename'],
                    "title": title,
                    "title_normalized": title_norm,
                    "page_count": meta_base['page_count'],
                    "json_path": str(json_path),
                    "article_number": "full",
                    "article_title": "",
                    "type": "full_document"
                }
            )
            documents.append(doc)
        else:
            for article in data['articles']:
                if _should_skip_article(article):
                    skipped += 1
                    logger.debug(
                        f"Skipped: {title[:30]} Madde {article['article_number']} "
                        f"({article.get('article_title','')[:30]}, {len(article.get('content',''))} ch)"
                    )
                    continue

                article_header = f"MADDE {article['article_number']}"
                if article['article_title']:
                    article_header += f" - {article['article_title']}"
                content = f"{article_header}\n\n{article['content']}"

                art_title = article.get('article_title', '')
                paragraphs = article.get('paragraphs', [])
                para_count = len(paragraphs) if isinstance(paragraphs, list) else 0

                metadata = {
                    "source": meta_base['filename'],
                    "title": title,
                    "title_normalized": title_norm,
                    "page_count": meta_base['page_count'],
                    "json_path": str(json_path),
                    "article_number": article['article_number'],
                    "article_title": art_title,
                    "article_title_normalized": _normalize_for_filter(art_title),
                    "paragraph_count": para_count,
                    "character_count": len(content),
                    "type": "article"
                }

                documents.append(Document(page_content=content, metadata=metadata))

        logger.debug(f"Loaded {len(documents)} docs from {json_path.name} (skipped {skipped})")
        return documents, skipped

    def load_by_title(self, title_pattern: str) -> List[Document]:
        matching_files = list(self.json_dir.glob(f"*{title_pattern}*.json"))
        logger.info(f"Found {len(matching_files)} files matching pattern: {title_pattern}")

        documents: List[Document] = []
        for json_file in matching_files:
            try:
                docs = self.load_single(json_file)
                documents.extend(docs)
            except Exception as e:
                logger.error(f"Error loading {json_file.name}: {e}")
        return documents

    def get_statistics(self) -> Dict:
        json_files = list(self.json_dir.glob("*.json"))

        total_articles = 0
        total_pages = 0
        total_size = 0

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    total_articles += data['statistics']['total_articles']
                    total_pages += data['statistics']['total_pages']
                    total_size += json_file.stat().st_size
            except Exception as e:
                logger.error(f"Error reading {json_file.name}: {e}")

        return {
            "total_files": len(json_files),
            "total_articles": total_articles,
            "total_pages": total_pages,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
