"""
Quick check: How many documents are on the website?
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.scraper import QDMSScraper

# Create scraper
scraper = QDMSScraper(headless=True)

print("🔍 Checking website: https://hukuk.subu.edu.tr/yonergeler")
print("⏳ Scraping links...\n")

# Extract links
links = scraper.extract_qdms_links()

print(f"✅ Toplam link sayısı: {len(links)}")
print(f"📁 Bizde olan PDF: 77")
print(f"📊 Fark: {len(links) - 77}")

if len(links) > 77:
    print(f"\n⚠️  Websitesinde {len(links) - 77} yeni doküman var!")
else:
    print(f"\n✅ Tüm dokümanlar güncel!")

print("\n📋 İlk 10 link:")
for i, link_data in enumerate(links[:10], 1):
    print(f"  {i}. {link_data['title'][:60]}...")

scraper.driver.quit()
