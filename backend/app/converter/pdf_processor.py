"""
PDF Processor - Converts PDF documents to structured JSON.

This processor:
1. Extracts text from PDFs using PyMuPDF
2. Detects document structure (madde, fıkra, bent)
3. Extracts metadata
4. Converts to structured JSON format
"""
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import fitz  # PyMuPDF
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("pdf_processor", "./logs/pdf_processor.log")


class PDFProcessor:
    """
    Process PDF files and convert to structured JSON.
    
    Usage:
        processor = PDFProcessor()
        result = processor.process_pdf("path/to/file.pdf")
        processor.save_json(result, "output.json")
    """
    
    def __init__(self):
        """Initialize PDF processor."""
        self.json_dir = Path(settings.json_directory)
        self.json_dir.mkdir(parents=True, exist_ok=True)
        logger.info("PDFProcessor initialized")
    
    def process_pdf(self, pdf_path: str, title: str = None) -> Dict:
        """
        Process a single PDF file.
        
        Args:
            pdf_path: Path to PDF file
            title: Document title (optional)
        
        Returns:
            Dictionary with structured document data
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Processing PDF: {pdf_path.name}")
        
        try:
            # Open PDF
            doc = fitz.open(pdf_path)
            
            # Extract metadata
            metadata = self._extract_metadata(doc, pdf_path, title)
            
            # Extract text from all pages
            full_text = ""
            page_texts = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                page_texts.append({
                    "page_number": page_num + 1,
                    "text": text
                })
                full_text += f"\n{text}"
            
            doc.close()
            
            # Parse document structure
            articles = self._parse_articles(full_text)
            
            # Build result
            result = {
                "metadata": metadata,
                "full_text": full_text.strip(),
                "page_texts": page_texts,
                "articles": articles,
                "statistics": {
                    "total_pages": len(page_texts),
                    "total_articles": len(articles),
                    "total_characters": len(full_text),
                    "processed_at": datetime.now().isoformat()
                }
            }
            
            logger.info(f"✅ Processed: {metadata['title']} - {len(articles)} articles found")
            return result
        
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}", exc_info=True)
            raise
    
    def _extract_metadata(self, doc: fitz.Document, pdf_path: Path, title: str = None) -> Dict:
        """
        Extract metadata from PDF.
        
        Args:
            doc: PyMuPDF document object
            pdf_path: Path to PDF file
            title: Override title
        
        Returns:
            Metadata dictionary
        """
        pdf_metadata = doc.metadata
        
        metadata = {
            "title": title or pdf_metadata.get("title") or pdf_path.stem,
            "filename": pdf_path.name,
            "filepath": str(pdf_path),
            "author": pdf_metadata.get("author", ""),
            "subject": pdf_metadata.get("subject", ""),
            "keywords": pdf_metadata.get("keywords", ""),
            "creator": pdf_metadata.get("creator", ""),
            "producer": pdf_metadata.get("producer", ""),
            "creation_date": pdf_metadata.get("creationDate", ""),
            "modification_date": pdf_metadata.get("modDate", ""),
            "page_count": len(doc)
        }
        
        return metadata
    
    def _parse_articles(self, text: str) -> List[Dict]:
        """
        Parse document structure (madde, fıkra, bent).
        
        This uses regex patterns to detect Turkish and English legal document structure:
        - MADDE X / Madde X / ARTICLE X: Main articles
        - (1), (2): Fıkra (paragraphs)
        - a), b), c): Bent (sub-items)
        
        Args:
            text: Full document text
        
        Returns:
            List of article dictionaries
        """
        articles = []
        
        # Pattern to match articles (case insensitive)
        # Matches: "MADDE 5", "Madde 5", "Md. 5", "ARTICLE 5", "Article 5"
        article_pattern = r'(?:MADDE|Madde|MD\.|Md\.|ARTICLE|Article)\s*(\d+)\s*[-:–—]?\s*([^\n]+)?'
        
        # Find all article matches
        matches = list(re.finditer(article_pattern, text, re.IGNORECASE | re.MULTILINE))
        
        if not matches:
            # No articles found - treat entire text as single document
            logger.warning("No article structure detected. Treating as single document.")
            return [{
                "article_number": "0",
                "article_title": "Full Document",
                "content": text.strip(),
                "paragraphs": self._parse_paragraphs(text),
                "character_count": len(text)
            }]
        
        # Process each article
        for i, match in enumerate(matches):
            article_num = match.group(1)
            article_title = match.group(2).strip() if match.group(2) else ""
            
            # Get content between this article and next article (or end)
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start_pos:end_pos].strip()
            
            # Parse paragraphs within this article
            paragraphs = self._parse_paragraphs(content)
            
            article = {
                "article_number": article_num,
                "article_title": article_title,
                "content": content,
                "paragraphs": paragraphs,
                "character_count": len(content)
            }
            
            articles.append(article)
            logger.debug(f"Parsed Article {article_num}: {len(paragraphs)} paragraphs")
        
        return articles
    
    def _parse_paragraphs(self, text: str) -> List[Dict]:
        """
        Parse paragraphs (fıkra) and sub-items (bent).
        
        Args:
            text: Article content text
        
        Returns:
            List of paragraph dictionaries
        """
        paragraphs = []
        
        # Pattern for numbered paragraphs: (1), (2), etc.
        para_pattern = r'\((\d+)\)\s*([^\(]+?)(?=\(\d+\)|$)'
        para_matches = list(re.finditer(para_pattern, text, re.DOTALL))
        
        if not para_matches:
            # No explicit paragraphs - treat as single paragraph
            return [{
                "paragraph_number": "1",
                "content": text.strip(),
                "sub_items": self._parse_sub_items(text)
            }]
        
        for match in para_matches:
            para_num = match.group(1)
            para_content = match.group(2).strip()
            
            # Parse sub-items (bent) within paragraph
            sub_items = self._parse_sub_items(para_content)
            
            paragraph = {
                "paragraph_number": para_num,
                "content": para_content,
                "sub_items": sub_items
            }
            
            paragraphs.append(paragraph)
        
        return paragraphs
    
    def _parse_sub_items(self, text: str) -> List[Dict]:
        """
        Parse sub-items (bent): a), b), c) or 1), 2), 3).
        
        Args:
            text: Paragraph content text
        
        Returns:
            List of sub-item dictionaries
        """
        sub_items = []
        
        # Pattern for lettered sub-items: a), b), c) with proper content capture
        # Matches: "a) text" or "1) text" until next item or newline
        sub_pattern = r'\n([a-zğüşıöçA-ZĞÜŞIÖÇ]|\d+)\)\s+([^\n]+?)(?=\n[a-zğüşıöçA-ZĞÜŞIÖÇ]|\d+\)|\n\n|$)'
        sub_matches = list(re.finditer(sub_pattern, text, re.MULTILINE | re.DOTALL))
        
        if not sub_matches:
            return []
        
        for match in sub_matches:
            sub_id = match.group(1)
            sub_content = match.group(2).strip()
            
            sub_item = {
                "sub_item_id": sub_id,
                "content": sub_content
            }
            
            sub_items.append(sub_item)
        
        return sub_items
    
    def save_json(self, data: Dict, output_filename: str = None) -> str:
        """
        Save processed data to JSON file.
        
        Args:
            data: Processed document data
            output_filename: Output filename (auto-generated if not provided)
        
        Returns:
            Path to saved JSON file
        """
        if not output_filename:
            # Generate filename from title
            title = data["metadata"]["title"]
            safe_title = re.sub(r'[^\w\s-]', '', title)
            safe_title = re.sub(r'[-\s]+', '_', safe_title)
            output_filename = f"{safe_title}.json"
        
        output_path = self.json_dir / output_filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Saved JSON: {output_path}")
            return str(output_path)
        
        except Exception as e:
            logger.error(f"Error saving JSON: {e}", exc_info=True)
            raise
    
    def process_batch(self, pdf_paths: List[str], titles: List[str] = None) -> List[Dict]:
        """
        Process multiple PDFs in batch.
        
        Args:
            pdf_paths: List of PDF file paths
            titles: List of titles (optional)
        
        Returns:
            List of results with status
        """
        results = []
        titles = titles or [None] * len(pdf_paths)
        
        logger.info(f"Starting batch processing: {len(pdf_paths)} PDFs")
        
        for i, (pdf_path, title) in enumerate(zip(pdf_paths, titles), 1):
            logger.info(f"Processing {i}/{len(pdf_paths)}: {Path(pdf_path).name}")
            
            try:
                # Process PDF
                data = self.process_pdf(pdf_path, title)
                
                # Save JSON
                json_path = self.save_json(data)
                
                results.append({
                    "pdf_path": pdf_path,
                    "json_path": json_path,
                    "status": "success",
                    "article_count": len(data["articles"]),
                    "page_count": data["statistics"]["total_pages"]
                })
            
            except Exception as e:
                logger.error(f"Failed to process {pdf_path}: {e}")
                results.append({
                    "pdf_path": pdf_path,
                    "json_path": None,
                    "status": "failed",
                    "error": str(e)
                })
        
        success_count = sum(1 for r in results if r["status"] == "success")
        logger.info(f"Batch processing complete: {success_count}/{len(pdf_paths)} successful")
        
        return results
