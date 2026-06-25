"""Iter13 — Manheim calendar + Otahuhu image regression backend tests."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://auto-nz-bidding.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@buyanywhere.com"
ADMIN_PASSWORD = "admin12345"

RU_CITIES_ALLOWED = {"Окленд", "Веллингтон", "Крайстчёрч", "Гамильтон", "Такини", "Дунедин", "Дюнидин", "Данидин"}


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


# --- Admin refresh: turners + manheim both > 0 ---------------------------------
def test_admin_refresh_returns_both_sources(admin_token):
    r = requests.post(
        f"{BASE_URL}/api/auto/admin/auctions/refresh",
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=120,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "fetched" in data and isinstance(data["fetched"], int)
    assert "by_category" in data and {"cars", "damaged", "trucks"} <= set(data["by_category"].keys())
    assert "by_source" in data and {"turners", "manheim"} <= set(data["by_source"].keys())
    assert "at" in data
    assert data["by_source"]["turners"] > 0, f"turners count was {data['by_source']['turners']}"
    assert data["by_source"]["manheim"] > 0, f"manheim count was {data['by_source']['manheim']}"


# --- Calendar exposes Manheim events with Russian-localised cities --------------
def test_calendar_contains_manheim_with_russian_city():
    r = requests.get(f"{BASE_URL}/api/auto/auctions/calendar?days_ahead=21", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert {"events", "by_day", "count"} <= set(data.keys())
    events = data["events"]
    assert isinstance(events, list) and len(events) > 0
    manheim = [e for e in events if e.get("source") == "manheim"]
    assert len(manheim) > 0, "no events have source=manheim"
    # Each manheim event should have a Russian-localised city
    bad = []
    for e in manheim:
        city = (e.get("city") or "").strip()
        if not any(allowed in city for allowed in RU_CITIES_ALLOWED):
            bad.append(city)
    assert not bad, f"manheim events with un-localised cities: {bad}"
