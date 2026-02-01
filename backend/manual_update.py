#!/usr/bin/env python3
"""
Manual Update Script - Güncellemeleri manuel olarak çalıştırır.

Bu script scheduler beklemeden hemen güncelleme yapar:
1. QDMS'den PDF'leri çeker
2. Değişiklikleri kontrol eder
3. Değişen dosyaları işler
4. Vector store'u günceller

Usage:
    python manual_update.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.scheduler import UpdateScheduler
from app.utils.logger import setup_logger

logger = setup_logger("manual_update", "./logs/manual_update.log")


def main():
    """Run manual update."""
    print("=" * 80)
    print("🔄 Manual Update - SUBU Mevzuat Chatbot")
    print("=" * 80)
    print()
    print("Bu işlem birkaç dakika sürebilir...")
    print()
    
    try:
        # Create scheduler
        scheduler = UpdateScheduler()
        
        # Run update immediately
        print("▶️  Güncelleme başlatıldı...")
        print()
        scheduler.run_now()
        print()
        print("=" * 80)
        print("✅ Güncelleme tamamlandı!")
        print("=" * 80)
        print()
        print("📋 Detaylar için log dosyasını kontrol edin:")
        print("   logs/scheduler.log")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ Güncelleme başarısız!")
        print("=" * 80)
        print()
        print(f"Hata: {e}")
        print()
        print("📋 Detaylar için log dosyasını kontrol edin:")
        print("   logs/manual_update.log")
        print("   logs/scheduler.log")
        print()
        logger.error(f"Manual update failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
