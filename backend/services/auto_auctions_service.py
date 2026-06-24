"""
АвтоРесурс — Turners auctions calendar.

Fetches https://www.turners.co.nz/Cars/Auctions/ (and its sibling damaged/
truck/general-goods pages on demand), parses the upcoming-auction table and
stores a normalised set of auction events in Mongo collection
``auto_auction_calendar``.

If Turners changes the page structure or blocks automated retrieval, the
parser falls back to an empty list and the caller can serve previously
cached calendar entries.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


TURNERS_CARS_URL = "https://www.turners.co.nz/Cars/Auctions/"
TURNERS_DAMAGED_URL = "https://www.turners.co.nz/Damaged-Vehicles/Auctions/"
TURNERS_TRUCKS_URL = "https://www.turners.co.nz/Trucks-Machinery/Auctions/"

# Per-branch listing URLs — these are statically rendered (unlike the
# root /Cars/Auctions/ index, which hydrates client-side).
TURNERS_BRANCH_URLS: List[str] = [
    "https://www.turners.co.nz/auctions/whangarei/",
    "https://www.turners.co.nz/auctions/otahuhu/",
    "https://www.turners.co.nz/auctions/north-shore/",
    "https://www.turners.co.nz/auctions/north-west-auckland/",
    "https://www.turners.co.nz/auctions/westgate/",
    "https://www.turners.co.nz/auctions/penrose-great-south-road/",
    "https://www.turners.co.nz/auctions/manukau/",
    "https://www.turners.co.nz/auctions/botany/",
    "https://www.turners.co.nz/auctions/hamilton/",
    "https://www.turners.co.nz/auctions/avalon-drive/",
    "https://www.turners.co.nz/auctions/te-rapa-road/",
    "https://www.turners.co.nz/auctions/tauranga/",
    "https://www.turners.co.nz/auctions/rotorua/",
    "https://www.turners.co.nz/auctions/napier/",
    "https://www.turners.co.nz/auctions/new-plymouth/",
    "https://www.turners.co.nz/auctions/palmerston-north/",
    "https://www.turners.co.nz/auctions/porirua-cars/",
    "https://www.turners.co.nz/auctions/nelson/",
    "https://www.turners.co.nz/auctions/hornby-cars/",
    "https://www.turners.co.nz/auctions/wairakei-rd/",
    "https://www.turners.co.nz/auctions/moorhouse-ave/",
    "https://www.turners.co.nz/auctions/timaru/",
    "https://www.turners.co.nz/auctions/dunedin/",
    "https://www.turners.co.nz/auctions/invercargill/",
]

UA = "AvtoResursBot/1.0 (+https://avtoresurs)"

DATE_RE = re.compile(r"(\d{1,2})\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)", re.IGNORECASE)
LOTS_RE = re.compile(r"Lots?\s*(\d+)", re.IGNORECASE)
TIME_RE = re.compile(r"(\d{1,2}):(\d{2})\s*(am|pm)", re.IGNORECASE)

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _parse_when(date_token: str, time_token: Optional[str]) -> Optional[datetime]:
    """Convert ('Today'/'25 Jun', '05:00pm') → datetime (UTC-naive, NZ wall time)."""
    now = datetime.utcnow()
    d = date_token.strip()
    if d.lower() == "today":
        date = now.date()
    elif d.lower() == "tomorrow":
        date = (now + timedelta(days=1)).date()
    else:
        m = DATE_RE.search(d)
        if not m:
            return None
        day = int(m.group(1))
        month = MONTHS[m.group(2)[:3].lower()]
        year = now.year
        # If parsed date is more than 2 months in the past, assume next year.
        candidate = datetime(year, month, day)
        if candidate < now - timedelta(days=60):
            candidate = datetime(year + 1, month, day)
        date = candidate.date()
    hour, minute = 12, 0
    if time_token:
        tm = TIME_RE.search(time_token)
        if tm:
            hour = int(tm.group(1)) % 12
            minute = int(tm.group(2))
            if tm.group(3).lower() == "pm":
                hour += 12
    return datetime(date.year, date.month, date.day, hour, minute)


@dataclass
class AuctionEvent:
    source: str = "turners"
    category: str = "cars"  # cars | damaged | trucks
    title: str = ""
    branch: str = ""
    city: Optional[str] = None
    starts_at: Optional[datetime] = None
    lots: int = 0
    auction_url: Optional[str] = None
    fetched_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def key(self) -> str:
        return f"{self.source}:{self.auction_url or self.title + '|' + self.branch + '|' + (self.starts_at.isoformat() if self.starts_at else '')}"

    def to_doc(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "source": self.source,
            "category": self.category,
            "title": self.title,
            "branch": self.branch,
            "city": self.city,
            "starts_at": self.starts_at,
            "lots": self.lots,
            "auction_url": self.auction_url,
            "fetched_at": self.fetched_at,
        }


# Map a Turners "branch" label → friendly city used by the transport calculator
BRANCH_TO_CITY = {
    "whangarei": "Whangarei",
    "otahuhu": "Otahuhu", "north shore": "North Shore", "westgate": "Westgate",
    "botany": "Botany", "manukau": "Manukau", "penrose": "Penrose",
    "avalon drive": "Hamilton", "te rapa road": "Hamilton", "hamilton": "Hamilton",
    "tauranga": "Tauranga", "rotorua": "Rotorua",
    "napier": "Napier", "new plymouth": "New Plymouth",
    "palmerston north": "Palmerston North",
    "porirua": "Porirua", "wellington": "Wellington",
    "nelson": "Nelson", "blenheim": "Blenheim",
    "wairakei rd": "Christchurch", "moorhouse ave": "Christchurch", "hornby": "Christchurch",
    "timaru": "Timaru", "dunedin": "Dunedin", "invercargill": "Invercargill",
}


def _branch_city(branch: str) -> Optional[str]:
    n = (branch or "").lower()
    for key, city in BRANCH_TO_CITY.items():
        if key in n:
            return city
    return None


def parse_turners_page(html: str, category: str = "cars") -> List[AuctionEvent]:
    """Parse a Turners branch auctions page.

    The page renders each auction inside a flat block whose plain text looks
    like::

        Today 05:00pm Event Big Wednesday Auction Branch Napier Cars Lots 22 View Live

    We locate every `<a href="/Cars/Auctions/{ID}/">` anchor, walk up to the
    nearest ancestor that contains the "Lots" + date tokens, and extract
    structured fields with regular expressions.
    """
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    seen: set = set()
    events: List[AuctionEvent] = []
    for a in soup.select('a[href*="/Cars/Auctions/"][href*="-"]'):
        href = a.get("href") or ""
        m = re.search(r"/(\d{3,}-\d{3,})/", href)
        if not m:
            continue
        full = href if href.startswith("http") else f"https://www.turners.co.nz{href}"
        if full in seen:
            continue
        # Walk up to find the auction block ancestor
        node = a
        block_text: Optional[str] = None
        for _ in range(15):
            node = node.parent
            if node is None:
                break
            text = re.sub(r"\s+", " ", node.get_text(" ", strip=True))
            if " Lots " in f" {text} " or text.endswith(" Lots") or "Lots 0" in text:
                # ensure date token present so we don't grab the page footer
                if any(tok in text for tok in (
                    "Today", "Tomorrow",
                    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
                )):
                    block_text = text
                    break
        if not block_text:
            continue
        seen.add(full)
        # Trim the block to start at the first date token (so we don't include header navigation text)
        idx = -1
        for tok in ("Today", "Tomorrow") + tuple(MONTHS.keys()):
            for cap in (tok.capitalize(), tok):
                p = block_text.find(cap)
                if p >= 0 and (idx == -1 or p < idx):
                    # Require a digit nearby (e.g. "25 Jun" or "Jun 25") OR be Today/Tomorrow
                    if cap in ("Today", "Tomorrow"):
                        idx = p
                    elif p >= 3 and block_text[p - 3 : p].strip().isdigit():
                        idx = p - 3
                    elif p >= 2 and block_text[p - 2 : p].strip().isdigit():
                        idx = p - 2
        if idx > 0:
            block_text = block_text[idx:]
        # Parse fields
        date_match = re.match(r"(Today|Tomorrow|\d{1,2}\s+[A-Za-z]{3,9})\s+(\d{1,2}:\d{2}\s*(?:am|pm))",
                              block_text, re.IGNORECASE)
        if not date_match:
            continue
        date_token = date_match.group(1)
        time_token = date_match.group(2)
        starts_at = _parse_when(date_token, time_token)
        # Title between "Event " and " Branch "
        title_m = re.search(r"Event\s+(.+?)\s+Branch\s+(.+?)\s+Lots\s+(\d+)", block_text)
        if not title_m:
            continue
        title = title_m.group(1).strip()
        branch = title_m.group(2).strip()
        lots = int(title_m.group(3))
        events.append(AuctionEvent(
            source="turners",
            category=category,
            title=title[:200],
            branch=branch,
            city=_branch_city(branch),
            starts_at=starts_at,
            lots=lots,
            auction_url=full,
        ))
    return events


async def fetch_turners_auctions(category: str = "cars") -> List[AuctionEvent]:
    """Fetch every branch page in parallel; aggregate + deduplicate by URL."""
    if category not in ("cars", "damaged", "trucks"):
        category = "cars"
    urls = list(TURNERS_BRANCH_URLS) if category == "cars" else []
    # The damaged + trucks indices are also JS-hydrated, but in the static HTML
    # they at least include the branch links. The cars list is most important
    # right now; damaged/trucks fall back to the root URLs and may yield 0.
    if category == "damaged":
        urls.append(TURNERS_DAMAGED_URL)
    elif category == "trucks":
        urls.append(TURNERS_TRUCKS_URL)

    async def _get(client: httpx.AsyncClient, url: str) -> str:
        try:
            r = await client.get(url)
            r.raise_for_status()
            return r.text
        except Exception as e:
            logger.warning(f"Turners fetch {url} failed: {e}")
            return ""

    events: List[AuctionEvent] = []
    seen_urls: set = set()
    try:
        async with httpx.AsyncClient(
            timeout=15.0, follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 AvtoResursBot/1.0"},
        ) as client:
            import asyncio as _aio
            htmls = await _aio.gather(*[_get(client, u) for u in urls])
    except Exception as e:
        logger.warning(f"Turners parallel fetch failed: {e}")
        return []
    for html in htmls:
        if not html:
            continue
        for ev in parse_turners_page(html, category=category):
            if ev.auction_url and ev.auction_url not in seen_urls:
                seen_urls.add(ev.auction_url)
                events.append(ev)
    return events


class AuctionCalendarService:
    """Persistence + queries for the auction calendar."""

    def __init__(self, db):
        self.db = db

    async def ensure_indexes(self) -> None:
        try:
            await self.db.auto_auction_calendar.create_index("key", unique=True)
            await self.db.auto_auction_calendar.create_index("starts_at")
            await self.db.auto_auction_calendar.create_index("city")
            await self.db.auto_auction_calendar.create_index("category")
        except Exception as e:
            logger.warning(f"Auction calendar indexes failed: {e}")

    async def refresh(self, categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """Re-fetch and upsert. Returns summary."""
        categories = categories or ["cars", "damaged", "trucks"]
        total = 0
        per_cat: Dict[str, int] = {}
        for cat in categories:
            events = await fetch_turners_auctions(cat)
            per_cat[cat] = len(events)
            total += len(events)
            for ev in events:
                doc = ev.to_doc()
                await self.db.auto_auction_calendar.update_one(
                    {"key": doc["key"]},
                    {"$set": doc},
                    upsert=True,
                )
        return {"fetched": total, "by_category": per_cat, "at": datetime.utcnow().isoformat()}

    async def list_events(
        self,
        city: Optional[str] = None,
        category: Optional[str] = None,
        days_ahead: int = 21,
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {}
        if city:
            query["city"] = city
        if category:
            query["category"] = category
        cutoff = datetime.utcnow() - timedelta(hours=6)
        horizon = datetime.utcnow() + timedelta(days=days_ahead)
        query["starts_at"] = {"$gte": cutoff, "$lte": horizon}
        out: List[Dict[str, Any]] = []
        async for d in self.db.auto_auction_calendar.find(query).sort("starts_at", 1):
            d.pop("_id", None)
            if isinstance(d.get("starts_at"), datetime):
                d["starts_at"] = d["starts_at"].isoformat()
            if isinstance(d.get("fetched_at"), datetime):
                d["fetched_at"] = d["fetched_at"].isoformat()
            out.append(d)
        return out

    async def summary_by_day(self, days_ahead: int = 21) -> List[Dict[str, Any]]:
        events = await self.list_events(days_ahead=days_ahead)
        bucket: Dict[str, Dict[str, Any]] = {}
        for ev in events:
            if not ev.get("starts_at"):
                continue
            day = ev["starts_at"][:10]
            b = bucket.setdefault(day, {"date": day, "events": 0, "lots": 0, "cities": set(), "categories": set()})
            b["events"] += 1
            b["lots"] += int(ev.get("lots") or 0)
            if ev.get("city"):
                b["cities"].add(ev["city"])
            if ev.get("category"):
                b["categories"].add(ev["category"])
        out = []
        for k in sorted(bucket.keys()):
            v = bucket[k]
            v["cities"] = sorted(list(v["cities"]))
            v["categories"] = sorted(list(v["categories"]))
            out.append(v)
        return out
