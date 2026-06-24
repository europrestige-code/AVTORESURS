"""
АвтоРесурс — lightweight background scheduler.

Spawns a single asyncio task on app startup that periodically refreshes the
Turners auctions calendar. We deliberately avoid heavy dependencies
(APScheduler / Celery): a sleep-and-run loop is enough for one job a day.

The task is resilient: if a single refresh fails, it logs and continues.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# How often to refresh the Turners calendar. 24h is more than enough — the
# operator can also click "Обновить из Turners" in the admin UI any time.
AUCTIONS_REFRESH_INTERVAL_SECONDS = 24 * 60 * 60
AUCTIONS_INITIAL_DELAY_SECONDS = 60  # don't hit the network during startup spike

# Module-level handle so we can cancel during shutdown if needed.
_task: Optional[asyncio.Task] = None
_last_run_at: Optional[datetime] = None
_last_result: Optional[dict] = None


async def _refresh_loop(db) -> None:
    global _last_run_at, _last_result
    from services.auto_auctions_service import AuctionCalendarService
    svc = AuctionCalendarService(db)
    await asyncio.sleep(AUCTIONS_INITIAL_DELAY_SECONDS)
    while True:
        try:
            logger.info("[scheduler] Refreshing Turners auctions calendar…")
            result = await svc.refresh(categories=["cars"])
            _last_run_at = datetime.utcnow()
            _last_result = result
            logger.info(f"[scheduler] Calendar refresh: {result.get('fetched', 0)} events")
        except asyncio.CancelledError:
            logger.info("[scheduler] cancelled")
            raise
        except Exception as e:
            logger.warning(f"[scheduler] Calendar refresh failed: {e}")
        try:
            await asyncio.sleep(AUCTIONS_REFRESH_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            raise


def start(db) -> None:
    """Start the background scheduler. Safe to call once at startup."""
    global _task
    if _task and not _task.done():
        logger.info("[scheduler] already running; skipping start")
        return
    loop = asyncio.get_event_loop()
    _task = loop.create_task(_refresh_loop(db), name="auto-auctions-refresh")
    logger.info("[scheduler] started auctions calendar refresh task")


def stop() -> None:
    global _task
    if _task and not _task.done():
        _task.cancel()


def status() -> dict:
    return {
        "running": bool(_task and not _task.done()),
        "interval_seconds": AUCTIONS_REFRESH_INTERVAL_SECONDS,
        "last_run_at": _last_run_at.isoformat() if _last_run_at else None,
        "last_result": _last_result,
    }
