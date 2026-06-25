"""
АвтоРесурс / BuyAnywhere Auto — source importers.

Goal: maintain the most complete possible catalogue of publicly available
vehicles from approved source websites. Importers MUST be modular: a failure
in one importer must never affect the rest of the platform.

Architecture:
    SourceImporter (interface)
        ├── TurnersImporter   (Turners NZ)
        ├── ManheimImporter   (Manheim NZ)
        └── PicklesImporter   (Pickles AU)

Each importer:
    - tries to fetch from a *publicly listed* index URL the operator configures;
    - parses what it can (HTML / RSS / JSON);
    - returns AutoVehicle records with consistent metadata
      (source, source_reference, source_url, last_sync_time, sync_status,
       inventory_status);
    - never raises into the orchestrator: any failure is captured into
      sync_status = 'failed' and surfaced for the admin.

Duplicate detection:
    Primary  → source + source_reference  (unique inside one source)
    Secondary → VIN  (across all sources)
    Tertiary → year + make + model + mileage_km + location

Status rules:
    Vehicles are *never* deleted. When a source no longer lists a vehicle the
    importer flips inventory_status to "sold" or "removed" and the visible
    status is updated. Admin can hide manually.
"""

from __future__ import annotations

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
from bs4 import BeautifulSoup

from models.auto import (
    AutoCountry,
    AutoImageRights,
    AutoInventoryStatus,
    AutoListingType,
    AutoSyncStatus,
    AutoVehicle,
    AutoVehicleStatus,
)
from services.auto_ai_service import AutoAIService

logger = logging.getLogger(__name__)


# ---------- helpers ----------

PRICE_RE = re.compile(r"(?:NZ\$|AU\$|\$)\s*([\d,]+(?:\.\d{1,2})?)", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
KM_RE = re.compile(r"([\d,]{2,})\s*(?:km|км)\b", re.IGNORECASE)


def _to_float(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    try:
        return float(s.replace(",", "").strip())
    except Exception:
        return None


def _norm(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    return re.sub(r"\s+", " ", s.strip()) or None


# ---------- result types ----------

@dataclass
class ImportResult:
    importer: str
    fetched: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    sync_status: AutoSyncStatus = AutoSyncStatus.SUCCESS
    errors: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "importer": self.importer,
            "fetched": self.fetched,
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "failed": self.failed,
            "sync_status": self.sync_status.value,
            "errors": self.errors[:20],
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }


# ---------- base ----------

class SourceImporter(ABC):
    """Abstract source importer.

    Concrete subclasses must implement at least `fetch_vehicles`. They MAY
    implement `fetch_vehicle_details` for richer enrichment.
    """

    name: str = "source"
    country: AutoCountry = AutoCountry.NZ
    listing_type: AutoListingType = AutoListingType.AUCTION
    base_url: Optional[str] = None
    user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

    def __init__(self, ai: Optional[AutoAIService] = None):
        self.ai = ai

    # ---- HTTP helpers ----
    async def _get(self, url: str, timeout: float = 12.0) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True,
                                         headers={"User-Agent": self.user_agent}) as c:
                r = await c.get(url)
                r.raise_for_status()
                return r.text
        except Exception as e:
            logger.warning(f"[{self.name}] GET {url} failed: {e}")
            return None

    # ---- abstract ----
    @abstractmethod
    async def fetch_vehicles(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return raw vehicle dicts (NOT yet AutoVehicle). The orchestrator
        will then call `normalise()` per dict."""
        raise NotImplementedError

    async def fetch_vehicle_details(self, source_reference: str) -> Optional[Dict[str, Any]]:
        return None

    # ---- normalisation ----
    def normalise(self, raw: Dict[str, Any]) -> AutoVehicle:
        """Convert a raw dict to an AutoVehicle. Subclasses can override."""
        title = _norm(raw.get("title") or raw.get("title_original")) or "Автомобиль"
        return AutoVehicle(
            source=self.name,
            source_url=raw.get("source_url"),
            source_reference=raw.get("source_reference"),
            country=self.country,
            listing_type=self.listing_type,
            title_original=title,
            title_ru=raw.get("title_ru") or title,
            description_original=raw.get("description") or raw.get("description_original"),
            make=_norm(raw.get("make")),
            model=_norm(raw.get("model")),
            year=raw.get("year"),
            mileage_km=raw.get("mileage_km"),
            engine=_norm(raw.get("engine")),
            fuel=_norm(raw.get("fuel")),
            transmission=_norm(raw.get("transmission")),
            body_type=_norm(raw.get("body_type")),
            location=_norm(raw.get("location")),
            condition=_norm(raw.get("condition")),
            damage_type=_norm(raw.get("damage_type")),
            current_price_nzd=raw.get("current_price_nzd"),
            buy_now_price_nzd=raw.get("buy_now_price_nzd"),
            status=AutoVehicleStatus.AVAILABLE,
            source_images=list(raw.get("images") or []),
            images=list(raw.get("images") or []),
            image_rights_status=AutoImageRights.SOURCE_PREVIEW,
            vin=raw.get("vin"),
            last_sync_time=datetime.utcnow(),
            sync_status=AutoSyncStatus.SUCCESS,
            inventory_status=AutoInventoryStatus.AVAILABLE,
        )


# ---------- concrete importers ----------

class TurnersImporter(SourceImporter):
    """Turners NZ. Uses the auction calendar collection (populated by the
    AuctionCalendarService) as starting points, then crawls per-auction pages.
    Falls back to the public branch index pages if the calendar is empty."""

    name = "turners"
    country = AutoCountry.NZ
    listing_type = AutoListingType.AUCTION
    base_url = "https://www.turners.co.nz"

    def __init__(self, ai=None, db=None):
        super().__init__(ai=ai)
        self.db = db

    async def fetch_vehicles(self, limit: int = 20) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        # Strategy 1: use cached calendar (admin already runs daily refresh)
        auction_urls: List[str] = []
        if self.db is not None:
            try:
                # Pull as many upcoming Turners auctions as we can — we want
                # the full mirror, not just the top-20.
                async for ev in self.db.auto_auction_calendar.find(
                    {"source": "turners"}
                ).sort("starts_at", 1).limit(200):
                    if ev.get("auction_url"):
                        auction_urls.append(ev["auction_url"])
            except Exception:
                pass
        # Strategy 2: also walk the branch index pages — this is what unlocks
        # the rest of the stock when a calendar entry's lots aren't paginated.
        from services.auto_auctions_service import (
            TURNERS_BRANCH_URLS,
            TURNERS_DAMAGED_URL,
            TURNERS_TRUCKS_URL,
        )
        # When the caller wants more than 100 items, scan ALL branches + the
        # damaged/trucks indexes. For small previews we keep the cheap 6-branch
        # cap so admin "scan" still feels snappy.
        if limit > 100:
            branch_pool = list(TURNERS_BRANCH_URLS) + [TURNERS_DAMAGED_URL, TURNERS_TRUCKS_URL]
        else:
            branch_pool = list(TURNERS_BRANCH_URLS)[:6]
        # Dedup-merge into auction_urls preserving calendar-first order.
        for u in branch_pool:
            if u not in auction_urls:
                auction_urls.append(u)
        for url in auction_urls:
            if len(items) >= limit:
                break
            html = await self._get(url)
            if not html:
                continue
            items.extend(self._parse_auction_page(html, url))
        # De-duplicate by source_url
        seen = set()
        deduped = []
        for it in items:
            key = it.get("source_url") or it.get("source_reference")
            if key in seen:
                continue
            seen.add(key)
            deduped.append(it)
        return deduped[:limit]

    def _parse_auction_page(self, html: str, base: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        results: List[Dict[str, Any]] = []
        seen = set()
        # Look for product anchors (Turners stock items live at /Cars/Used-Cars-for-Sale/<slug>/)
        for a in soup.select("a"):
            href = a.get("href") or ""
            if not href:
                continue
            if not any(p in href for p in ("/Used-Cars-for-Sale/", "/cars/used-cars-for-sale/")):
                continue
            full = href if href.startswith("http") else f"{self.base_url}{href}"
            if full in seen:
                continue
            text = _norm(a.get_text(" ", strip=True))
            if not text or len(text) < 8:
                continue
            # Reject landing/aggregator pages and CTA tiles (iter15 cleanup).
            low = text.lower().strip()
            if low in {
                "view stock", "find a car", "discounted cars",
                "buy now", "buy a car", "bid now", "sell my car",
                "view auction", "auctions", "view all stock",
            }:
                continue
            if any(p in low for p in ("view stock", "find a car", "discounted cars", "view all")):
                continue
            ref_m = re.search(r"/(\d{4,})(?:/|$)", full)
            year_m = YEAR_RE.search(text)
            price_m = PRICE_RE.search(text)
            # A real lot must have at least a 4-digit year and a stock id.
            if not year_m or not ref_m:
                continue
            seen.add(full)
            results.append({
                "source_url": full,
                "source_reference": ref_m.group(1) if ref_m else None,
                "title": text[:160],
                "year": int(year_m.group(0)) if year_m else None,
                "current_price_nzd": _to_float(price_m.group(1)) if price_m else None,
            })
        return results


class ManheimImporter(SourceImporter):
    """Manheim NZ — parses public search pages (passenger + damaged).

    Each card has `.vehicle-card` with:
      - h2  → "<year> <make> <model> <body>"
      - a   → "/<category>/<numeric_id>/<slug>?..."  (source_reference = numeric_id)
      - img → CDN image (img.manheim.com.au)
      - body text contains location, lot, starting bid, odometer, etc.
    """

    name = "manheim"
    country = AutoCountry.NZ
    listing_type = AutoListingType.AUCTION
    base_url = "https://www.manheim.co.nz"

    SEARCH_PAGES = [
        ("/passenger-vehicles/search", AutoListingType.AUCTION, None),
        ("/damaged-vehicles/search",   AutoListingType.AUCTION, "damaged"),
        ("/trucks-machinery/search",   AutoListingType.AUCTION, None),
    ]

    # 2016 Nissan Leaf Hatch  →  year=2016 make=Nissan model="Leaf Hatch"
    _TITLE_RE = re.compile(r"^\s*(19|20)(\d{2})\s+([A-Za-z\-]+)\s+(.+?)\s*$")
    _ODO_RE   = re.compile(r"([\d,]{2,})\s*KM", re.IGNORECASE)
    _BID_RE   = re.compile(r"\$\s*([\d,]+)\s*Starting\s*Bid", re.IGNORECASE)

    async def fetch_vehicles(self, limit: int = 20) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        seen: set = set()
        # Paginate each category until we hit the user-requested ceiling
        # or the page returns 0 new items (= we've consumed the catalogue).
        for path, ltype, damage_hint in self.SEARCH_PAGES:
            if len(results) >= limit:
                break
            for page in range(1, 51):  # safety stop at 50 pages × ~24 cards
                if len(results) >= limit:
                    break
                sep = "&" if "?" in path else "?"
                url = f"{self.base_url}{path}{sep}page={page}"
                html = await self._get(url)
                if not html:
                    break
                before = len(results)
                results.extend(
                    self._parse_search(html, ltype, damage_hint, seen, limit - len(results))
                )
                # Stop paginating this category when the page yields no new card.
                if len(results) == before:
                    break
        return results[:limit]

    def _parse_search(self, html: str, ltype: AutoListingType,
                       damage_hint: Optional[str], seen: set, remaining: int) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        out: List[Dict[str, Any]] = []
        for card in soup.select(".vehicle-card"):
            if len(out) >= remaining:
                break
            a = card.select_one("a[href]")
            if not a:
                continue
            href = a.get("href") or ""
            full = href if href.startswith("http") else f"{self.base_url}{href}"
            ref_m = re.search(r"/(\d{6,})(?:/|$)", full)
            ref = ref_m.group(1).lstrip("0") if ref_m else None
            key = ref or full
            if key in seen:
                continue
            seen.add(key)
            title_el = card.select_one("h2")
            title = _norm(title_el.get_text(" ", strip=True)) if title_el else None
            year = make = model = body = None
            if title:
                tm = self._TITLE_RE.match(title)
                if tm:
                    year = int(f"{tm.group(1)}{tm.group(2)}")
                    make = tm.group(3)
                    rest = tm.group(4)
                    parts = rest.split()
                    body = parts[-1] if len(parts) > 1 else None
                    model = " ".join(parts[:-1]) if body and len(parts) > 1 else rest
            text = card.get_text(" ", strip=True)
            odo_m = self._ODO_RE.search(text)
            bid_m = self._BID_RE.search(text)
            # Location: usually "Suburb, City, Region"
            loc_m = re.search(r"([A-Z][A-Za-z\s]+?,\s*[A-Z][A-Za-z\s]+?,\s*[A-Z][A-Za-z\s]+?Island)", text)
            img_el = card.select_one("img")
            img_url = (img_el.get("src") or img_el.get("data-src")) if img_el else None
            out.append({
                "source_url": full,
                "source_reference": ref,
                "title": title or "Manheim listing",
                "year": year,
                "make": make,
                "model": model,
                "body_type": body,
                "mileage_km": int(odo_m.group(1).replace(",", "")) if odo_m else None,
                "current_price_nzd": float(bid_m.group(1).replace(",", "")) if bid_m else None,
                "location": _norm(loc_m.group(1)) if loc_m else None,
                "damage_type": damage_hint,
                "images": [img_url] if img_url else [],
                "_listing_type": ltype,
            })
        return out

    def normalise(self, raw: Dict[str, Any]) -> AutoVehicle:
        v = super().normalise(raw)
        # honour per-card listing type override
        if raw.get("_listing_type"):
            v.listing_type = raw["_listing_type"]
        if raw.get("damage_type") == "damaged":
            v.status = AutoVehicleStatus.AVAILABLE
        return v


class PicklesImporter(SourceImporter):
    """Pickles AU — parses /cars/search grid cards.

    Each card has `[class*='gridCard']` with:
      - h2 → "<year> <make> <model>"
      - a  → "/used/details/cars/<slug>/<stock_id>"
      - img.src → CDN image
      - card text contains: location, "<km> km", year, seats, fuel, transmission, "Stock <id>"
    """

    name = "pickles"
    country = AutoCountry.AU
    listing_type = AutoListingType.INQUIRY_ONLY
    base_url = "https://www.pickles.com.au"

    SEARCH_PAGES = [
        "/cars/search",
        "/used/search/category/passenger",
    ]

    _TITLE_RE = re.compile(r"^\s*(19|20)(\d{2})\s+([A-Za-z\-]+)\s+(.+?)\s*$")
    _KM_RE    = re.compile(r"([\d,]{2,})\s*km\b", re.IGNORECASE)
    _STOCK_RE = re.compile(r"Stock\s+(\d{4,})", re.IGNORECASE)
    _LOC_RE   = re.compile(r"\b([A-Z][A-Za-z\s']+,\s*(?:NSW|VIC|QLD|SA|WA|TAS|ACT|NT))\b")

    async def fetch_vehicles(self, limit: int = 20) -> List[Dict[str, Any]]:
        seen: set = set()
        results: List[Dict[str, Any]] = []
        for path in self.SEARCH_PAGES:
            if len(results) >= limit:
                break
            # Paginate up to 50 pages per search; stop on empty page.
            for page in range(1, 51):
                if len(results) >= limit:
                    break
                sep = "&" if "?" in path else "?"
                url = f"{self.base_url}{path}{sep}page={page}"
                html = await self._get(url)
                if not html:
                    break
                before = len(results)
                results.extend(self._parse_search(html, seen, limit - len(results)))
                if len(results) == before:
                    break
        return results[:limit]

    def _parse_search(self, html: str, seen: set, remaining: int) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        out: List[Dict[str, Any]] = []
        for card in soup.select("[class*='gridCard'], article[class*='Card']"):
            if len(out) >= remaining:
                break
            a = card.select_one("a[href]")
            if not a:
                continue
            href = a.get("href") or ""
            full = href if href.startswith("http") else f"{self.base_url}{href}"
            # /used/details/cars/<slug>/<id>
            ref_m = re.search(r"/(\d{6,})(?:/|$|\?)", full)
            ref = ref_m.group(1) if ref_m else None
            key = ref or full
            if key in seen:
                continue
            seen.add(key)
            title_el = card.select_one("h2")
            title = _norm(title_el.get_text(" ", strip=True)) if title_el else None
            year = make = model = None
            if title:
                tm = self._TITLE_RE.match(title)
                if tm:
                    year = int(f"{tm.group(1)}{tm.group(2)}")
                    make = tm.group(3)
                    model = tm.group(4)
            text = card.get_text(" ", strip=True)
            km_m = self._KM_RE.search(text)
            stock_m = self._STOCK_RE.search(text)
            loc_m = self._LOC_RE.search(text)
            img_el = card.select_one("img")
            img_url = (img_el.get("src") or img_el.get("data-src")) if img_el else None
            out.append({
                "source_url": full,
                "source_reference": ref or (stock_m.group(1) if stock_m else None),
                "title": title or "Pickles listing",
                "year": year,
                "make": make,
                "model": model,
                "mileage_km": int(km_m.group(1).replace(",", "")) if km_m else None,
                "location": _norm(loc_m.group(1)) if loc_m else None,
                "images": [img_url] if img_url else [],
            })
        return out


# Registry — easy to add a phase-2/3 source without touching call sites.
IMPORTERS: Dict[str, type] = {
    "turners": TurnersImporter,
    "manheim": ManheimImporter,
    "pickles": PicklesImporter,
}


# ---------- duplicate detection ----------

async def find_duplicate(db, candidate: AutoVehicle) -> Optional[Dict[str, Any]]:
    """Return an existing vehicle that duplicates `candidate`, or None.

    Order: source+source_reference → vin → year+make+model+mileage+location.
    """
    if candidate.source and candidate.source_reference:
        doc = await db.auto_vehicles.find_one(
            {"source": candidate.source, "source_reference": candidate.source_reference}
        )
        if doc:
            return doc
    if candidate.vin:
        doc = await db.auto_vehicles.find_one({"vin": candidate.vin})
        if doc:
            return doc
    if all([candidate.year, candidate.make, candidate.model]):
        q: Dict[str, Any] = {
            "year": candidate.year,
            "make": {"$regex": f"^{re.escape(candidate.make)}$", "$options": "i"},
            "model": {"$regex": f"^{re.escape(candidate.model)}$", "$options": "i"},
        }
        if candidate.mileage_km:
            q["mileage_km"] = {"$gte": int(candidate.mileage_km * 0.9),
                               "$lte": int(candidate.mileage_km * 1.1)}
        if candidate.location:
            q["location"] = {"$regex": re.escape(candidate.location), "$options": "i"}
        doc = await db.auto_vehicles.find_one(q)
        if doc:
            return doc
    return None


# ---------- orchestrator ----------

class ImportOrchestrator:
    """Runs one or all importers, applies duplicate detection, upserts into
    Mongo, and records a single ImportResult per importer."""

    def __init__(self, db, ai: Optional[AutoAIService] = None):
        self.db = db
        self.ai = ai

    def available_sources(self) -> List[str]:
        return list(IMPORTERS.keys())

    async def run_one(self, source: str, limit: int = 20) -> ImportResult:
        if source not in IMPORTERS:
            return ImportResult(importer=source, sync_status=AutoSyncStatus.FAILED,
                                errors=[f"Unknown source: {source}"], finished_at=datetime.utcnow())
        importer = IMPORTERS[source](ai=self.ai)
        result = ImportResult(importer=source)
        try:
            raw_items = await importer.fetch_vehicles(limit=limit)
        except Exception as e:
            result.sync_status = AutoSyncStatus.FAILED
            result.errors.append(str(e))
            result.finished_at = datetime.utcnow()
            return result
        result.fetched = len(raw_items)
        for raw in raw_items:
            try:
                vehicle = importer.normalise(raw)
                existing = await find_duplicate(self.db, vehicle)
                payload = vehicle.model_dump()
                if existing:
                    payload.pop("id", None)
                    payload.pop("created_at", None)
                    payload["updated_at"] = datetime.utcnow()
                    payload["last_sync_time"] = datetime.utcnow()
                    await self.db.auto_vehicles.update_one(
                        {"id": existing["id"]}, {"$set": payload}
                    )
                    result.updated += 1
                else:
                    await self.db.auto_vehicles.insert_one(payload)
                    result.created += 1
            except Exception as e:
                result.failed += 1
                result.errors.append(str(e))
        if result.failed > 0 and result.created + result.updated == 0:
            result.sync_status = AutoSyncStatus.FAILED
        elif result.failed > 0:
            result.sync_status = AutoSyncStatus.PARTIAL
        result.finished_at = datetime.utcnow()
        await self.db.auto_import_runs.insert_one(result.to_dict())
        return result

    async def run_all(self, limit_per_source: int = 20) -> List[ImportResult]:
        """Run every importer in parallel. A failure in one MUST NOT affect
        the others (per spec)."""
        async def _safe(src: str) -> ImportResult:
            try:
                return await self.run_one(src, limit=limit_per_source)
            except Exception as e:
                return ImportResult(importer=src, sync_status=AutoSyncStatus.FAILED,
                                    errors=[str(e)], finished_at=datetime.utcnow())
        return await asyncio.gather(*[_safe(s) for s in IMPORTERS.keys()])
