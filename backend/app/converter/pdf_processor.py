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
    
    def process_pdf(self, pdf_path: str, title: Optional[str] = None) -> Dict:
        """
        Process a single PDF file.
        
        Args:
            pdf_path: Path to PDF file
            title: Document title (optional)
        
        Returns:
            Dictionary with structured document data
        """
        path = Path(pdf_path)
        
        if not path.exists():
            logger.error(f"PDF file not found: {path}")
            raise FileNotFoundError(f"PDF file not found: {path}")
        
        logger.info(f"Processing PDF: {path.name}")
        
        try:
            # Open PDF
            doc = fitz.open(path)
            
            # Extract metadata
            metadata = self._extract_metadata(doc, path, title)
            
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
            
            full_text = self._clean_text(full_text, doc_title=metadata["title"])
            
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
            logger.error(f"Error processing PDF {path}: {e}", exc_info=True)
            raise
    
    def _extract_metadata(self, doc: fitz.Document, pdf_path: Path, title: Optional[str] = None) -> Dict:
        """
        Extract metadata from PDF.
        
        Args:
            doc: PyMuPDF document object
            pdf_path: Path to PDF file
            title: Override title
        
        Returns:
            Metadata dictionary
        """
        pdf_metadata = doc.metadata or {}
        
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

    def _clean_text(self, text: str, doc_title: Optional[str] = None) -> str:
        """
        PDF'den çekilen metni temizle:
        - QDMS header/footer bloklarını tamamen kaldır
        - Doküman başlığı tekrarlarını kaldır
        - Sayfa geçişlerindeki gereksiz boşluk/satırları birleştir
        """
        lines = text.split('\n')
        lines_to_remove: set = set()

        _qdms_patterns = [
            re.compile(r'Doküman No\s*:', re.IGNORECASE),
            re.compile(r'Revizyon Tarihi\s*:', re.IGNORECASE),
            re.compile(r'Revizyon No\s*:', re.IGNORECASE),
            re.compile(r'İlk Yayın Tarihi\s*:', re.IGNORECASE),
            re.compile(r'Sayfa\s*:\s*\d+\s*/\s*\d+', re.IGNORECASE),
            re.compile(r'^\s*\d+\s*/\s*\d+\s*$'),
            re.compile(r'KYS\.\w+\.\d+'),
            re.compile(r'^\s*\d{2}\.\d{2}\.\d{4}\s*$'),
            re.compile(r'^\s*\d{1,2}\s*$'),
            re.compile(r'^\s*Sayfa\s*:?\s*$', re.IGNORECASE),
        ]

        for i, line in enumerate(lines):
            for pat in _qdms_patterns:
                if pat.search(line):
                    lines_to_remove.add(i)
                    break

        if doc_title and len(doc_title) > 8:
            title_upper = re.sub(r'\s+', ' ', doc_title.strip()).upper()
            title_norm = re.sub(r'[^\w\s]', '', title_upper)
            title_words = set(title_norm.split())
            for i, line in enumerate(lines):
                if i in lines_to_remove:
                    continue
                s = line.strip()
                if not s or len(s) < 8:
                    continue
                s_upper = re.sub(r'\s+', ' ', s).upper()
                s_norm = re.sub(r'[^\w\s]', '', s_upper)
                s_words = set(s_norm.split())

                is_exact = (s_norm == title_norm)
                is_contained = (
                    len(title_norm) > 15
                    and title_norm in s_norm
                    and len(s) < len(doc_title) + 30
                )
                is_fuzzy = (
                    len(s_words) >= 3
                    and len(s_words) <= len(title_words) + 3
                    and len(s_words & title_words) >= len(title_words) * 0.7
                    and re.match(r'^[A-ZÇĞİÖŞÜ\s,\-–()/]+$', s)
                )

                if is_exact or is_contained or is_fuzzy:
                    lines_to_remove.add(i)

        for i, line in enumerate(lines):
            if i in lines_to_remove:
                continue
            s = line.strip()
            if not s or len(s) > 100 or len(s) < 8:
                continue
            if not re.match(r'^[A-ZÇĞİÖŞÜ\s,\-–()/\d]+$', s):
                continue
            following_removed = sum(
                1 for j in range(i + 1, min(len(lines), i + 6))
                if j in lines_to_remove
            )
            if following_removed < 2:
                continue
            next_content = None
            for j in range(i + 1, min(len(lines), i + 4)):
                if j not in lines_to_remove and lines[j].strip():
                    next_content = lines[j].strip()
                    break
            if next_content and re.match(
                r'(?:MADDE|Madde|MD\.|ARTICLE)', next_content, re.IGNORECASE
            ):
                continue
            lines_to_remove.add(i)

        cleaned_lines = [
            line for i, line in enumerate(lines) if i not in lines_to_remove
        ]
        cleaned = '\n'.join(cleaned_lines)
        cleaned = re.sub(r'[ \t]+\n', '\n', cleaned)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

        return cleaned

    @staticmethod
    def _is_valid_article_title(text: str) -> bool:
        """Pre-MADDE satırının gerçek bir başlık mı yoksa içerik sızması mı olduğunu belirle."""
        if not text:
            return False
        t = text.strip()
        if len(t) > 70:
            return False
        if t[-1] in '.,:;)':
            return False
        if re.search(r'\(\d+\)', t):
            return False
        if t[0].islower():
            return False
        return True

    def _parse_articles(self, text: str) -> List[Dict]:
        """
        Parse document structure (madde, fıkra, bent).

        - MADDE X / Madde X / ARTICLE X: Main articles
        - (1), (2): Fıkra (paragraphs)
        - a), b), c): Bent (sub-items)
        """
        articles = []

        ek_pattern = r'\n\s*EK[-\s]*\d+.*$'
        text = re.split(ek_pattern, text, maxsplit=1, flags=re.MULTILINE)[0]

        article_pattern = (
            r'(?:([A-ZÇĞİÖŞÜa-zçğıöşü][^\n]{2,80})\n\s*)?'
            r'(?:MADDE|Madde|MD\.|Md\.|ARTICLE|Article)\s*(\d+)\s*[-:–—]?\s*([^\n]+)?'
        )
        matches = list(re.finditer(article_pattern, text, re.IGNORECASE | re.MULTILINE))

        if not matches:
            logger.warning("No article structure detected. Treating as single document.")
            return [{
                "article_number": "0",
                "article_title": "Full Document",
                "content": text.strip(),
                "paragraphs": self._parse_paragraphs(text),
                "character_count": len(text)
            }]

        for i, match in enumerate(matches):
            article_num = match.group(2)
            pre_title = match.group(1).strip() if match.group(1) else ""
            inline_title = match.group(3).strip() if match.group(3) else ""

            if pre_title and self._is_valid_article_title(pre_title):
                article_title = pre_title
            elif inline_title and not inline_title.startswith("(") and not re.match(r'^\d+\)', inline_title):
                article_title = inline_title[:70]
            else:
                article_title = ""

            inline_is_content = (
                inline_title
                and (inline_title.startswith("(") or re.match(r'^\d+\)', inline_title))
            )

            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            raw_content = text[start_pos:end_pos].strip()

            if inline_is_content:
                content = inline_title + "\n" + raw_content if raw_content else inline_title
            else:
                content = raw_content

            paragraphs = self._parse_paragraphs(content)

            article = {
                "article_number": article_num,
                "article_title": article_title,
                "content": content,
                "paragraphs": paragraphs,
                "character_count": len(content)
            }

            articles.append(article)
            logger.debug(f"Parsed Article {article_num}: {len(paragraphs)} paragraphs, {len(content)} chars")

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
    
    def save_json(self, data: Dict, output_filename: Optional[str] = None) -> str:
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
    
    def process_batch(self, pdf_paths: List[str], titles: Optional[List[Optional[str]]] = None) -> List[Dict]:
        """
        Process multiple PDFs in batch.
        
        Args:
            pdf_paths: List of PDF file paths
            titles: List of titles (optional)
        
        Returns:
            List of results with status
        """
        results = []
        titles_list: List[Optional[str]] = titles if titles is not None else [None] * len(pdf_paths)
        
        logger.info(f"Starting batch processing: {len(pdf_paths)} PDFs")
        
        for i, (pdf_path, title) in enumerate(zip(pdf_paths, titles_list), 1):
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
