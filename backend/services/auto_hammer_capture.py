"""Hammer-price capture — infers "sold" observations from the catalog.

Turners / Manheim / Pickles don't expose public post-auction hammer-price
pages we can crawl. Instead we treat our own hourly importer as the sensor:

  • Every scrape re-touches `last_sync_time` on lots that are still live.
  • Lots that stop re-appearing for `stale_hours` have almost certainly
    ended (sold or passed in).  We record their LAST-observed price into
    `auction_observations` with `sold=True` (assumed) so the
    `similar_sold_history` widget starts serving real hammer ranges
    instead of falling back to current listings.

The heuristic is intentionally conservative:
  - stale_hours defaults to 48 h  (Turners auctions run daily; a 2-day
    absence is much longer than the normal sync gap).
  - only priced lots are captured (skip inquiry-only rows and rows the
    scraper never got a bid off).
  - once a lot has been captured we bump its `status → sold` so we
    don't double-count it on subsequent sweeps.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from models.auto_intelligence import AuctionObservation


async def sweep_stale_as_sold(
    db,
    source: str,
    *,
    stale_hours: int = 48,
    active_window_days: int = 5,
    max_rows: int = 500,
) -> Dict[str, int]:
    """Convert stale `available` lots from `source` into `sold` observations.

    We only accept a lot as "recently-active-then-vanished" — i.e. its
    `last_sync_time` sits in the window `[now - active_window_days,
    now - stale_hours]`. This filters out one-off big-batch imports whose
    rows have simply never been re-touched by the paginated hourly scrape.

    Returns {inspected, captured, marked_sold}.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    stale_cut = now - timedelta(hours=int(stale_hours))
    active_cut = now - timedelta(days=int(active_window_days))

    query: Dict[str, Any] = {
        "source": source,
        "status": "available",
        "current_price_nzd": {"$gt": 0},
        "last_sync_time": {"$lt": stale_cut, "$gte": active_cut},
    }

    inspected = 0
    captured = 0
    marked = 0
    to_mark: List[str] = []
    docs = db.auto_vehicles.find(query).limit(int(max_rows))
    async for v in docs:
        inspected += 1
        obs_payload = dict(
            vehicle_id=v.get("id"),
            source_type="public_archive",
            lot_ref=v.get("source_reference"),
            make=v.get("make"),
            model=v.get("model"),
            year=v.get("year"),
            mileage_km=v.get("mileage_km"),
            body_type=v.get("body_type"),
            damage_type=v.get("damage_type"),
            branch=v.get("location"),
            observed_at=datetime.now(timezone.utc),
            observed_price_nzd=float(v.get("current_price_nzd") or 0),
            buy_now_price_nzd=v.get("buy_now_price_nzd"),
            sold=True,
        )
        try:
            doc = AuctionObservation(source=source, **obs_payload).model_dump()
        except Exception:
            continue
        # Avoid double-inserts on repeated sweeps: dedupe by (source, lot_ref)
        # if we already captured it.
        if doc.get("lot_ref"):
            existing = await db.auction_observations.find_one({
                "source": source, "lot_ref": doc["lot_ref"], "sold": True,
            })
            if existing:
                to_mark.append(v["id"])
                continue
        await db.auction_observations.insert_one(doc)
        captured += 1
        to_mark.append(v["id"])

    if to_mark:
        r = await db.auto_vehicles.update_many(
            {"id": {"$in": to_mark}},
            {"$set": {"status": "sold", "sold_at": datetime.utcnow()}},
        )
        marked = r.modified_count

    return {
        "source": source,
        "stale_hours": stale_hours,
        "inspected": inspected,
        "captured": captured,
        "marked_sold": marked,
    }


async def snapshot_current_listings(db, source: str, *, max_rows: int = 200) -> Dict[str, int]:
    """Capture a lightweight "official_listing" observation for every priced
    lot currently on this source.

    Unlike `sweep_stale_as_sold` these are NOT hammer prices — they're a
    time-series snapshot of asking prices.  Two use cases:

      1. Feeds AI estimator with a broader base of live data.
      2. Gives `similar_sold_history` something to serve when we haven't
         yet accumulated genuine sold rows (though the widget already
         falls back to current_listings via the catalog).

    Deduplicated per (source, lot_ref, observed_price_nzd) within 24 h so
    we don't spam Mongo with identical rows every 6 h.
    """
    now = datetime.now(timezone.utc)
    day_ago = (now - timedelta(hours=24)).replace(tzinfo=None)

    inspected = 0
    captured = 0
    cursor = db.auto_vehicles.find({
        "source": source,
        "status": "available",
        "current_price_nzd": {"$gt": 0},
    }).limit(int(max_rows))

    async for v in cursor:
        inspected += 1
        lot_ref = v.get("source_reference")
        price = float(v.get("current_price_nzd") or 0)
        if not lot_ref or price <= 0:
            continue
        # Skip if we already captured the same price in the last 24 h.
        existing = await db.auction_observations.find_one({
            "source": source,
            "lot_ref": lot_ref,
            "source_type": "official_listing",
            "observed_price_nzd": price,
            "observed_at": {"$gte": day_ago},
        })
        if existing:
            continue
        try:
            doc = AuctionObservation(
                source=source,
                source_type="official_listing",
                lot_ref=lot_ref,
                vehicle_id=v.get("id"),
                make=v.get("make"),
                model=v.get("model"),
                year=v.get("year"),
                mileage_km=v.get("mileage_km"),
                body_type=v.get("body_type"),
                damage_type=v.get("damage_type"),
                branch=v.get("location"),
                observed_at=now,
                observed_price_nzd=price,
                buy_now_price_nzd=v.get("buy_now_price_nzd"),
                sold=False,
            ).model_dump()
        except Exception:
            continue
        await db.auction_observations.insert_one(doc)
        captured += 1

    return {"source": source, "inspected": inspected, "captured": captured}


async def sweep_stale_all(db, stale_hours: int = 48) -> List[Dict[str, int]]:
    """Sweep every known auction source. Skips inquiry-only sources like
    Pickles where lots don't have an auction close (they're negotiations).
    """
    out = []
    for src in ("turners", "manheim"):
        out.append(await sweep_stale_as_sold(db, src, stale_hours=stale_hours))
    return out


async def snapshot_all(db) -> List[Dict[str, int]]:
    """Snapshot every auction source's currently priced live listings."""
    out = []
    for src in ("turners", "manheim"):
        out.append(await snapshot_current_listings(db, src))
    return out
