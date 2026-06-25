"""Iter10 — backend tests for AI-подборщик quiz + Deep CRM timeline."""
import os
import pytest
import requests

def _load_url():
    v = os.environ.get("REACT_APP_BACKEND_URL")
    if not v:
        # fallback: read frontend/.env directly
        try:
            with open("/app/frontend/.env") as f:
                for line in f:
                    if line.startswith("REACT_APP_BACKEND_URL"):
                        v = line.split("=", 1)[1].strip()
                        break
        except FileNotFoundError:
            pass
    assert v, "REACT_APP_BACKEND_URL must be set"
    return v.rstrip("/")


BASE_URL = _load_url()


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": "admin@buyanywhere.com", "password": "admin12345"},
                      timeout=20)
    assert r.status_code == 200, r.text
    return r.json().get("access_token")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def client_id():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": "client@buyanywhere.com", "password": "client12345"},
                      timeout=20)
    assert r.status_code == 200, r.text
    tok = r.json().get("access_token")
    me = requests.get(f"{BASE_URL}/api/auth/me",
                      headers={"Authorization": f"Bearer {tok}"}, timeout=20)
    if me.status_code == 200:
        return me.json().get("id")
    # fallback: decode-less; use admin clients listing
    return None


# ---------- Quiz meta ----------
def test_quiz_meta_structure():
    r = requests.get(f"{BASE_URL}/api/auto/quiz/meta", timeout=20)
    assert r.status_code == 200
    data = r.json()
    for key in ("budgets", "purposes", "urgencies", "countries"):
        assert key in data, f"missing {key}"
        assert isinstance(data[key], list) and len(data[key]) > 0
    # Russian labels (Cyrillic) check
    joined = " ".join([b["label"] for b in data["budgets"]])
    assert any(ord(c) > 127 for c in joined), "expected Russian/Cyrillic labels"
    keys = {b["key"] for b in data["budgets"]}
    assert {"u1m", "1_2m", "2_3m", "3_5m", "5_8m", "open"}.issubset(keys)


# ---------- Regression: /vehicles ----------
def test_vehicles_listing_regression():
    r = requests.get(f"{BASE_URL}/api/auto/vehicles?limit=5", timeout=20)
    assert r.status_code == 200
    data = r.json()
    # endpoint may return list or {items:[]}
    items = data if isinstance(data, list) else data.get("items") or data.get("vehicles") or []
    assert isinstance(items, list)


# ---------- Quiz submit validation ----------
def test_quiz_submit_missing_name_400():
    r = requests.post(f"{BASE_URL}/api/auto/quiz/submit",
                      json={"name": "", "contact": "+79991110000"}, timeout=20)
    assert r.status_code == 400, r.text


def test_quiz_submit_missing_contact_400():
    r = requests.post(f"{BASE_URL}/api/auto/quiz/submit",
                      json={"name": "TEST_quiz_user", "contact": ""}, timeout=20)
    assert r.status_code == 400, r.text


# ---------- Quiz submit happy path ----------
QUIZ_PHONE = "+79991117710"
QUIZ_PAYLOAD = {
    "name": "TEST_quiz_iter10",
    "contact": QUIZ_PHONE,
    "budget_key": "3_5m",
    "body_types": ["suv"],
    "country": "NZ",
    "purpose": "family",
    "urgency": "now",
    "city": "Владивосток",
    "notes": "iter10 test",
}


def test_quiz_submit_happy(admin_headers):
    r = requests.post(f"{BASE_URL}/api/auto/quiz/submit", json=QUIZ_PAYLOAD, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "lead" in data and "matches" in data
    lead = data["lead"]
    assert lead["name"] == QUIZ_PAYLOAD["name"]
    assert lead["contact"] == QUIZ_PHONE
    assert lead["budget_key"] == "3_5m"
    assert lead["budget_rub_max"] == 5_000_000
    assert lead["budget_nzd_max"] and lead["budget_nzd_max"] > 0
    assert lead["country"] == "NZ"
    assert lead["body_types"] == ["suv"]
    assert "matches" in data
    assert isinstance(data["matches"], list)
    # Mirror into auto_interests should make this phone show up in admin clients
    clients_r = requests.get(f"{BASE_URL}/api/auto/admin/clients?limit=500",
                             headers=admin_headers, timeout=30)
    assert clients_r.status_code == 200
    clients = clients_r.json()
    found = [c for c in clients if c.get("phone") == QUIZ_PHONE and c.get("kind") == "lead"]
    assert found, "Quiz lead phone should appear in admin/clients as kind=lead"


def test_quiz_matches_non_empty():
    # Use a relaxed search to maximise chance of matches
    payload = {
        "name": "TEST_quiz_match",
        "contact": "+79991117711",
        "budget_key": "open",
        "body_types": [],
        "country": None,
        "purpose": "family",
        "urgency": "watch",
    }
    r = requests.post(f"{BASE_URL}/api/auto/quiz/submit", json=payload, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert len(data["matches"]) >= 1, "expected at least 1 match for open budget"
    m = data["matches"][0]
    assert "id" in m
    assert "title_ru" in m


# ---------- Admin clients listing shape ----------
def test_admin_clients_shape(admin_headers):
    r = requests.get(f"{BASE_URL}/api/auto/admin/clients?limit=500",
                     headers=admin_headers, timeout=30)
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list) and len(items) > 0
    # Required fields per spec
    required = {"kind", "interests", "offers", "bids", "chat_messages",
                "quiz_leads", "last_activity", "total_events"}
    sample = items[0]
    assert required.issubset(sample.keys()), \
        f"missing fields: {required - set(sample.keys())}"
    kinds = {c.get("kind") for c in items}
    assert "user" in kinds, "should contain kind=user"
    assert "lead" in kinds, "should contain kind=lead"


def test_admin_clients_unauthorized():
    r = requests.get(f"{BASE_URL}/api/auto/admin/clients", timeout=20)
    assert r.status_code in (401, 403)


# ---------- Admin timeline (user) ----------
def test_admin_client_timeline_user(admin_headers):
    # find client@buyanywhere.com id via admin/clients
    r = requests.get(f"{BASE_URL}/api/auto/admin/clients?limit=500",
                     headers=admin_headers, timeout=30)
    assert r.status_code == 200
    client_row = next((c for c in r.json()
                       if c.get("kind") == "user" and c.get("email") == "client@buyanywhere.com"),
                      None)
    assert client_row, "client@buyanywhere.com not in admin/clients list"
    uid = client_row["id"]
    tl = requests.get(f"{BASE_URL}/api/auto/admin/clients/{uid}/timeline",
                      headers=admin_headers, timeout=30)
    assert tl.status_code == 200, tl.text
    body = tl.json()
    assert "client" in body and "events" in body
    assert body["client"] and body["client"].get("email") == "client@buyanywhere.com"
    assert isinstance(body["events"], list)
    # Sorted desc by 'at'
    ats = [e.get("at") for e in body["events"] if e.get("at")]
    assert ats == sorted(ats, reverse=True), "events not sorted desc by at"
    types_allowed = {"interest", "offer", "bid", "chat", "deposit", "quiz"}
    for e in body["events"]:
        assert e.get("type") in types_allowed


def test_admin_client_timeline_user_404(admin_headers):
    r = requests.get(f"{BASE_URL}/api/auto/admin/clients/__nope__/timeline",
                     headers=admin_headers, timeout=20)
    assert r.status_code == 404


# ---------- Admin timeline (anonymous lead) ----------
def test_admin_lead_timeline_anon(admin_headers):
    # Ensure quiz lead from earlier exists
    r = requests.get(
        f"{BASE_URL}/api/auto/admin/clients/lead/{QUIZ_PHONE}/timeline",
        headers=admin_headers, timeout=20,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["client"]["kind"] == "lead"
    assert data["client"]["phone"] == QUIZ_PHONE
    assert isinstance(data["events"], list)
    # Should contain at least one quiz event (we just submitted it)
    types = {e["type"] for e in data["events"]}
    assert "quiz" in types or "interest" in types, f"types found: {types}"
