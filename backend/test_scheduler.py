#!/usr/bin/env python3
"""
Test Scheduler - Otomatik güncelleme sistemini test eder.

Bu script scheduler'ın düzgün çalışıp çalışmadığını test eder:
1. Scheduler oluşturur
2. Update job'u manuel olarak çalıştırır
3. Sonuçları raporlar

Usage:
    python test_scheduler.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.scheduler import UpdateScheduler
from app.utils.logger import setup_logger

logger = setup_logger("test_scheduler", "./logs/test_scheduler.log")


def test_scheduler():
    """Test scheduler functionality."""
    print("=" * 80)
    print("🧪 Testing Update Scheduler")
    print("=" * 80)
    print()
    
    try:
        # Create scheduler
        print("1️⃣  Creating scheduler...")
        scheduler = UpdateScheduler()
        print("   ✅ Scheduler created")
        print()
        
        # Run update job immediately
        print("2️⃣  Running update job (this may take several minutes)...")
        print("   📥 Scraping QDMS website...")
        print("   🔍 Checking for changes...")
        print("   ⚙️  Processing updates...")
        print()
        
        scheduler.run_now()
        
        print()
        print("=" * 80)
        print("✅ Test Complete!")
        print("=" * 80)
        print()
        print("📋 Check logs for details:")
        print("   - logs/test_scheduler.log")
        print("   - logs/scheduler.log")
        print()
        
        return True
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ Test Failed!")
        print("=" * 80)
        print(f"\nError: {e}")
        print("\n📋 Check logs for details:")
        print("   - logs/test_scheduler.log")
        print()
        logger.error(f"Scheduler test failed: {e}", exc_info=True)
        return False


def test_scheduler_start_stop():
    """Test scheduler start/stop."""
    print("=" * 80)
    print("🧪 Testing Scheduler Start/Stop")
    print("=" * 80)
    print()
    
    try:
        scheduler = UpdateScheduler()
        
        # Start
        print("1️⃣  Starting scheduler...")
        scheduler.start()
        print("   ✅ Scheduler started")
        
        # Check status
        jobs = scheduler.scheduler.get_jobs()
        print(f"   📋 Active jobs: {len(jobs)}")
        
        if jobs:
            next_run = jobs[0].next_run_time
            print(f"   ⏰ Next run: {next_run}")
        
        # Stop
        print("\n2️⃣  Stopping scheduler...")
        scheduler.stop()
        print("   ✅ Scheduler stopped")
        
        print("\n✅ Start/Stop test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Start/Stop test failed: {e}")
        logger.error(f"Start/stop test failed: {e}", exc_info=True)
        return False


def main():
    """Main test runner."""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║        SUBU Chatbot - Scheduler Test Suite                    ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print()
    
    tests = [
        ("Update Job Test", test_scheduler),
        ("Start/Stop Test", test_scheduler_start_stop),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} raised exception: {e}")
            results.append((name, False))
        
        print()
    
    # Summary
    print("=" * 80)
    print("📊 Test Summary")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Result: {passed}/{total} tests passed")
    print("=" * 80)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
