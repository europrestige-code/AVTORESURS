"""BuyAnywhere Auto module - comprehensive backend API tests.

Tests cover: auth, vehicle catalog/filters, bidding rules (deposit gate, equal-bid,
AU rule, outbid), watchlist, inquiry, deposit upload+admin verify, admin CRUD,
AI translate/summary, importer, and legacy endpoints.
"""
import os
import time
import uuid
import pytest
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path("/app/frontend/.env"))
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@buyanywhere.com", "password": "admin12345"}
CLIENT = {"email": "client@buyanywhere.com", "password": "client12345"}
CLIENT2 = {"email": "client2@buyanywhere.com", "password": "client12345"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=20)
    assert r.status_code == 200, f"login failed for {creds['email']}: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin_token():
    return _login(ADMIN)


@pytest.fixture(scope="session")
def client_token():
    return _login(CLIENT)


@pytest.fixture(scope="session")
def client2_token():
    return _login(CLIENT2)


@pytest.fixture(scope="session")
def all_vehicles():
    r = requests.get(f"{API}/auto/vehicles", params={"limit": 100}, timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    return data["items"] if isinstance(data, dict) else data


@pytest.fixture(scope="session")
def nz_auction_vehicle(all_vehicles):
    for v in all_vehicles:
        if v.get("country") == "NZ" and v.get("listing_type") == "auction" and v.get("status") != "hidden":
            return v
    pytest.skip("No NZ auction vehicle found in seed data")


@pytest.fixture(scope="session")
def au_vehicle(all_vehicles):
    for v in all_vehicles:
        if v.get("country") == "AU":
            return v
    pytest.skip("No AU vehicle found in seed data")


# ------------- Legacy endpoints -------------

class TestLegacy:
    def test_root(self):
        r = requests.get(f"{API}/", timeout=10)
        assert r.status_code == 200
        assert "message" in r.json()

    def test_currency_info(self):
        r = requests.get(f"{API}/currency-info", timeout=10)
        assert r.status_code == 200


# ------------- Auth -------------

class TestAuth:
    def test_admin_login(self):
        t = _login(ADMIN)
        assert isinstance(t, str) and len(t) > 20

    def test_client_login(self):
        t = _login(CLIENT)
        assert isinstance(t, str)

    def test_client2_login(self):
        t = _login(CLIENT2)
        assert isinstance(t, str)


# ------------- Vehicle catalog -------------

class TestVehicles:
    def test_list_vehicles_seeded(self, all_vehicles):
        assert len(all_vehicles) >= 12, f"expected >=12 seeded vehicles, got {len(all_vehicles)}"

    def test_filter_country_nz(self):
        r = requests.get(f"{API}/auto/vehicles", params={"country": "NZ", "limit": 100}, timeout=15)
        assert r.status_code == 200
        items = r.json()["items"] if isinstance(r.json(), dict) else r.json()
        assert all(v["country"] == "NZ" for v in items)
        assert len(items) >= 1

    def test_filter_listing_type_auction(self):
        r = requests.get(f"{API}/auto/vehicles", params={"listing_type": "auction", "limit": 100}, timeout=15)
        assert r.status_code == 200
        items = r.json()["items"] if isinstance(r.json(), dict) else r.json()
        assert all(v["listing_type"] == "auction" for v in items)

    def test_filter_search_toyota(self):
        r = requests.get(f"{API}/auto/vehicles", params={"search": "Toyota", "limit": 100}, timeout=15)
        assert r.status_code == 200
        items = r.json()["items"] if isinstance(r.json(), dict) else r.json()
        assert len(items) >= 1

    def test_filter_year_price_range(self):
        r = requests.get(f"{API}/auto/vehicles", params={"year_from": 2010, "year_to": 2025, "price_from": 1000, "price_to": 500000, "limit": 100}, timeout=15)
        assert r.status_code == 200

    def test_pagination(self):
        r = requests.get(f"{API}/auto/vehicles", params={"limit": 2, "offset": 0}, timeout=15)
        assert r.status_code == 200
        body = r.json()
        items = body["items"] if isinstance(body, dict) else body
        assert len(items) <= 2

    def test_get_vehicle_detail(self, all_vehicles):
        vid = all_vehicles[0]["id"]
        r = requests.get(f"{API}/auto/vehicles/{vid}", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["id"] == vid
        assert "highest_bid_nzd" in d
        assert "bid_count" in d
        assert "price_breakdown" in d

    def test_highest_bid_endpoint(self, all_vehicles):
        vid = all_vehicles[0]["id"]
        r = requests.get(f"{API}/auto/vehicles/{vid}/highest-bid", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["vehicle_id"] == vid
        assert "highest_bid_nzd" in d
        assert "bid_count" in d


# ------------- Price breakdown -------------

class TestPriceBreakdown:
    def test_breakdown_formula(self):
        payload = {"vehicle_price_nzd": 10000, "storage_days": 3, "forklift_nzd": 0,
                   "local_transport_nzd": 500, "documentation_nzd": 250, "container_share_nzd": 3333}
        r = requests.post(f"{API}/auto/price-breakdown", json=payload, timeout=15)
        assert r.status_code == 200
        d = r.json()
        # commission = 20% of 10000 = 2000; storage = 3*50 = 150
        # total = 10000 + 2000 + 500 + 150 + 250 + 3333 = 16233
        assert abs(d.get("total_nzd", 0) - 16233) < 1, d
        assert abs(d.get("commission_nzd", 0) - 2000) < 1


# ------------- Bidding rules -------------

class TestBidding:
    def test_bid_requires_deposit_client2(self, client2_token, nz_auction_vehicle):
        h = {"Authorization": f"Bearer {client2_token}"}
        r = requests.post(f"{API}/auto/vehicles/{nz_auction_vehicle['id']}/bid",
                          json={"max_bid_nzd": 9000}, headers=h, timeout=15)
        assert r.status_code == 403, f"expected 403, got {r.status_code} {r.text}"
        body = r.text.lower()
        assert "депозит" in body or "deposit" in body

    def test_bid_happy_path_and_outbid(self, client_token, nz_auction_vehicle):
        h = {"Authorization": f"Bearer {client_token}"}
        # Find current state
        vid = nz_auction_vehicle["id"]
        cur = requests.get(f"{API}/auto/vehicles/{vid}/highest-bid", timeout=10).json()
        new_bid = float(cur.get("highest_bid_nzd") or nz_auction_vehicle.get("current_price_nzd") or 5000) + 500
        r = requests.post(f"{API}/auto/vehicles/{vid}/bid",
                          json={"max_bid_nzd": new_bid}, headers=h, timeout=20)
        assert r.status_code in (200, 201), f"bid failed: {r.status_code} {r.text}"
        # Check vehicle updated
        after = requests.get(f"{API}/auto/vehicles/{vid}", timeout=10).json()
        assert float(after.get("highest_bid_nzd") or 0) >= new_bid

    def test_equal_bid_rejected(self, client_token, nz_auction_vehicle):
        h = {"Authorization": f"Bearer {client_token}"}
        vid = nz_auction_vehicle["id"]
        cur = requests.get(f"{API}/auto/vehicles/{vid}/highest-bid", timeout=10).json()
        same = float(cur.get("highest_bid_nzd") or 0)
        if same <= 0:
            pytest.skip("No prior bid to duplicate")
        r = requests.post(f"{API}/auto/vehicles/{vid}/bid",
                          json={"max_bid_nzd": same}, headers=h, timeout=15)
        assert r.status_code == 400, f"expected 400, got {r.status_code} {r.text}"
        assert "уже существует" in r.text or "выше" in r.text

    def test_au_bidding_disabled(self, client_token, au_vehicle):
        h = {"Authorization": f"Bearer {client_token}"}
        r = requests.post(f"{API}/auto/vehicles/{au_vehicle['id']}/bid",
                          json={"max_bid_nzd": 999999}, headers=h, timeout=15)
        assert r.status_code in (400, 403), f"expected 400/403 for AU, got {r.status_code} {r.text}"


# ------------- Watchlist -------------

class TestWatchlist:
    def test_toggle(self, client_token, all_vehicles):
        h = {"Authorization": f"Bearer {client_token}"}
        vid = all_vehicles[0]["id"]
        r1 = requests.post(f"{API}/auto/vehicles/{vid}/watchlist", headers=h, timeout=15)
        assert r1.status_code == 200, r1.text
        s1 = r1.json().get("watching")
        r2 = requests.post(f"{API}/auto/vehicles/{vid}/watchlist", headers=h, timeout=15)
        assert r2.status_code == 200
        s2 = r2.json().get("watching")
        assert s1 != s2


# ------------- Inquiry -------------

class TestInquiry:
    def test_inquiry_anonymous(self, au_vehicle):
        r = requests.post(f"{API}/auto/vehicles/{au_vehicle['id']}/inquiry",
                          json={"message": "Anon inquiry TEST", "email": "anon@test.com"}, timeout=15)
        assert r.status_code in (200, 201), r.text
        assert "id" in r.json()

    def test_inquiry_authenticated(self, client_token, au_vehicle):
        h = {"Authorization": f"Bearer {client_token}"}
        r = requests.post(f"{API}/auto/vehicles/{au_vehicle['id']}/inquiry",
                          json={"message": "TEST authed inquiry"}, headers=h, timeout=15)
        assert r.status_code in (200, 201)
        assert "id" in r.json()


# ------------- Deposit flow (manual + admin verify) -------------

class TestDepositFlow:
    pending_deposit_id = None

    def test_client2_no_deposit_initially(self, client2_token):
        h = {"Authorization": f"Bearer {client2_token}"}
        r = requests.get(f"{API}/auto/my/deposit", headers=h, timeout=10)
        assert r.status_code == 200
        # before upload - either no deposit or pending one (in case re-run)
        assert r.json()["verified"] in (False,)

    def test_client2_upload_deposit(self, client2_token):
        h = {"Authorization": f"Bearer {client2_token}"}
        data = {"amount": "1000", "currency": "NZD", "method": "bank_transfer", "payment_proof_note": "wire 123 TEST"}
        r = requests.post(f"{API}/auto/deposit/upload", data=data, headers=h, timeout=20)
        assert r.status_code in (200, 201), r.text
        d = r.json()
        assert d.get("status") == "pending"
        TestDepositFlow.pending_deposit_id = d["id"]

    def test_my_deposit_pending(self, client2_token):
        h = {"Authorization": f"Bearer {client2_token}"}
        r = requests.get(f"{API}/auto/my/deposit", headers=h, timeout=10)
        assert r.status_code == 200
        assert r.json()["verified"] is False

    def test_admin_deposits_lists_pending(self, admin_token):
        h = {"Authorization": f"Bearer {admin_token}"}
        r = requests.get(f"{API}/auto/admin/deposits", headers=h, timeout=15)
        assert r.status_code == 200
        ids = [d["id"] for d in r.json()]
        if TestDepositFlow.pending_deposit_id:
            assert TestDepositFlow.pending_deposit_id in ids

    def test_non_admin_cannot_list_deposits(self, client_token):
        h = {"Authorization": f"Bearer {client_token}"}
        r = requests.get(f"{API}/auto/admin/deposits", headers=h, timeout=10)
        assert r.status_code == 403

    def test_admin_verify_deposit(self, admin_token):
        if not TestDepositFlow.pending_deposit_id:
            pytest.skip("No pending deposit captured")
        h = {"Authorization": f"Bearer {admin_token}"}
        r = requests.put(f"{API}/auto/admin/deposits/{TestDepositFlow.pending_deposit_id}/verify",
                         json={"note": "test verify"}, headers=h, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json().get("status") == "verified"

    def test_client2_can_bid_after_verify(self, client2_token, nz_auction_vehicle):
        h = {"Authorization": f"Bearer {client2_token}"}
        vid = nz_auction_vehicle["id"]
        cur = requests.get(f"{API}/auto/vehicles/{vid}/highest-bid", timeout=10).json()
        bid_val = float(cur.get("highest_bid_nzd") or 0) + 250
        r = requests.post(f"{API}/auto/vehicles/{vid}/bid",
                          json={"max_bid_nzd": bid_val}, headers=h, timeout=20)
        assert r.status_code in (200, 201), f"client2 bid after verify failed: {r.status_code} {r.text}"


# ------------- Admin vehicle CRUD -------------

class TestAdminVehicles:
    created_id = None

    def test_create(self, admin_token):
        h = {"Authorization": f"Bearer {admin_token}"}
        payload = {"title_ru": "Тест TEST", "country": "NZ", "listing_type": "auction",
                   "current_price_nzd": 5000}
        r = requests.post(f"{API}/auto/admin/vehicles", json=payload, headers=h, timeout=15)
        assert r.status_code in (200, 201), r.text
        TestAdminVehicles.created_id = r.json()["id"]

    def test_update(self, admin_token):
        if not TestAdminVehicles.created_id:
            pytest.skip("no created vehicle")
        h = {"Authorization": f"Bearer {admin_token}"}
        r = requests.put(f"{API}/auto/admin/vehicles/{TestAdminVehicles.created_id}",
                         json={"current_price_nzd": 6000}, headers=h, timeout=15)
        assert r.status_code == 200, r.text
        assert float(r.json().get("current_price_nzd") or 0) == 6000

    def test_delete(self, admin_token):
        if not TestAdminVehicles.created_id:
            pytest.skip()
        h = {"Authorization": f"Bearer {admin_token}"}
        r = requests.delete(f"{API}/auto/admin/vehicles/{TestAdminVehicles.created_id}", headers=h, timeout=15)
        assert r.status_code == 200
        # Verify status is hidden
        r2 = requests.get(f"{API}/auto/vehicles/{TestAdminVehicles.created_id}", timeout=10)
        if r2.status_code == 200:
            assert r2.json().get("status") == "hidden"


# ------------- AI endpoints -------------

class TestAI:
    def test_ai_translate(self, admin_token, all_vehicles):
        h = {"Authorization": f"Bearer {admin_token}"}
        vid = all_vehicles[0]["id"]
        r = requests.post(f"{API}/auto/admin/vehicles/{vid}/ai-translate", headers=h, timeout=90)
        assert r.status_code == 200, f"ai-translate failed: {r.status_code} {r.text[:300]}"

    def test_ai_summary(self, admin_token, all_vehicles):
        h = {"Authorization": f"Bearer {admin_token}"}
        vid = all_vehicles[0]["id"]
        r = requests.post(f"{API}/auto/admin/vehicles/{vid}/ai-summary", headers=h, timeout=90)
        assert r.status_code == 200, f"ai-summary failed: {r.status_code} {r.text[:300]}"
        body = r.json()
        # Should have result + updates (fields may be present or fallback)
        assert "result" in body


# ------------- Importer -------------

class TestImport:
    def test_import_from_text(self, admin_token):
        h = {"Authorization": f"Bearer {admin_token}"}
        payload = {"text": "2015 Mazda Demio 1.3L petrol auto 110000 km Auckland NZ$5,500"}
        r = requests.post(f"{API}/auto/admin/import/from-text", json=payload, headers=h, timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("ok") is True, d

    def test_import_from_text_save(self, admin_token):
        h = {"Authorization": f"Bearer {admin_token}"}
        payload = {"text": "2014 Honda Fit 1.3L petrol 95000 km Wellington NZ$4,800 TEST"}
        r = requests.post(f"{API}/auto/admin/import/from-text?save=true", json=payload, headers=h, timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        if d.get("ok"):
            assert "saved" in d

    def test_import_from_invalid_url(self, admin_token):
        h = {"Authorization": f"Bearer {admin_token}"}
        r = requests.post(f"{API}/auto/admin/import/from-url",
                          json={"url": "http://this-domain-does-not-exist-xyz123.invalid/x"},
                          headers=h, timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("ok") is False
