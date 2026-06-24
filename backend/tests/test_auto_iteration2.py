"""Iteration 2: tests for new endpoints — transport cost, auctions calendar,
price-breakdown with branch_or_city + non-runner, and vehicle detail for Russian city.
"""
import os
import pytest
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path("/app/frontend/.env"))
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@buyanywhere.com", "password": "admin12345"}
CLIENT = {"email": "client@buyanywhere.com", "password": "client12345"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin_token():
    return _login(ADMIN)


@pytest.fixture(scope="session")
def client_token():
    return _login(CLIENT)


# ---------- Transport cost ----------

class TestTransportCost:
    def test_wellington_non_runner(self):
        r = requests.get(f"{API}/auto/transport/cost",
                         params={"branch": "Wellington", "non_runner": "true"}, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["runner_nzd"] == 680
        assert d["multiplier"] == 2.0
        assert d["transport_nzd"] == 1360
        assert d["matched"] is True

    def test_auckland_runner(self):
        r = requests.get(f"{API}/auto/transport/cost",
                         params={"branch": "Auckland", "non_runner": "false"}, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["runner_nzd"] == 0
        assert d["multiplier"] == 1.0
        assert d["transport_nzd"] == 0
        assert d["matched"] is True

    def test_pricing_table(self):
        r = requests.get(f"{API}/auto/transport/pricing", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "runner_nzd_by_branch" in d
        assert isinstance(d["runner_nzd_by_branch"], dict)
        assert len(d["runner_nzd_by_branch"]) >= 20

    def test_unknown_branch_fallback(self):
        r = requests.get(f"{API}/auto/transport/cost",
                         params={"branch": "Атлантида", "non_runner": "false"}, timeout=15)
        assert r.status_code == 200
        d = r.json()
        # Falls back to 500 legacy default, matched=False
        assert d["matched"] is False
        assert d["runner_nzd"] == 500


# ---------- Price breakdown with branch + non-runner ----------

class TestPriceBreakdownBranch:
    def test_christchurch_non_runner(self):
        payload = {"vehicle_price_nzd": 8000, "branch_or_city": "Christchurch", "is_non_runner": True}
        r = requests.post(f"{API}/auto/price-breakdown", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("local_transport_nzd") == 2500
        td = d.get("transport_detail") or {}
        assert td.get("runner_nzd") == 1250
        assert td.get("multiplier") == 2.0
        assert d.get("total_nzd") == 15683

    def test_legacy_back_compat_no_branch(self):
        payload = {"vehicle_price_nzd": 10000, "storage_days": 0}
        r = requests.post(f"{API}/auto/price-breakdown", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        # legacy default 500
        assert d.get("local_transport_nzd") == 500


# ---------- Auctions calendar ----------

class TestAuctionsCalendar:
    def test_calendar_basic_shape(self):
        r = requests.get(f"{API}/auto/auctions/calendar",
                         params={"days_ahead": 21}, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "count" in d
        assert "events" in d
        assert "by_day" in d
        assert isinstance(d["events"], list)
        assert isinstance(d["by_day"], list)
        # buckets sum equals total events
        # each bucket has either 'events' (per current impl) or 'count'
        bucket_sum = sum(b.get("events", b.get("count", 0)) for b in d["by_day"])
        assert bucket_sum == d["count"], f"bucket sum {bucket_sum} != events {d['count']}"
        # each event sanity check
        for ev in d["events"]:
            assert ev.get("source") == "turners"
            assert ev.get("starts_at"), "missing starts_at"
            assert "lots" in ev
            assert isinstance(ev["lots"], int)
            url = ev.get("auction_url") or ""
            assert "turners.co.nz" in url

    def test_calendar_filter_by_city(self):
        r = requests.get(f"{API}/auto/auctions/calendar",
                         params={"city": "Christchurch", "days_ahead": 21}, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        for ev in d["events"]:
            city = (ev.get("city") or "").lower()
            assert "christchurch" in city, f"event not Christchurch: {ev}"

    def test_admin_refresh_requires_auth(self):
        r = requests.post(f"{API}/auto/admin/auctions/refresh",
                          json={"categories": ["cars"]}, timeout=60)
        assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"

    def test_admin_refresh_with_token(self, admin_token):
        h = {"Authorization": f"Bearer {admin_token}"}
        r = requests.post(f"{API}/auto/admin/auctions/refresh",
                          json={"categories": ["cars"]}, headers=h, timeout=120)
        # If external network blocked, fetched may be 0 but must be 200
        assert r.status_code == 200, r.text
        d = r.json()
        assert "fetched" in d
        assert isinstance(d["fetched"], int)
        assert "by_category" in d
        assert "at" in d


# ---------- Vehicle detail with Russian city ----------

class TestVehicleRussianCity:
    def test_vehicle_with_russian_location_does_not_500(self, admin_token):
        h = {"Authorization": f"Bearer {admin_token}"}
        # Create test vehicle with Russian location
        payload = {
            "title_ru": "TEST Russian location",
            "country": "NZ",
            "listing_type": "auction",
            "current_price_nzd": 5000,
            "location": "Веллингтон",
        }
        r = requests.post(f"{API}/auto/admin/vehicles", json=payload, headers=h, timeout=20)
        assert r.status_code in (200, 201), r.text
        vid = r.json()["id"]
        try:
            g = requests.get(f"{API}/auto/vehicles/{vid}", timeout=15)
            assert g.status_code == 200, g.text
            d = g.json()
            assert "price_breakdown" in d
            pb = d["price_breakdown"]
            # transport_detail should be present and contain a transport_nzd value (either matched or legacy)
            td = pb.get("transport_detail")
            assert td is not None, "transport_detail missing"
            assert "transport_nzd" in td
        finally:
            requests.delete(f"{API}/auto/admin/vehicles/{vid}?hard=true", headers=h, timeout=15)
