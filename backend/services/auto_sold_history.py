"""Sold-history service for the vehicle detail page.

Queries our own auction_observations collection for hammer prices of
similar vehicles. When observations are empty (early days), falls back
to CURRENT listing prices of comparable available lots so the widget is
still informative — but the response distinguishes both cases.
"""
from __future__ import annotations

import re
import statistics
from typing import Any, Dict, List, Optional


def _bucket_stats(prices: List[float]) -> Dict[str, Any]:
    if not prices:
        return {}
    prices = sorted(prices)
    return {
        "count": len(prices),
        "min_nzd": round(min(prices), 0),
        "max_nzd": round(max(prices), 0),
        "median_nzd": round(statistics.median(prices), 0),
        "avg_nzd": round(sum(prices) / len(prices), 0),
    }


async def similar_sold_history(
    db,
    vehicle: Dict[str, Any],
    *,
    year_window: int = 2,
    max_observations: int = 60,
) -> Dict[str, Any]:
    """Return a compact "sold at NZ$X-Y" snapshot for the vehicle.

    Data-source rules (in order):
      1) `auction_observations` with `sold: true` for same make/model/year±N.
      2) Currently-available lots of the same make/model/year±N with
         `current_price_nzd > 0`. Flagged as `source: "current_listings"`
         so the frontend can label the range "выставлены за" (listed at)
         instead of "проданы за" (sold at).
      3) None → empty payload with `source: "insufficient"`.
    """
    make = (vehicle.get("make") or "").strip()
    model = (vehicle.get("model") or "").strip()
    year = vehicle.get("year")

    if not make or not model:
        return {"source": "insufficient", "reason": "no_make_model"}

    make_rx = {"$regex": f"^{re.escape(make)}$", "$options": "i"}
    model_rx = {"$regex": f"^{re.escape(model)}$", "$options": "i"}

    obs_query: Dict[str, Any] = {
        "sold": True,
        "make": make_rx,
        "model": model_rx,
        "observed_price_nzd": {"$gt": 0},
    }
    if year:
        obs_query["year"] = {"$gte": year - year_window, "$lte": year + year_window}

    prices: List[float] = []
    async for o in db.auction_observations.find(obs_query).limit(max_observations):
        v = o.get("observed_price_nzd")
        if isinstance(v, (int, float)) and v > 0:
            prices.append(float(v))
    if prices:
        stats = _bucket_stats(prices)
        return {
            "source": "sold_observations",
            "make": make,
            "model": model,
            "year": year,
            "year_window": year_window,
            **stats,
        }

    # Fallback — same make/model/year in the live catalog with a real price.
    live_query: Dict[str, Any] = {
        "make": make_rx,
        "model": model_rx,
        "current_price_nzd": {"$gt": 0},
        "id": {"$ne": vehicle.get("id")},
    }
    if year:
        live_query["year"] = {"$gte": year - year_window, "$lte": year + year_window}

    async for v in db.auto_vehicles.find(live_query).limit(max_observations):
        p = v.get("current_price_nzd")
        if isinstance(p, (int, float)) and p > 0:
            prices.append(float(p))
    if prices:
        stats = _bucket_stats(prices)
        return {
            "source": "current_listings",
            "make": make,
            "model": model,
            "year": year,
            "year_window": year_window,
            **stats,
        }

    return {"source": "insufficient", "make": make, "model": model, "year": year}
