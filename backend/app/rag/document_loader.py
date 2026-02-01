"""
Document Loader - Loads processed JSON files for RAG pipeline.
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from langchain.schema import Document

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("document_loader", "./logs/document_loader.log")


class DocumentLoader:
    """
    Loads processed JSON documents and converts them to LangChain Document format.
    
    Usage:
        loader = DocumentLoader()
        documents = loader.load_all()
    """
    
    def __init__(self, json_directory: str = None):
        """
        Initialize document loader.
        
        Args:
            json_directory: Path to JSON directory (defaults to settings)
        """
        self.json_dir = Path(json_directory or settings.json_directory)
        if not self.json_dir.exists():
            raise ValueError(f"JSON directory not found: {self.json_dir}")
        
        logger.info(f"DocumentLoader initialized with directory: {self.json_dir}")
    
    def load_all(self) -> List[Document]:
        """
        Load all JSON files and convert to LangChain Documents.
        
        Returns:
            List of Document objects
        """
        json_files = list(self.json_dir.glob("*.json"))
        logger.info(f"Found {len(json_files)} JSON files to load")
        
        all_documents = []
        
        for json_file in json_files:
            try:
                docs = self.load_single(json_file)
                all_documents.extend(docs)
            except Exception as e:
                logger.error(f"Error loading {json_file.name}: {e}")
        
        logger.info(f"Loaded {len(all_documents)} total documents from {len(json_files)} files")
        return all_documents
    
    def load_single(self, json_path: Path) -> List[Document]:
        """
        Load a single JSON file and convert to Documents.
        
        Each article becomes a separate Document with metadata.
        
        Args:
            json_path: Path to JSON file
        
        Returns:
            List of Document objects
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []
        metadata_base = data['metadata']
        
        # If no articles found, treat full text as single document
        if not data['articles'] or data['articles'][0]['article_number'] == "0":
            doc = Document(
                page_content=data['full_text'],
                metadata={
                    "source": metadata_base['filename'],
                    "title": metadata_base['title'],
                    "page_count": metadata_base['page_count'],
                    "json_path": str(json_path),
                    "article_number": "full",
                    "type": "full_document"
                }
            )
            documents.append(doc)
            logger.debug(f"Loaded full document: {metadata_base['title']}")
        else:
            # Create a document for each article
            for article in data['articles']:
                # Build content with article structure
                content_parts = []
                
                # Article header
                article_header = f"MADDE {article['article_number']}"
                if article['article_title']:
                    article_header += f" - {article['article_title']}"
                content_parts.append(article_header)
                
                # Article content
                content_parts.append(article['content'])
                
                content = "\n\n".join(content_parts)
                
                # Create metadata
                metadata = {
                    "source": metadata_base['filename'],
                    "title": metadata_base['title'],
                    "page_count": metadata_base['page_count'],
                    "json_path": str(json_path),
                    "article_number": article['article_number'],
                    "article_title": article['article_title'],
                    "paragraph_count": len(article['paragraphs']),
                    "character_count": article['character_count'],
                    "type": "article"
                }
                
                doc = Document(
                    page_content=content,
                    metadata=metadata
                )
                documents.append(doc)
        
        logger.debug(f"Loaded {len(documents)} documents from {json_path.name}")
        return documents
    
    def load_by_title(self, title_pattern: str) -> List[Document]:
        """
        Load documents matching a title pattern.
        
        Args:
            title_pattern: Pattern to match in filenames
        
        Returns:
            List of matching Document objects
        """
        matching_files = list(self.json_dir.glob(f"*{title_pattern}*.json"))
        logger.info(f"Found {len(matching_files)} files matching pattern: {title_pattern}")
        
        documents = []
        for json_file in matching_files:
            try:
                docs = self.load_single(json_file)
                documents.extend(docs)
            except Exception as e:
                logger.error(f"Error loading {json_file.name}: {e}")
        
        return documents
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about loaded documents.
        
        Returns:
            Dictionary with statistics
        """
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
