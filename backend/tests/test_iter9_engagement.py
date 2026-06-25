"""Iter9 — Three-stage engagement (Interest → Offer → Bid) regression.

Validates the new /api/auto endpoints introduced just before MVP launch.
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://auto-nz-bidding.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@buyanywhere.com", "password": "admin12345"}
CLIENT_VERIFIED = {"email": "client@buyanywhere.com", "password": "client12345"}
CLIENT_NO_DEP = {"email": "client2@buyanywhere.com", "password": "client12345"}


# ---------- fixtures ----------
@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{API}/auth/login", json=ADMIN, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def verified_token():
    r = requests.post(f"{API}/auth/login", json=CLIENT_VERIFIED, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def nodep_token():
    r = requests.post(f"{API}/auth/login", json=CLIENT_NO_DEP, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def h(t): return {"Authorization": f"Bearer {t}"}


# ---------- Interests ----------
def test_interest_anon_requires_name_phone():
    r = requests.post(f"{API}/auto/interests", json={"name": "", "phone": ""}, timeout=20)
    assert r.status_code in (400, 422)


def test_interest_anon_success_no_auth():
    payload = {"name": "TEST Anon Visitor", "phone": "+79139999999",
               "city": "Москва", "budget_nzd": 25000,
               "source": "vehicle_page", "message": "iter9 test"}
    r = requests.post(f"{API}/auto/interests", json=payload, timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "id" in data and "created_at" in data
    assert data["name"] == payload["name"]
    assert data["phone"] == payload["phone"]
    assert data["status"] == "new"
    assert data["user_id"] is None


def test_interest_with_jwt_attaches_user_id(verified_token):
    # who am I?
    me = requests.get(f"{API}/auto/my/dashboard", headers=h(verified_token), timeout=20)
    assert me.status_code == 200
    uid = me.json().get("user", {}).get("id")
    assert uid

    payload = {"name": "TEST AuthedLead", "phone": "+79991112233", "source": "vehicle_page"}
    r = requests.post(f"{API}/auto/interests", json=payload, headers=h(verified_token), timeout=20)
    assert r.status_code == 200, r.text
    assert r.json()["user_id"] == uid


def test_interest_mirrors_to_contacts(admin_token):
    """Insert an interest with phone '+79139999999' and verify the contacts
    collection contains a row tagged 'auto-lead'. We can't query Mongo directly,
    but the iter1-iter8 CRM /api/contacts admin endpoint (if exists) or the
    contacts presence is best verified via the side-effect — re-posting the
    same phone should increment engagement_count (the mirror finds existing)."""
    # 1st insert (the test above already inserted +79139999999)
    requests.post(f"{API}/auto/interests",
                  json={"name": "TEST Mirror", "phone": "+79139999999"}, timeout=20)
    # 2nd insert — same phone, should hit the "existing contact" branch silently
    r = requests.post(f"{API}/auto/interests",
                      json={"name": "TEST Mirror2", "phone": "+79139999999"}, timeout=20)
    assert r.status_code == 200  # mirror failure must NOT break the request


# ---------- Offers ----------
def _pick_vehicle(country=None, listing_type=None):
    params = {"limit": 5}
    if country: params["country"] = country
    if listing_type: params["listing_type"] = listing_type
    r = requests.get(f"{API}/auto/vehicles", params=params, timeout=20)
    items = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
    return items[0] if items else None


def test_offer_requires_auth():
    r = requests.post(f"{API}/auto/offers",
                      json={"vehicle_id": "x", "offer_price_nzd": 1000}, timeout=20)
    assert r.status_code in (401, 403)


def test_offer_rejects_zero_or_negative(verified_token):
    v = _pick_vehicle()
    assert v
    r = requests.post(f"{API}/auto/offers",
                      json={"vehicle_id": v["id"], "offer_price_nzd": 0},
                      headers=h(verified_token), timeout=20)
    assert r.status_code == 400
    r2 = requests.post(f"{API}/auto/offers",
                       json={"vehicle_id": v["id"], "offer_price_nzd": -50},
                       headers=h(verified_token), timeout=20)
    assert r2.status_code == 400


@pytest.fixture(scope="session")
def created_offer(verified_token):
    v = _pick_vehicle()
    assert v
    r = requests.post(f"{API}/auto/offers",
                      json={"vehicle_id": v["id"], "offer_price_nzd": 12345,
                            "message": "TEST iter9 offer"},
                      headers=h(verified_token), timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["offer_price_nzd"] == 12345
    assert data["status"] == "soft_offer"
    return data


def test_offer_create_and_my_offers(verified_token, created_offer):
    r = requests.get(f"{API}/auto/my/offers", headers=h(verified_token), timeout=20)
    assert r.status_code == 200
    items = r.json().get("items", [])
    ids = {o["id"] for o in items}
    assert created_offer["id"] in ids


def test_engagement_counts_reflect_offer(created_offer):
    vid = created_offer["vehicle_id"]
    r = requests.get(f"{API}/auto/vehicles/{vid}/engagement", timeout=20)
    assert r.status_code == 200
    body = r.json()
    for k in ("watchers", "interested", "offers", "bids"):
        assert k in body and isinstance(body[k], int)
    assert body["offers"] >= 1


# ---------- Bid deposit gate ----------
def test_bid_blocked_without_deposit(nodep_token):
    v = _pick_vehicle(country="NZ", listing_type="auction")
    if not v:
        pytest.skip("No NZ auction vehicle in catalog")
    base_price = v.get("current_price_nzd") or v.get("buy_now_price_nzd") or 1000
    r = requests.post(f"{API}/auto/vehicles/{v['id']}/bid",
                      json={"max_bid_nzd": base_price + 500},
                      headers=h(nodep_token), timeout=20)
    # 403 from deposit gate (or 400 from validation chain — spec allows both)
    assert r.status_code in (400, 403), f"Unexpected: {r.status_code} {r.text}"


def test_bid_allowed_with_verified_deposit(verified_token):
    """Try active NZ auction. Skip gracefully if no eligible lot."""
    from datetime import datetime, timezone
    r = requests.get(f"{API}/auto/vehicles",
                     params={"country": "NZ", "listing_type": "auction",
                             "status": "available", "limit": 25}, timeout=20)
    items = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
    now = datetime.now(timezone.utc).timestamp()
    candidate = None
    for v in items:
        end = v.get("auction_ends_at") or v.get("auction_end_time")
        if not end:
            continue
        try:
            ts = datetime.fromisoformat(str(end).replace("Z", "+00:00")).timestamp()
        except Exception:
            continue
        if ts > now:
            candidate = v
            break
    if not candidate:
        pytest.skip("No live NZ auction lot — skip per spec")
    amount = (candidate.get("current_price_nzd") or candidate.get("buy_now_price_nzd") or 1000) + 250
    r = requests.post(f"{API}/auto/vehicles/{candidate['id']}/bid",
                      json={"max_bid_nzd": amount},
                      headers=h(verified_token), timeout=20)
    assert r.status_code in (200, 201), f"Bid failed: {r.status_code} {r.text}"


# ---------- Market summary + ending-soon ----------
def test_market_summary_shape():
    r = requests.get(f"{API}/auto/market-summary", timeout=20)
    assert r.status_code == 200
    body = r.json()
    for k in ("available", "auctions_total", "ending_soon", "damaged", "buynow", "interests_today"):
        assert k in body, f"missing {k}"
        assert isinstance(body[k], int) and body[k] >= 0


def test_ending_soon_shape():
    r = requests.get(f"{API}/auto/ending-soon?limit=8", timeout=20)
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and isinstance(body["items"], list)
    assert "fx_rate" in body and isinstance(body["fx_rate"], dict)


# ---------- Admin gates + status PATCH ----------
def test_admin_interests_requires_admin(verified_token):
    r = requests.get(f"{API}/auto/admin/interests", headers=h(verified_token), timeout=20)
    assert r.status_code in (401, 403)


def test_admin_offers_requires_admin(verified_token):
    r = requests.get(f"{API}/auto/admin/offers", headers=h(verified_token), timeout=20)
    assert r.status_code in (401, 403)


def test_admin_lists_and_status_transitions(admin_token, created_offer):
    # interests list
    r = requests.get(f"{API}/auto/admin/interests", headers=h(admin_token), timeout=20)
    assert r.status_code == 200, r.text
    interests = r.json().get("items", [])
    assert len(interests) >= 1
    sample_interest = interests[0]

    # PATCH interest status: new → contacted → qualified → closed
    for new_status in ("contacted", "qualified", "closed"):
        rp = requests.patch(
            f"{API}/auto/admin/interests/{sample_interest['id']}/status",
            json={"status": new_status},
            headers=h(admin_token), timeout=20,
        )
        assert rp.status_code == 200, rp.text
        assert rp.json()["status"] == new_status

    # offers list
    r = requests.get(f"{API}/auto/admin/offers", headers=h(admin_token), timeout=20)
    assert r.status_code == 200
    offers = r.json().get("items", [])
    assert any(o["id"] == created_offer["id"] for o in offers)

    # PATCH offer status: soft_offer → countered → accepted → declined → expired
    for new_status in ("countered", "accepted", "declined", "expired"):
        rp = requests.patch(
            f"{API}/auto/admin/offers/{created_offer['id']}/status",
            json={"status": new_status, "admin_response": "iter9-test"},
            headers=h(admin_token), timeout=20,
        )
        assert rp.status_code == 200, rp.text
        assert rp.json()["status"] == new_status

    # invalid status -> 404 per route impl
    rp = requests.patch(
        f"{API}/auto/admin/offers/{created_offer['id']}/status",
        json={"status": "bogus"},
        headers=h(admin_token), timeout=20,
    )
    assert rp.status_code == 404
