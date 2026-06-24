"""Iter8 — Final pre-MVP regression.

Covers:
- /api/auto/auctions/calendar — Russian i18n (title/branch/city + *_en keys)
- /api/auto/body-type-counts — 8 canonical items
- /api/auto/vehicles?body_type=sedan|suv|hatchback — alias regex filtering
- Regression: admin login, AI chat, admin settings, deposit GET, Stripe session
"""
from __future__ import annotations

import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://auto-nz-bidding.preview.emergentagent.com").rstrip("/")

ADMIN_EMAIL = "admin@buyanywhere.com"
ADMIN_PASSWORD = "admin12345"
CLIENT_EMAIL = "client@buyanywhere.com"
CLIENT_PASSWORD = "client12345"

CANONICAL_BODY_TYPES = {"convertible", "wagon", "utility", "coupe", "hatchback", "van", "sedan", "suv"}

# RU alphabet check for translated strings
RU_RE = re.compile(r"[А-Яа-яЁё]")


@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def admin_token(session):
    r = session.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token")
    assert tok
    return tok


@pytest.fixture(scope="session")
def client_token(session):
    r = session.post(f"{BASE_URL}/api/auth/login", json={"email": CLIENT_EMAIL, "password": CLIENT_PASSWORD})
    assert r.status_code == 200, f"Client login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token")
    assert tok
    return tok


# ---------------------------------------------------------------- CALENDAR i18n
class TestCalendarI18n:
    def test_calendar_returns_events(self, session):
        r = session.get(f"{BASE_URL}/api/auto/auctions/calendar", params={"days_ahead": 21})
        assert r.status_code == 200, r.text
        data = r.json()
        # Response shape may be {events: [...]} or list — handle both
        events = data.get("events") if isinstance(data, dict) else data
        assert isinstance(events, list), f"Expected list-like events, got {type(events)}: {data}"
        assert len(events) > 0, "Calendar should return at least one event"
        # Save for next tests via attribute on class
        self.__class__.events = events

    def test_calendar_titles_are_russian(self, session):
        r = session.get(f"{BASE_URL}/api/auto/auctions/calendar", params={"days_ahead": 21})
        events = r.json().get("events") if isinstance(r.json(), dict) else r.json()
        # At least 70% of events with title should contain Cyrillic characters
        titled = [e for e in events if e.get("title")]
        assert titled, "No events have title"
        ru_titles = [e for e in titled if RU_RE.search(e["title"] or "")]
        ratio = len(ru_titles) / len(titled)
        assert ratio >= 0.7, f"Only {ratio:.0%} of titles look Russian; sample={titled[:3]}"

    def test_calendar_preserves_english_originals(self, session):
        r = session.get(f"{BASE_URL}/api/auto/auctions/calendar", params={"days_ahead": 21})
        events = r.json().get("events") if isinstance(r.json(), dict) else r.json()
        # At least one event should have title_en preserved
        with_en = [e for e in events if e.get("title_en")]
        assert with_en, "Expected at least one event to have title_en key for English original"
        # And title_en should be ASCII English (no Cyrillic)
        sample = with_en[0]
        assert not RU_RE.search(sample["title_en"]), f"title_en should be English, got {sample['title_en']!r}"

    def test_calendar_branches_translated(self, session):
        r = session.get(f"{BASE_URL}/api/auto/auctions/calendar", params={"days_ahead": 21})
        events = r.json().get("events") if isinstance(r.json(), dict) else r.json()
        branched = [e for e in events if e.get("branch")]
        if not branched:
            pytest.skip("No events with branch field")
        ru_branches = [e for e in branched if RU_RE.search(e["branch"] or "")]
        ratio = len(ru_branches) / len(branched)
        assert ratio >= 0.5, f"Only {ratio:.0%} of branches look Russian; sample={[e['branch'] for e in branched[:5]]}"
        # Spot-check: at least one event with branch_en should exist
        with_en = [e for e in branched if e.get("branch_en")]
        assert with_en, "Expected branch_en preserved on at least one event"

    def test_calendar_cities_translated(self, session):
        r = session.get(f"{BASE_URL}/api/auto/auctions/calendar", params={"days_ahead": 21})
        events = r.json().get("events") if isinstance(r.json(), dict) else r.json()
        citied = [e for e in events if e.get("city")]
        if not citied:
            pytest.skip("No events with city field")
        ru_cities = [e for e in citied if RU_RE.search(e["city"] or "")]
        ratio = len(ru_cities) / len(citied)
        assert ratio >= 0.7, f"Only {ratio:.0%} of cities are Russian; sample={[e['city'] for e in citied[:5]]}"


# ---------------------------------------------------------------- BODY TYPE
class TestBodyTypeCounts:
    def test_body_type_counts_returns_canonical_8(self, session):
        r = session.get(f"{BASE_URL}/api/auto/body-type-counts")
        assert r.status_code == 200, r.text
        data = r.json()
        items = data.get("items") if isinstance(data, dict) else data
        assert isinstance(items, list)
        assert len(items) == 8, f"Expected 8 items, got {len(items)}"
        keys = {it.get("key") or it.get("body_type") or it.get("slug") for it in items}
        assert keys == CANONICAL_BODY_TYPES, f"Mismatch. Got {keys}"
        for it in items:
            assert "count" in it
            assert isinstance(it["count"], int)

    @pytest.mark.parametrize("body_type", ["sedan", "suv", "hatchback"])
    def test_vehicles_body_type_filter(self, session, body_type):
        r = session.get(f"{BASE_URL}/api/auto/vehicles", params={"body_type": body_type})
        assert r.status_code == 200, r.text
        data = r.json()
        total = data.get("total") if isinstance(data, dict) else len(data)
        assert total and total > 0, f"{body_type} returned 0 vehicles: {data}"


# ---------------------------------------------------------------- REGRESSION
class TestRegression:
    def test_admin_login(self, admin_token):
        assert admin_token

    def test_client_login(self, client_token):
        assert client_token

    def test_chat_reply(self, session):
        r = session.post(f"{BASE_URL}/api/auto/chat", json={"message": "Привет, какие машины есть?"})
        assert r.status_code == 200, r.text
        data = r.json()
        reply = data.get("reply") or data.get("message") or data.get("text") or data.get("content")
        assert reply, f"No reply field in chat response: {data}"
        assert len(reply) > 0

    def test_admin_settings(self, session, admin_token):
        r = session.get(
            f"{BASE_URL}/api/auto/admin/settings",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, dict) and len(data) > 0

    def test_my_deposit_verified_client(self, session, client_token):
        r = session.get(
            f"{BASE_URL}/api/auto/my/deposit",
            headers={"Authorization": f"Bearer {client_token}"},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        # Verified client should have status indicating they've paid
        status = data.get("status") or data.get("deposit_status") or (data.get("deposit") or {}).get("status")
        assert status, f"No status field: {data}"
        assert data.get("verified") is True or status == "verified"

    def test_deposit_stripe_session(self, session, client_token):
        # Use client2 (no deposit) instead since client1 is verified
        r2 = session.post(f"{BASE_URL}/api/auth/login", json={"email": "client2@buyanywhere.com", "password": "client12345"})
        if r2.status_code != 200:
            pytest.skip("client2 login failed")
        token2 = r2.json()["access_token"]
        r = session.post(
            f"{BASE_URL}/api/auto/deposit/stripe/session",
            headers={"Authorization": f"Bearer {token2}"},
            json={"origin_url": "https://auto-nz-bidding.preview.emergentagent.com"},
        )
        if r.status_code == 400:
            return  # Already verified
        assert r.status_code == 200, f"Stripe session failed: {r.status_code} {r.text}"
        data = r.json()
        url = data.get("url") or data.get("checkout_url") or data.get("session_url")
        assert url and "stripe.com" in url, f"Expected stripe checkout url, got: {data}"


# ---------------------------------------------------------------- PROD READINESS
class TestProductionReadiness:
    def test_backend_url_is_production(self):
        assert BASE_URL.startswith("https://"), f"REACT_APP_BACKEND_URL not HTTPS: {BASE_URL}"
        assert "localhost" not in BASE_URL

    def test_no_nzd_in_calendar_response(self, session):
        r = session.get(f"{BASE_URL}/api/auto/auctions/calendar", params={"days_ahead": 21})
        body = r.text
        # NZ$ shouldn't appear in user-facing strings
        assert "NZ$" not in body, "NZ$ leaks in calendar response"

    def test_no_nzd_in_vehicles_response(self, session):
        r = session.get(f"{BASE_URL}/api/auto/vehicles", params={"limit": 5})
        assert r.status_code == 200
        assert "NZ$" not in r.text, "NZ$ leaks in vehicles response"
