"""
Web scraping module for QDMS documents
"""
from app.scraper.qdms_scraper import QDMSScraper
from app.scraper.link_tracker import LinkTracker

__all__ = ["QDMSScraper", "LinkTracker"]
