"""
QDMS Scraper - Extracts PDF links from SUBU law website.

This scraper:
1. Opens the QDMS webpage using Selenium
2. Waits for dynamic content to load
3. Extracts all QDMS PDF links
4. Downloads PDFs to specified directory
5. Calculates file hash for change detection
"""
import time
import hashlib
import requests
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("scraper", "./logs/scraper.log")


class QDMSScraper:
    """
    Scraper for QDMS documents from SUBU website.
    
    Usage:
        scraper = QDMSScraper()
        links = scraper.extract_qdms_links()
        for link in links:
            scraper.download_pdf(link['url'], link['title'])
    """
    
    def __init__(self, headless: bool = True):
        """
        Initialize scraper.
        
        Args:
            headless: Run browser in headless mode (no GUI)
        """
        self.headless = headless
        self.download_dir = Path(settings.download_directory)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"QDMSScraper initialized. Download directory: {self.download_dir}")
    
    def _setup_driver(self) -> webdriver.Chrome:
        """
        Setup Chrome WebDriver with options.
        
        Returns:
            Configured WebDriver instance
        """
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Performance and stability options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Disable images for faster loading (we only need links)
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        driver = webdriver.Chrome(options=chrome_options)
        logger.info("Chrome WebDriver initialized")
        return driver
    
    def extract_qdms_links(self, url: str = None) -> List[Dict[str, str]]:
        """
        Extract all QDMS PDF links from the webpage.
        
        Args:
            url: Target URL (defaults to settings.qdms_url)
        
        Returns:
            List of dictionaries with 'title', 'url', and 'text' keys
        """
        target_url = url or settings.qdms_url
        driver = None
        
        try:
            driver = self._setup_driver()
            logger.info(f"Navigating to {target_url}")
            driver.get(target_url)
            
            # Wait for page to load (adjust timeout as needed)
            wait = WebDriverWait(driver, 20)
            
            # Wait for body to be present
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            logger.info("Page loaded, waiting for dynamic content...")
            
            # Additional wait for JavaScript to render
            time.sleep(3)
            
            # Find all <a> tags
            all_links = driver.find_elements(By.TAG_NAME, "a")
            logger.info(f"Found {len(all_links)} total links on page")
            
            # Filter QDMS links
            qdms_links = []
            for link in all_links:
                try:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    
                    # Check if it's a QDMS link (contains 'qdms' in URL)
                    if href and "qdms" in href.lower():
                        # Try to extract title from link text or nearby elements
                        title = text if text else "Untitled Document"
                        
                        qdms_links.append({
                            "title": title,
                            "url": href,
                            "text": text,
                            "discovered_at": datetime.now().isoformat()
                        })
                        logger.debug(f"Found QDMS link: {title} - {href}")
                
                except Exception as e:
                    logger.warning(f"Error processing link: {e}")
                    continue
            
            logger.info(f"Extracted {len(qdms_links)} QDMS links")
            return qdms_links
        
        except TimeoutException:
            logger.error("Timeout waiting for page to load")
            return []
        
        except Exception as e:
            logger.error(f"Error extracting links: {e}", exc_info=True)
            return []
        
        finally:
            if driver:
                driver.quit()
                logger.info("WebDriver closed")
    
    def download_pdf(self, url: str, title: str) -> Optional[Dict[str, any]]:
        """
        Download PDF from URL and calculate its hash.
        
        Args:
            url: PDF URL
            title: Document title (used for filename)
        
        Returns:
            Dictionary with download info or None if failed
        """
        try:
            # Sanitize filename
            safe_filename = self._sanitize_filename(title)
            filepath = self.download_dir / f"{safe_filename}.pdf"
            
            # Check if already exists
            if filepath.exists():
                logger.info(f"File already exists: {filepath.name}")
                file_hash = self._calculate_file_hash(filepath)
                return {
                    "filepath": str(filepath),
                    "filename": filepath.name,
                    "file_hash": file_hash,
                    "file_size": filepath.stat().st_size,
                    "status": "already_exists"
                }
            
            # Download file
            logger.info(f"Downloading: {url}")
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Save to file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = filepath.stat().st_size
            file_hash = self._calculate_file_hash(filepath)
            
            logger.info(f"Downloaded: {filepath.name} ({file_size} bytes, hash: {file_hash[:16]}...)")
            
            return {
                "filepath": str(filepath),
                "filename": filepath.name,
                "file_hash": file_hash,
                "file_size": file_size,
                "status": "downloaded"
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {url}: {e}")
            return None
        
        except Exception as e:
            logger.error(f"Error downloading PDF: {e}", exc_info=True)
            return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Clean filename to be filesystem-safe.
        
        Args:
            filename: Original filename
        
        Returns:
            Safe filename
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        max_length = 200
        if len(filename) > max_length:
            filename = filename[:max_length]
        
        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')
        
        # If empty, use timestamp
        if not filename:
            filename = f"document_{int(time.time())}"
        
        return filename
    
    def _calculate_file_hash(self, filepath: Path) -> str:
        """
        Calculate SHA-256 hash of file for change detection.
        
        Args:
            filepath: Path to file
        
        Returns:
            Hex digest of file hash
        """
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def scrape_and_download_all(self) -> List[Dict[str, any]]:
        """
        Complete workflow: Extract links and download all PDFs.
        
        Returns:
            List of download results
        """
        logger.info("Starting full scrape and download workflow")
        
        # Extract links
        links = self.extract_qdms_links()
        
        if not links:
            logger.warning("No QDMS links found")
            return []
        
        logger.info(f"Found {len(links)} links, starting downloads...")
        
        # Download all PDFs
        results = []
        for i, link in enumerate(links, 1):
            logger.info(f"Processing {i}/{len(links)}: {link['title']}")
            result = self.download_pdf(link['url'], link['title'])
            
            if result:
                result['title'] = link['title']
                result['url'] = link['url']
                results.append(result)
            
            # Be polite, add small delay between downloads
            time.sleep(0.5)
        
        logger.info(f"Download complete. Successfully downloaded: {len(results)}/{len(links)}")
        return results
