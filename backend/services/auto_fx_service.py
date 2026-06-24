"""
АвтоРесурс — live NZD → RUB FX with a 3% "convenience" markup.

We fetch the spot mid-market rate from a free public source
(https://open.er-api.com — no key required) once an hour, cache it in-process,
and apply a +3% markup so the public RUB price shown to Russian buyers covers
our currency-conversion overhead. Same structure as the legacy buyanywhere.ru
currency engine.

Public API:
    await get_fx_rate()           → {nzd_to_rub_spot, nzd_to_rub_display, ...}
    await nzd_to_rub(amount_nzd)  → float (display RUB)
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Dict, Optional

import httpx

log = logging.getLogger("auto.fx")

CONVENIENCE_MARKUP = 0.03   # +3% over Google/spot rate
CACHE_TTL_SEC = 60 * 60      # 1 hour
PROVIDER_URL = "https://open.er-api.com/v6/latest/NZD"

# Fallback used when the provider is unreachable. Tuned to mid-2026 levels.
FALLBACK_NZD_TO_RUB = 56.0

_lock = asyncio.Lock()
_cache: Dict[str, float | str] = {}
_cache_at: float = 0.0


async def _fetch_remote() -> Optional[Dict[str, float]]:
    try:
        async with httpx.AsyncClient(timeout=8.0) as c:
            r = await c.get(PROVIDER_URL)
            r.raise_for_status()
            data = r.json()
            rates = data.get("rates") or {}
            rub = rates.get("RUB")
            usd = rates.get("USD")
            eur = rates.get("EUR")
            if not rub:
                return None
            return {
                "nzd_to_rub_spot": float(rub),
                "nzd_to_usd": float(usd or 0.6),
                "nzd_to_eur": float(eur or 0.55),
            }
    except Exception as e:                                    # noqa: BLE001
        log.warning("FX fetch failed: %s", e)
        return None


async def get_fx_rate(force_refresh: bool = False) -> Dict[str, float | str]:
    """Return current rates with caching.

    Output keys:
        nzd_to_rub_spot     — raw mid-market rate
        nzd_to_rub_display  — what the public website applies (spot × 1.03)
        markup_pct          — convenience markup (0.03)
        source              — provider URL or "fallback"
        fetched_at          — unix ts
    """
    global _cache_at, _cache
    async with _lock:
        now = time.time()
        if (not force_refresh) and _cache and (now - _cache_at) < CACHE_TTL_SEC:
            return dict(_cache)
        remote = await _fetch_remote()
        if remote:
            spot = remote["nzd_to_rub_spot"]
            _cache = {
                **remote,
                "nzd_to_rub_display": round(spot * (1 + CONVENIENCE_MARKUP), 6),
                "markup_pct": CONVENIENCE_MARKUP,
                "source": PROVIDER_URL,
                "fetched_at": int(now),
            }
        else:
            _cache = {
                "nzd_to_rub_spot": FALLBACK_NZD_TO_RUB,
                "nzd_to_rub_display": round(FALLBACK_NZD_TO_RUB * (1 + CONVENIENCE_MARKUP), 6),
                "nzd_to_usd": 0.6,
                "nzd_to_eur": 0.55,
                "markup_pct": CONVENIENCE_MARKUP,
                "source": "fallback",
                "fetched_at": int(now),
            }
        _cache_at = now
        return dict(_cache)


async def nzd_to_rub(amount_nzd: float) -> float:
    """Convert NZD → RUB using the cached display rate."""
    if amount_nzd is None:
        return 0.0
    rate = (await get_fx_rate())["nzd_to_rub_display"]
    return float(amount_nzd) * float(rate)
