"""
Chunker - Intelligent text splitting for mevzuat documents.

This module implements article-based chunking strategy optimized for
Turkish legal documents (yönerge, mevzuat).
"""
from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("chunker", "./logs/chunker.log")


class MevzuatChunker:
    """
    Smart chunker for mevzuat documents.
    
    Strategy:
    - Small articles (< chunk_size): Keep as single chunk
    - Large articles (> chunk_size): Split with overlap
    - Preserve article boundaries
    - Maintain metadata
    
    Usage:
        chunker = MevzuatChunker()
        chunks = chunker.chunk_documents(documents)
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        max_chunk_size: int = 1500
    ):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
            max_chunk_size: Maximum size before forcing split
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.max_chunk_size = max_chunk_size
        
        # Text splitter for large articles
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=[
                "\n\n",  # Paragraphs
                "\n",    # Lines
                ". ",    # Sentences
                ", ",    # Clauses
                " ",     # Words
                ""       # Characters
            ],
            length_function=len,
        )
        
        logger.info(f"MevzuatChunker initialized: chunk_size={self.chunk_size}, overlap={self.chunk_overlap}")
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Chunk documents intelligently.
        
        Args:
            documents: List of Document objects (articles)
        
        Returns:
            List of chunked Document objects
        """
        logger.info(f"Starting to chunk {len(documents)} documents")
        
        chunked_docs = []
        
        for doc in documents:
            content_length = len(doc.page_content)
            
            # Strategy 1: Small articles - keep as is
            if content_length <= self.chunk_size:
                chunked_docs.append(doc)
                logger.debug(f"Kept article {doc.metadata.get('article_number', '?')} as single chunk ({content_length} chars)")
            
            # Strategy 2: Medium articles - keep but mark as large
            elif content_length <= self.max_chunk_size:
                # Keep as single chunk but it's larger than ideal
                chunked_docs.append(doc)
                logger.debug(f"Kept large article {doc.metadata.get('article_number', '?')} as single chunk ({content_length} chars)")
            
            # Strategy 3: Very large articles - must split
            else:
                logger.info(f"Splitting large article {doc.metadata.get('article_number', '?')} ({content_length} chars)")
                split_docs = self._split_large_article(doc)
                chunked_docs.extend(split_docs)
        
        logger.info(f"Chunking complete: {len(documents)} → {len(chunked_docs)} chunks")
        return chunked_docs
    
    def _split_large_article(self, doc: Document) -> List[Document]:
        """
        Split a large article into multiple chunks.
        
        Args:
            doc: Document to split
        
        Returns:
            List of split Document objects
        """
        # Use text splitter
        texts = self.text_splitter.split_text(doc.page_content)
        
        # Create new documents with updated metadata
        split_docs = []
        for i, text in enumerate(texts):
            new_metadata = doc.metadata.copy()
            new_metadata['chunk_index'] = i
            new_metadata['total_chunks'] = len(texts)
            new_metadata['is_chunked'] = True
            
            split_doc = Document(
                page_content=text,
                metadata=new_metadata
            )
            split_docs.append(split_doc)
        
        return split_docs
    
    def get_chunk_statistics(self, chunks: List[Document]) -> dict:
        """
        Get statistics about chunks.
        
        Args:
            chunks: List of chunked documents
        
        Returns:
            Statistics dictionary
        """
        chunk_sizes = [len(chunk.page_content) for chunk in chunks]
        
        chunked_count = sum(1 for c in chunks if c.metadata.get('is_chunked', False))
        
        stats = {
            "total_chunks": len(chunks),
            "chunked_articles": chunked_count,
            "single_articles": len(chunks) - chunked_count,
            "avg_chunk_size": round(sum(chunk_sizes) / len(chunk_sizes)) if chunk_sizes else 0,
            "min_chunk_size": min(chunk_sizes) if chunk_sizes else 0,
            "max_chunk_size": max(chunk_sizes) if chunk_sizes else 0,
        }
        
        return stats
