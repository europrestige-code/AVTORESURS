"""
АвтоРесурс — lightweight background scheduler.

Two independent loops:
  1) Turners auctions calendar refresh — once / 24h
  2) Email campaign DRAFT generation — twice / day (morning + evening)

Both are resilient: if a single tick fails, it logs and continues. The
operator can also trigger each job manually from the admin UI.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1) Turners auctions calendar refresh — daily
# ---------------------------------------------------------------------------
AUCTIONS_REFRESH_INTERVAL_SECONDS = 24 * 60 * 60
AUCTIONS_INITIAL_DELAY_SECONDS = 60

_auc_task: Optional[asyncio.Task] = None
_last_run_at: Optional[datetime] = None
_last_result: Optional[dict] = None

# ---------------------------------------------------------------------------
# 2) Email campaign drafts — twice a day at 09:00 and 17:00 (NZ local).
#    We use a simple wait-until-next-target loop in UTC; NZ ≈ UTC+13 (NZDT).
# ---------------------------------------------------------------------------
CAMPAIGN_SLOTS_NZ = [time(9, 0), time(17, 0)]   # 09:00, 17:00 NZ local
NZ_OFFSET_HOURS = 13                              # NZDT — fine for our purposes
CAMPAIGN_INITIAL_DELAY_SECONDS = 120

_camp_task: Optional[asyncio.Task] = None
_last_camp_at: Optional[datetime] = None
_last_camp_result: Optional[dict] = None


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


def _seconds_until_next_slot() -> tuple[int, str]:
    """Return (seconds_to_wait, slot_label) for the next campaign slot.

    Uses UTC math but interprets the targets as NZ-local (UTC+13).
    """
    now_utc = datetime.now(timezone.utc)
    candidates = []
    for nz_t in CAMPAIGN_SLOTS_NZ:
        target_utc_hour = (nz_t.hour - NZ_OFFSET_HOURS) % 24
        target = now_utc.replace(hour=target_utc_hour, minute=nz_t.minute, second=0, microsecond=0)
        if target <= now_utc:
            target = target + timedelta(days=1)
        slot = "morning" if nz_t.hour < 12 else "evening"
        candidates.append((target, slot))
    candidates.sort(key=lambda x: x[0])
    nxt, label = candidates[0]
    return max(1, int((nxt - now_utc).total_seconds())), label


async def _campaign_loop(db) -> None:
    global _last_camp_at, _last_camp_result
    from services.auto_email_service import generate_campaign_draft
    await asyncio.sleep(CAMPAIGN_INITIAL_DELAY_SECONDS)
    while True:
        wait_s, slot = _seconds_until_next_slot()
        logger.info(f"[scheduler] next campaign slot: {slot} in {wait_s}s")
        try:
            await asyncio.sleep(wait_s)
        except asyncio.CancelledError:
            raise
        try:
            camp = await generate_campaign_draft(db, slot=slot)
            _last_camp_at = datetime.utcnow()
            _last_camp_result = {
                "slot": slot,
                "campaign_id": getattr(camp, "id", None),
                "vehicles": len(camp.vehicles) if camp else 0,
                "recipient_count": camp.recipient_count if camp else 0,
            }
            logger.info(f"[scheduler] campaign draft created: {_last_camp_result}")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning(f"[scheduler] campaign generation failed: {e}")
            _last_camp_result = {"slot": slot, "error": str(e)}


def start(db) -> None:
    """Start both background loops. Safe to call once at startup."""
    global _auc_task, _camp_task, _intel_task
    loop = asyncio.get_event_loop()
    if not _auc_task or _auc_task.done():
        _auc_task = loop.create_task(_refresh_loop(db), name="auto-auctions-refresh")
        logger.info("[scheduler] started auctions calendar refresh task")
    if not _camp_task or _camp_task.done():
        _camp_task = loop.create_task(_campaign_loop(db), name="auto-email-campaigns")
        logger.info("[scheduler] started email-campaigns task (2x/day)")
    if not _intel_task or _intel_task.done():
        _intel_task = loop.create_task(_intel_loop(db), name="auto-intel-estimates")
        logger.info("[scheduler] started AI-estimate generator (hourly)")


_intel_task = None


async def _intel_loop(db) -> None:
    """Hourly: generate AI estimates for any vehicles without one. Each run
    handles at most 20 to stay under the LLM rate-limit and the budget."""
    while True:
        try:
            from services.auto_intel_engine import estimate_for_vehicle
            cursor = db.auto_vehicles.find(
                {"status": {"$ne": "hidden"}, "ai_estimate": {"$exists": False}}
            ).limit(20)
            done = 0
            async for v in cursor:
                try:
                    await estimate_for_vehicle(db, v)
                    done += 1
                except Exception:
                    pass
            if done:
                logger.info(f"[scheduler] AI estimates generated: {done}")
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.warning(f"[scheduler] AI estimate loop failed: {e}")
        await asyncio.sleep(3600)  # 1 hour


def stop() -> None:
    global _auc_task, _camp_task
    for t in (_auc_task, _camp_task):
        if t and not t.done():
            t.cancel()


def status() -> dict:
    return {
        "auctions": {
            "running": bool(_auc_task and not _auc_task.done()),
            "interval_seconds": AUCTIONS_REFRESH_INTERVAL_SECONDS,
            "last_run_at": _last_run_at.isoformat() if _last_run_at else None,
            "last_result": _last_result,
        },
        "campaigns": {
            "running": bool(_camp_task and not _camp_task.done()),
            "slots_nz_local": [t.strftime("%H:%M") for t in CAMPAIGN_SLOTS_NZ],
            "last_run_at": _last_camp_at.isoformat() if _last_camp_at else None,
            "last_result": _last_camp_result,
        },
    }
