"""
Chunker - Intelligent text splitting for mevzuat documents.

Strategy based on data analysis (1957 articles):
  - 71% of articles are ≤ 800 chars → keep as single chunk
  - 15% are 800-1500 chars → keep as single chunk (still effective for embedding)
  - 14% are > 1500 chars → split by fıkra boundaries to preserve legal structure
  - 88 articles are > 3000 chars, 31 are > 5000 chars → must be split

Splitting uses fıkra "(1)", "(2)" boundaries rather than arbitrary character splits
so each chunk remains a legally coherent unit.
"""
from typing import List, Optional
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("chunker", "./logs/chunker.log")

SPLIT_THRESHOLD = 1500
MAX_SINGLE_CHUNK = 4000

_FIKRA_PATTERN_STR = r'\n\s*\(\d+\)\s*'


class MevzuatChunker:
    """
    Smart chunker for Turkish legal documents.

    - Articles ≤ SPLIT_THRESHOLD: single chunk (semantic integrity preserved)
    - Articles > SPLIT_THRESHOLD: split by fıkra boundaries first, then by
      RecursiveCharacterTextSplitter as fallback
    - Each chunk carries original article header for embedding signal
    """

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", ", ", " ", ""],
            length_function=len,
        )

        logger.info(
            f"MevzuatChunker initialized: chunk_size={self.chunk_size}, "
            f"overlap={self.chunk_overlap}, split_threshold={SPLIT_THRESHOLD}"
        )

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        logger.info(f"Starting to chunk {len(documents)} documents")

        chunked: List[Document] = []
        split_count = 0

        for doc in documents:
            content_length = len(doc.page_content)

            if content_length <= SPLIT_THRESHOLD:
                chunked.append(doc)
            else:
                parts = self._split_by_fikra(doc)
                if len(parts) > 1:
                    split_count += 1
                chunked.extend(parts)

        logger.info(
            f"Chunking complete: {len(documents)} articles → {len(chunked)} chunks "
            f"({split_count} articles were split)"
        )
        return chunked

    def chunk_document(self, doc: Document) -> List[Document]:
        return self.chunk_documents([doc])

    def _split_by_fikra(self, doc: Document) -> List[Document]:
        """
        Split a long article by fıkra "(1)", "(2)" boundaries.
        Falls back to RecursiveCharacterTextSplitter if fıkra split is not effective.
        """
        import re

        content = doc.page_content
        header = self._extract_header(content)

        fikra_parts = re.split(_FIKRA_PATTERN_STR, content)
        fikra_markers = re.findall(_FIKRA_PATTERN_STR, content)

        if len(fikra_parts) <= 1:
            return self._fallback_split(doc, header)

        reconstructed: List[str] = [fikra_parts[0]]
        for marker, part in zip(fikra_markers, fikra_parts[1:]):
            reconstructed.append(marker.strip() + " " + part)

        merged_chunks: List[str] = []
        current = ""
        for segment in reconstructed:
            candidate = (current + "\n" + segment).strip() if current else segment
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    merged_chunks.append(current)
                if len(segment) > MAX_SINGLE_CHUNK:
                    sub_parts = self.text_splitter.split_text(segment)
                    merged_chunks.extend(sub_parts)
                    current = ""
                else:
                    current = segment
        if current:
            merged_chunks.append(current)

        if len(merged_chunks) <= 1:
            return [doc]

        result: List[Document] = []
        for i, chunk_text in enumerate(merged_chunks):
            new_meta = doc.metadata.copy()
            new_meta["chunk_index"] = i
            new_meta["total_chunks"] = len(merged_chunks)
            new_meta["is_chunked"] = True
            new_meta["character_count"] = len(chunk_text)

            if i > 0 and header and not chunk_text.startswith(header[:20]):
                chunk_text = header + "\n\n" + chunk_text

            result.append(Document(page_content=chunk_text, metadata=new_meta))

        logger.debug(
            f"Split Madde {doc.metadata.get('article_number', '?')}: "
            f"{len(doc.page_content)} ch → {len(result)} chunks"
        )
        return result

    def _fallback_split(self, doc: Document, header: str) -> List[Document]:
        """RecursiveCharacterTextSplitter ile bölme (fıkra yoksa)."""
        if len(doc.page_content) <= MAX_SINGLE_CHUNK:
            return [doc]

        texts = self.text_splitter.split_text(doc.page_content)
        if len(texts) <= 1:
            return [doc]

        result: List[Document] = []
        for i, text in enumerate(texts):
            new_meta = doc.metadata.copy()
            new_meta["chunk_index"] = i
            new_meta["total_chunks"] = len(texts)
            new_meta["is_chunked"] = True
            new_meta["character_count"] = len(text)

            if i > 0 and header and not text.startswith(header[:20]):
                text = header + "\n\n" + text

            result.append(Document(page_content=text, metadata=new_meta))

        return result

    @staticmethod
    def _extract_header(content: str) -> str:
        """Extract article header (MADDE X - Title) from content start."""
        first_break = content.find("\n\n")
        if first_break == -1 or first_break > 150:
            first_line = content.split("\n")[0].strip()
            return first_line if len(first_line) < 150 else ""
        return content[:first_break].strip()

    def get_chunk_statistics(self, chunks: List[Document]) -> dict:
        chunk_sizes = [len(c.page_content) for c in chunks]
        chunked_count = sum(1 for c in chunks if c.metadata.get('is_chunked', False))

        return {
            "total_chunks": len(chunks),
            "chunked_articles": chunked_count,
            "single_articles": len(chunks) - chunked_count,
            "avg_chunk_size": round(sum(chunk_sizes) / len(chunk_sizes)) if chunk_sizes else 0,
            "min_chunk_size": min(chunk_sizes) if chunk_sizes else 0,
            "max_chunk_size": max(chunk_sizes) if chunk_sizes else 0,
        }


DocumentChunker = MevzuatChunker
