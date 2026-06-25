"""Iter16 — tiered payment-terms tests.

Covers:
- GET /api/auto/payment-terms (public disclosure)
- GET /api/auto/vehicles/{id}/deposit-required for base/tier1/tier2
- 404 on garbage vehicle id
- POST /api/auto/vehicles/{id}/bid enforces required deposit (tier1 with NZ$1,000 deposit -> 403)
"""
import os
import sys
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")

# Allow importing services for unit-style tier2 helper assertion
sys.path.insert(0, "/app/backend")

TIER1_VEHICLE_ID = "1f49c4c5-4f6a-44d8-a1fa-d6ff43579a88"


@pytest.fixture(scope="module")
def client_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "client@buyanywhere.com", "password": "client12345"},
        timeout=15,
    )
    assert r.status_code == 200, f"login failed {r.status_code} {r.text}"
    return r.json()["access_token"]


# ---- payment-terms summary endpoint ----

def test_payment_terms_summary():
    r = requests.get(f"{BASE_URL}/api/auto/payment-terms", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert "version" in data
    assert data["base_deposit_nzd"] == 1000
    assert data["tier1_threshold_nzd"] == 20000
    assert data["tier1_percent"] == 20
    assert data["tier2_threshold_nzd"] == 40000
    assert data["tier2_percent"] == 30
    assert data["full_payment_window_hours"] == 24
    bullets = data.get("bullets_ru")
    assert isinstance(bullets, list) and len(bullets) >= 5
    # All bullets should be Russian text — check at least one Cyrillic char
    for b in bullets:
        assert any("\u0400" <= ch <= "\u04ff" for ch in b), f"non-russian bullet: {b}"


# ---- per-vehicle deposit-required ----

def test_deposit_required_tier1_hilux():
    r = requests.get(
        f"{BASE_URL}/api/auto/vehicles/{TIER1_VEHICLE_ID}/deposit-required", timeout=15
    )
    assert r.status_code == 200, r.text
    data = r.json()
    req = data["required"]
    assert req["tier"] == "tier1"
    assert req["percent"] == 20
    # price is 24500 -> 4900
    assert abs(req["amount_nzd"] - 4900.0) < 0.01
    assert req["is_percent"] is True


def test_deposit_required_base_cheap_lot():
    # find a cheap vehicle <= 20000
    r = requests.get(
        f"{BASE_URL}/api/auto/vehicles?limit=100&price_to=20000",
        timeout=20,
    )
    assert r.status_code == 200
    payload = r.json()
    items = payload.get("items") if isinstance(payload, dict) else payload
    assert items, "expected at least one vehicle <= 20000"
    chosen = None
    for v in items:
        p = v.get("current_price_nzd") or 0
        if 0 < p <= 20000:
            chosen = v
            break
    if not chosen:
        # fall back to any item, the helper will still return base if price is 0/<=20000
        chosen = items[0]
    vid = chosen["id"]
    r2 = requests.get(
        f"{BASE_URL}/api/auto/vehicles/{vid}/deposit-required", timeout=15
    )
    assert r2.status_code == 200, r2.text
    req = r2.json()["required"]
    assert req["tier"] == "base"
    assert req["amount_nzd"] == 1000
    assert req["is_percent"] is False


def test_deposit_required_tier2_via_helper():
    """If no >40K vehicle in live catalog, hit the helper directly."""
    from services.auto_payment_terms import required_deposit_nzd
    res = required_deposit_nzd({"current_price_nzd": 55000})
    assert res["tier"] == "tier2"
    assert res["percent"] == 30
    assert abs(res["amount_nzd"] - 16500.0) < 0.01
    assert res["is_percent"] is True


def test_deposit_required_garbage_id_404():
    r = requests.get(
        f"{BASE_URL}/api/auto/vehicles/garbage-id/deposit-required", timeout=15
    )
    assert r.status_code == 404


# ---- bid enforcement ----

def test_bid_blocked_when_deposit_insufficient(client_token):
    """client@buyanywhere.com has NZ$1,000 verified deposit. Tier1 needs >$1,000 → expect 403.

    Spec asked us to test the Hilux SR5 (1f49c4c5-...) but that vehicle in seed data is
    country=AU + listing_type=inquiry_only, so the bid is rejected with 400 before the
    deposit gate fires. We therefore pick a real NZ auction tier1 lot (price 20K-40K) and
    assert the 403 deposit gate triggers and includes the required amount."""
    headers = {"Authorization": f"Bearer {client_token}"}
    # Find an NZ auction tier1 vehicle
    r0 = requests.get(
        f"{BASE_URL}/api/auto/vehicles?country=NZ&listing_type=auction&price_from=20001&price_to=40000&limit=10",
        timeout=20,
    )
    assert r0.status_code == 200
    payload = r0.json()
    items = payload.get("items") if isinstance(payload, dict) else payload
    assert items, "expected at least one NZ auction tier1 vehicle"
    vid = items[0]["id"]
    price = items[0].get("current_price_nzd") or 0
    expected_deposit = round(price * 0.2)

    r = requests.post(
        f"{BASE_URL}/api/auto/vehicles/{vid}/bid",
        json={"max_bid_nzd": price + 1000},
        headers=headers,
        timeout=20,
    )
    assert r.status_code == 403, f"expected 403 got {r.status_code} {r.text}"
    body = r.text
    # error message must include required amount
    amt_str = f"{expected_deposit:,.0f}"  # e.g. 7,000 for $35K
    assert (str(expected_deposit) in body) or (amt_str in body) or (amt_str.replace(",", "") in body), (
        f"required amount {expected_deposit} not in error body: {body}"
    )
