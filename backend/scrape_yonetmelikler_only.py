#!/usr/bin/env python3
"""
Sadece yönetmelikler sayfasından (hukuk.subu.edu.tr/yonetmelikler-0) PDF indirir.
Yönergeler sayfasına dokunmaz.
Kullanım: cd backend && . venv/bin/activate && python scrape_yonetmelikler_only.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.scraper.qdms_scraper import QDMSScraper

def main():
    scraper = QDMSScraper(headless=True)
    results = scraper.scrape_and_download_all(sources=["yonetmelikler"])
    print(f"\nTamamlandı: {len(results)} dosya (indirilen veya zaten mevcut)")
    return 0 if results else 1

if __name__ == "__main__":
    sys.exit(main())
