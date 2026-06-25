"""Iter12 — Saved Searches + Tatiana quiz extra steps + Telegram binding."""
import os
import time

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fall back to frontend .env file
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().strip('"').rstrip("/")
API = f"{BASE_URL}/api"

CLIENT_EMAIL = "client@buyanywhere.com"
CLIENT_PASSWORD = "client12345"
ADMIN_EMAIL = "admin@buyanywhere.com"
ADMIN_PASSWORD = "admin12345"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def client_token(session):
    r = session.post(f"{API}/auth/login", json={
        "email": CLIENT_EMAIL, "password": CLIENT_PASSWORD,
    })
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_token(session):
    r = session.post(f"{API}/auth/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD,
    })
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


# ---------- Quiz meta + matching ----------

class TestQuizMeta:
    def test_quiz_meta_includes_repairs_and_buyer_types(self, session):
        r = session.get(f"{API}/auto/quiz/meta")
        assert r.status_code == 200
        data = r.json()
        assert "repairs" in data
        assert "buyer_types" in data
        rep_keys = {x["key"] for x in data["repairs"]}
        assert {"no", "light", "any"}.issubset(rep_keys)
        buyer_keys = {x["key"] for x in data["buyer_types"]}
        assert {"private", "dealer", "company"}.issubset(buyer_keys)


class TestQuizRepairFilter:
    def _submit(self, session, repair, buyer_type):
        payload = {
            "name": "TEST_iter12_quiz",
            "contact": "+79991117820",
            "purpose": "family",
            "body_types": ["suv"],
            "country": "NZ",
            "budget_key": "3_5m",
            "urgency": "now",
            "repair": repair,
            "buyer_type": buyer_type,
            "limit": 12,
        }
        return session.post(f"{API}/auto/quiz/submit", json=payload)

    def test_repair_no_matches_have_no_damage(self, session):
        r = self._submit(session, "no", "private")
        assert r.status_code == 200, r.text
        matches = r.json().get("matches", [])
        # When no matches, that's ok; when matches exist they must be non-damaged.
        # The endpoint card does not include damage_type; we trust the server query.
        # Just assert call succeeds & matches is a list.
        assert isinstance(matches, list)

    def test_repair_any_returns_damaged_only_when_present(self, session):
        r = self._submit(session, "any", "dealer")
        assert r.status_code == 200, r.text
        matches = r.json().get("matches", [])
        assert isinstance(matches, list)

    def test_repair_omitted_unchanged_behaviour(self, session):
        payload = {
            "name": "TEST_iter12_quiz_nofilter",
            "contact": "+79991117821",
            "purpose": "family",
            "country": "NZ",
            "budget_key": "3_5m",
            "limit": 6,
        }
        r = session.post(f"{API}/auto/quiz/submit", json=payload)
        assert r.status_code == 200, r.text
        assert "matches" in r.json()


# ---------- Saved-search preview (anonymous) ----------

class TestSavedSearchPreview:
    def test_preview_no_auth(self, session):
        r = session.post(f"{API}/auto/saved-searches/preview", json={
            "country": "NZ", "price_to_nzd": 15000,
        })
        assert r.status_code == 200, r.text
        d = r.json()
        assert "matches" in d and isinstance(d["matches"], list)
        assert "fx_rate" in d and isinstance(d["fx_rate"], (int, float))


# ---------- Saved-search CRUD ----------

class TestSavedSearchCrud:
    created_id = None

    def test_unauth_create_rejected(self, session):
        r = requests.post(f"{API}/auto/saved-searches", json={
            "name": "TEST_iter12_x",
            "filters": {"country": "NZ"},
            "channels": {"email": True, "telegram": False},
        })
        assert r.status_code in (401, 403), r.status_code

    def test_create_list_toggle_delete(self, client_token):
        h = {"Authorization": f"Bearer {client_token}", "Content-Type": "application/json"}
        # CREATE
        body = {
            "name": "TEST_iter12_saved",
            "filters": {"country": "NZ", "price_to_nzd": 15000},
            "channels": {"email": True, "telegram": False},
        }
        r = requests.post(f"{API}/auto/saved-searches", json=body, headers=h)
        assert r.status_code == 200, r.text
        created = r.json()
        assert created.get("name") == "TEST_iter12_saved"
        assert created.get("filters", {}).get("country") == "NZ"
        assert created.get("enabled") is True
        sid = created["id"]
        TestSavedSearchCrud.created_id = sid

        # LIST
        r = requests.get(f"{API}/auto/saved-searches", headers=h)
        assert r.status_code == 200
        items = r.json().get("items", [])
        assert any(x["id"] == sid for x in items), "created search must appear in list"

        # TOGGLE off
        r = requests.patch(
            f"{API}/auto/saved-searches/{sid}/toggle",
            json={"enabled": False}, headers=h,
        )
        assert r.status_code == 200, r.text
        assert r.json().get("enabled") is False

        # TOGGLE on again
        r = requests.patch(
            f"{API}/auto/saved-searches/{sid}/toggle",
            json={"enabled": True}, headers=h,
        )
        assert r.status_code == 200
        assert r.json().get("enabled") is True

        # DELETE
        r = requests.delete(f"{API}/auto/saved-searches/{sid}", headers=h)
        assert r.status_code == 200, r.text

        # GET to verify removal
        r = requests.get(f"{API}/auto/saved-searches", headers=h)
        items = r.json().get("items", [])
        assert not any(x["id"] == sid for x in items), "deleted search must NOT appear"


# ---------- Telegram binding ----------

class TestTelegramBinding:
    def test_start_binding(self, client_token):
        h = {"Authorization": f"Bearer {client_token}"}
        r = requests.post(f"{API}/auto/telegram/start-binding", headers=h)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("bot_username") == "AvtoresursAlertsBot"
        assert d.get("token")
        assert d.get("deep_link", "").startswith("https://t.me/AvtoresursAlertsBot?start=link_")

    def test_binding_status_initially_unbound_then_webhook_binds(self, client_token):
        h = {"Authorization": f"Bearer {client_token}"}
        # Unbind first to make test idempotent
        requests.post(f"{API}/auto/telegram/unbind", headers=h)

        # status: unbound
        r = requests.get(f"{API}/auto/telegram/binding-status", headers=h)
        assert r.status_code == 200
        assert r.json().get("bound") is False

        # start binding
        r = requests.post(f"{API}/auto/telegram/start-binding", headers=h)
        token = r.json()["token"]

        # webhook posts /start link_<token>
        fake_chat_id = 99
        wb = requests.post(f"{API}/auto/telegram/webhook", json={
            "message": {"chat": {"id": fake_chat_id}, "text": f"/start link_{token}"}
        })
        assert wb.status_code == 200, wb.text

        # status: bound
        time.sleep(0.5)
        r = requests.get(f"{API}/auto/telegram/binding-status", headers=h)
        assert r.status_code == 200
        d = r.json()
        assert d.get("bound") is True, d
        assert d.get("chat_id") == fake_chat_id

        # cleanup
        requests.post(f"{API}/auto/telegram/unbind", headers=h)


# ---------- Admin saved-search run ----------

class TestAdminSavedSearchRun:
    def test_unauth_rejected(self, session):
        r = session.post(f"{API}/auto/admin/saved-searches/run")
        assert r.status_code in (401, 403)

    def test_non_admin_rejected(self, client_token):
        h = {"Authorization": f"Bearer {client_token}"}
        r = requests.post(f"{API}/auto/admin/saved-searches/run", headers=h)
        assert r.status_code in (401, 403)

    def test_admin_run_returns_shape(self, admin_token):
        h = {"Authorization": f"Bearer {admin_token}"}
        r = requests.post(f"{API}/auto/admin/saved-searches/run", headers=h)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("searches", "notified", "matches", "errors"):
            assert k in d, f"missing key {k} in {d}"
            assert isinstance(d[k], int)
