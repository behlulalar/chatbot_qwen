"""
Run FastAPI server with scheduler.

This script:
1. Starts FastAPI server
2. Starts background scheduler for updates
3. Keeps both running

Usage:
    python run_server.py
"""
import sys
from pathlib import Path
import signal

sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from app.config import settings
from app.scheduler import UpdateScheduler
from app.utils.logger import setup_logger

logger = setup_logger("server", "./logs/server.log")

# Global scheduler instance
scheduler = None


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info("Shutdown signal received")
    if scheduler:
        scheduler.stop()
    sys.exit(0)


def main():
    """Main server runner."""
    global scheduler
    
    print("=" * 80)
    print(f"🚀 {settings.app_name} v{settings.app_version}")
    print("=" * 80)
    port = getattr(settings, "port", 8000)
    print(f"\n📍 API Server: http://localhost:{port}")
    print(f"📖 API Docs: http://localhost:{port}/docs")
    print(f"⏰ Update Interval: {settings.update_interval} hours")
    print(f"\n⚠️  Press Ctrl+C to stop\n")
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start scheduler
    try:
        logger.info("Starting update scheduler...")
        scheduler = UpdateScheduler()
        scheduler.start()
        print("✅ Scheduler started")
        print(f"   Next update: {scheduler.scheduler.get_jobs()[0].next_run_time if scheduler.scheduler.get_jobs() else 'N/A'}")
        
        # Optional: Run update job immediately on startup
        # Useful for checking updates when server starts
        # Uncomment to enable:
        # print("\n🔄 Running initial update check...")
        # scheduler.run_now()
        # print("✅ Initial update complete")
        
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}", exc_info=True)
        print(f"⚠️ Scheduler not started: {e}")
    
    # Start FastAPI server
    try:
        logger.info("Starting FastAPI server...")
        print("✅ API Server starting...\n")
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            reload=settings.debug,
            log_level="info"
        )
    
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        if scheduler:
            scheduler.stop()
        raise


if __name__ == "__main__":
    main()
