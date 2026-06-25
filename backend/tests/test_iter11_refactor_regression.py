"""Iter11 — regression after auto_routes.py refactor into routes/auto/ sub-routers.

Endpoints/payloads/shapes MUST be byte-identical to iter10.
"""
import os
import pytest
import requests


def _load_url():
    v = os.environ.get("REACT_APP_BACKEND_URL")
    if not v:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL"):
                    v = line.split("=", 1)[1].strip()
                    break
    assert v, "REACT_APP_BACKEND_URL must be set"
    return v.rstrip("/")


BASE_URL = _load_url()


@pytest.fixture(scope="module")
def admin_headers():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "admin@buyanywhere.com", "password": "admin12345"},
        timeout=20,
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def client_headers():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "client@buyanywhere.com", "password": "client12345"},
        timeout=20,
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ---------- chat_quiz sub-router ----------
def test_quiz_meta_200():
    r = requests.get(f"{BASE_URL}/api/auto/quiz/meta", timeout=20)
    assert r.status_code == 200
    data = r.json()
    for k in ("budgets", "purposes", "urgencies", "countries"):
        assert isinstance(data.get(k), list) and len(data[k]) > 0


def test_quiz_submit_happy():
    payload = {
        "name": "TEST_iter11_quiz",
        "contact": "+79991117811",
        "budget_key": "open",
        "body_types": [],
        "purpose": "family",
        "urgency": "watch",
    }
    r = requests.post(f"{BASE_URL}/api/auto/quiz/submit", json=payload, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "lead" in data and "matches" in data
    assert data["lead"]["contact"] == "+79991117811"


def test_quiz_submit_400_empty_name():
    r = requests.post(
        f"{BASE_URL}/api/auto/quiz/submit",
        json={"name": "", "contact": "+79991110001"}, timeout=20,
    )
    assert r.status_code == 400


def test_quiz_submit_400_empty_contact():
    r = requests.post(
        f"{BASE_URL}/api/auto/quiz/submit",
        json={"name": "TEST_iter11", "contact": ""}, timeout=20,
    )
    assert r.status_code == 400


def test_chat_post_any_message():
    r = requests.post(
        f"{BASE_URL}/api/auto/chat",
        json={"message": "Привет, что есть из Toyota?"},
        timeout=60,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, dict) and len(data) > 0


# ---------- engagement sub-router ----------
def test_vehicles_200():
    r = requests.get(f"{BASE_URL}/api/auto/vehicles?limit=5", timeout=30)
    assert r.status_code == 200
    items = r.json() if isinstance(r.json(), list) else r.json().get("items") or r.json().get("vehicles") or []
    assert isinstance(items, list)


def test_interests_anonymous():
    # "Anonymous" = no Bearer token but name/phone provided in body
    payload = {
        "vehicle_id": None,
        "vehicle_title_ru": "TEST_iter11 anon interest",
        "name": "TEST_iter11_anon",
        "phone": "+79991117813",
        "message": "iter11 anon",
    }
    r = requests.post(f"{BASE_URL}/api/auto/interests", json=payload, timeout=30)
    assert r.status_code in (200, 201), r.text
    data = r.json()
    assert isinstance(data, dict)


def test_interests_with_name_phone():
    payload = {
        "vehicle_id": None,
        "vehicle_title_ru": "TEST_iter11 named interest",
        "name": "TEST_iter11_user",
        "phone": "+79991117812",
        "message": "iter11 named",
    }
    r = requests.post(f"{BASE_URL}/api/auto/interests", json=payload, timeout=30)
    assert r.status_code in (200, 201), r.text
    data = r.json()
    assert isinstance(data, dict)


def test_market_summary_200():
    r = requests.get(f"{BASE_URL}/api/auto/market-summary", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, dict)


def test_ending_soon_200():
    r = requests.get(f"{BASE_URL}/api/auto/ending-soon", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    # Accept list or dict-with-items
    assert isinstance(data, (list, dict))


def test_offers_requires_bearer_401():
    payload = {"vehicle_id": "any", "offer_nzd": 10000}
    r = requests.post(f"{BASE_URL}/api/auto/offers", json=payload, timeout=20)
    assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code} {r.text}"


# ---------- admin_crm sub-router ----------
def test_admin_interests_auth(admin_headers):
    r = requests.get(f"{BASE_URL}/api/auto/admin/interests", headers=admin_headers, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, (list, dict))


def test_admin_interests_unauthorized():
    r = requests.get(f"{BASE_URL}/api/auto/admin/interests", timeout=20)
    assert r.status_code in (401, 403)


def test_admin_clients_auth(admin_headers):
    r = requests.get(
        f"{BASE_URL}/api/auto/admin/clients?limit=500", headers=admin_headers, timeout=30
    )
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list) and len(items) > 0
    required = {"kind", "interests", "offers", "bids", "chat_messages",
                "quiz_leads", "last_activity", "total_events"}
    assert required.issubset(items[0].keys())


def test_admin_client_timeline(admin_headers):
    r = requests.get(
        f"{BASE_URL}/api/auto/admin/clients?limit=500", headers=admin_headers, timeout=30
    )
    row = next((c for c in r.json()
                if c.get("kind") == "user" and c.get("email") == "client@buyanywhere.com"), None)
    assert row, "client@buyanywhere.com not found"
    tl = requests.get(
        f"{BASE_URL}/api/auto/admin/clients/{row['id']}/timeline",
        headers=admin_headers, timeout=30,
    )
    assert tl.status_code == 200
    body = tl.json()
    assert "client" in body and "events" in body
    assert isinstance(body["events"], list)
