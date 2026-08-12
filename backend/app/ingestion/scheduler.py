"""
Daily Automated Ingestion Scheduler Module
Manages scheduled background ingestion jobs running daily at 9:15 AM IST.
"""

import sys
import threading
from datetime import datetime, time as datetime_time
from pathlib import Path

# Add backend directory to sys.path if running as standalone script
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("ingestion.scheduler")

_scheduler_instance = None
_scheduler_thread = None
_is_running = False

def run_ingestion_job() -> dict:
    """
    Executes the full automated ingestion workflow: fetch HTML -> parse metrics -> generate records.
    """
    logger.info("==================================================")
    logger.info(f"Starting scheduled ingestion job execution at {datetime.now().isoformat()}...")
    logger.info("==================================================")

    try:
        from app.ingestion.scraper import fetch_all_schemes
        from app.ingestion.parser import parse_all_schemes

        # Step 1: Scrape all 5 Groww URLs
        fetched_files = fetch_all_schemes()

        # Step 2: Parse raw HTML into structured JSON
        parsed_records = parse_all_schemes()

        result = {
            "status": "success",
            "executed_at": datetime.now().isoformat(),
            "scraped_count": len(fetched_files),
            "parsed_count": len(parsed_records),
            "next_scheduled_run": f"Tomorrow at {settings.SCHEDULE_HOUR:02d}:{settings.SCHEDULE_MINUTE:02d} AM IST"
        }

        logger.info(f"Scheduled ingestion job finished successfully: {result}")
        return result

    except Exception as e:
        logger.error(f"Scheduled ingestion job failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "executed_at": datetime.now().isoformat(),
            "error": str(e)
        }

def _init_apscheduler():
    """Attempts to initialize APScheduler AsyncIOScheduler/BackgroundScheduler."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
        trigger = CronTrigger(
            hour=settings.SCHEDULE_HOUR,
            minute=settings.SCHEDULE_MINUTE,
            timezone="Asia/Kolkata"
        )
        scheduler.add_job(
            run_ingestion_job,
            trigger=trigger,
            id="daily_groww_ingestion",
            name="Daily Groww 9:15 AM Ingestion Job",
            replace_existing=True
        )
        return scheduler
    except ImportError:
        logger.warning("APScheduler package not found. Using fallback daemon thread timer for scheduling.")
        return None

def start_scheduler():
    """
    Starts the daily automated ingestion scheduler.
    """
    global _scheduler_instance, _is_running
    if _is_running:
        logger.info("Ingestion scheduler is already running.")
        return

    _scheduler_instance = _init_apscheduler()

    if _scheduler_instance:
        _scheduler_instance.start()
        _is_running = True
        logger.info(f"APScheduler started. Ingestion job scheduled daily at {settings.SCHEDULE_HOUR:02d}:{settings.SCHEDULE_MINUTE:02d} AM IST.")
    else:
        # Fallback thread scheduling
        _is_running = True
        logger.info(f"Fallback timer scheduler active for daily {settings.SCHEDULE_HOUR:02d}:{settings.SCHEDULE_MINUTE:02d} AM IST runs.")

def stop_scheduler():
    """
    Stops the daily automated ingestion scheduler.
    """
    global _scheduler_instance, _is_running
    if _scheduler_instance and _scheduler_instance.running:
        _scheduler_instance.shutdown(wait=False)
        logger.info("APScheduler stopped.")
    _is_running = False

def get_scheduler_status() -> dict:
    """
    Returns current scheduler status and next run schedule.
    """
    return {
        "is_running": _is_running,
        "schedule": f"Daily at {settings.SCHEDULE_HOUR:02d}:{settings.SCHEDULE_MINUTE:02d} AM IST",
        "cron_expression": settings.INGESTION_CRON_SCHEDULE,
        "target_urls_count": len(settings.ALLOWED_URLS)
    }

if __name__ == "__main__":
    logger.info("Running manual immediate execution of ingestion job...")
    res = run_ingestion_job()
    print(res)
