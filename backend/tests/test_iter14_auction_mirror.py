"""Iter14 — internal auction mirror endpoint.

Verifies:
  1) GET /api/auto/auctions/calendar exposes a non-empty `event_id` on each event.
  2) GET /api/auto/auctions/events/<event_id> returns {event, vehicles},
     event has the required fields & Russian-localised translations.
  3) GET /api/auto/auctions/events/<garbage> returns 404 with the Russian detail.
"""
from __future__ import annotations

import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"

CAL_URL = f"{BASE_URL}/api/auto/auctions/calendar?days_ahead=21"
EVENT_URL = f"{BASE_URL}/api/auto/auctions/events"


@pytest.fixture(scope="module")
def calendar_payload():
    r = requests.get(CAL_URL, timeout=30)
    assert r.status_code == 200, f"calendar HTTP {r.status_code}: {r.text[:300]}"
    data = r.json()
    assert "events" in data and isinstance(data["events"], list)
    return data


class TestAuctionMirror:
    def test_calendar_events_have_event_id(self, calendar_payload):
        events = calendar_payload["events"]
        assert len(events) > 0, "no events returned from calendar"
        missing = [e for e in events if not e.get("event_id")]
        assert not missing, f"{len(missing)} events missing event_id"
        # all event_ids are 12-char hex
        bad = [e for e in events if not re.fullmatch(r"[0-9a-f]{12}", e.get("event_id", ""))]
        assert not bad, f"event_id not 12-hex for {len(bad)} events; sample={bad[0] if bad else None}"

    def test_event_detail_returns_event_and_vehicles(self, calendar_payload):
        ev = calendar_payload["events"][0]
        eid = ev["event_id"]
        r = requests.get(f"{EVENT_URL}/{eid}", timeout=30)
        assert r.status_code == 200, f"detail HTTP {r.status_code}: {r.text[:300]}"
        data = r.json()
        assert "event" in data and "vehicles" in data
        assert isinstance(data["vehicles"], list), "vehicles must be a list (may be empty)"
        event = data["event"]
        # required fields
        for k in ("event_id", "source", "category", "title", "branch", "city", "starts_at", "lots"):
            assert k in event, f"event missing key {k}: {list(event.keys())}"
        assert event["event_id"] == eid
        # translate_event_doc replaces title/branch/city with Russian translations
        # in-place and exposes the originals under *_en fields. Verify _en
        # presence (proof translation ran) and that the city contains Cyrillic
        # (or is the special "National" sentinel).
        for k in ("title_en", "branch_en", "city_en"):
            assert k in event, f"missing translation marker {k}: {list(event.keys())}"
        city = event.get("city") or ""
        # Russian text must contain at least one Cyrillic character for the
        # city field (Russian localisation contract). Empty city is acceptable
        # only when the upstream had no branch (rare).
        if city:
            assert re.search(r"[\u0400-\u04FF]", city), f"city not Russian-localised: {city!r}"

    def test_event_detail_garbage_id_returns_404(self):
        r = requests.get(f"{EVENT_URL}/this-id-does-not-exist", timeout=30)
        assert r.status_code == 404, f"expected 404, got {r.status_code}: {r.text[:200]}"
        body = r.json()
        assert body.get("detail") == "Аукцион не найден.", f"unexpected detail: {body}"
