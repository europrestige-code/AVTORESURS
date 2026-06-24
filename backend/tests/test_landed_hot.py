"""Tests for new endpoints: /hot-daily, /ru-customs/calc, /vehicles/{id}/landed-defaults."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://auto-nz-bidding.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api/auto"


def test_hot_daily_returns_items():
    r = requests.get(f"{API}/hot-daily?limit=6", timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data and "count" in data
    for it in data["items"]:
        assert it.get("listing_type") == "auction"
        assert it.get("status") == "available"


def test_ru_customs_calc_full():
    params = {
        "fob_nzd": 15000, "age_years": 7, "engine_cc": 1800, "engine_hp": 140,
        "importer_type": "personal", "scheme": "whole",
        "nz_branch": "Wellington", "is_non_runner": "true",
        "inspection": "true", "forklift": "false", "dismantling": "false",
        "storage_days": 3,
    }
    r = requests.get(f"{API}/ru-customs/calc", params=params, timeout=20)
    assert r.status_code == 200, r.text
    d = r.json()
    for k in ["fob_nzd", "nz_extras_total_nzd", "freight_usd", "cif_rub",
              "duty_rub", "utilsbor_rub", "customs_total_rub", "landed_total_rub"]:
        assert k in d, f"missing {k} in response"
    assert d["fob_nzd"] == 15000
    assert d["nz_local_transport_nzd"] > 0
    # non_runner=true should mark transport doubled
    assert d.get("nz_local_transport_non_runner") in (True, "true", 1)


def test_ru_customs_invalid_scheme():
    r = requests.get(f"{API}/ru-customs/calc", params={"fob_nzd": 10000, "scheme": "bad"}, timeout=10)
    assert r.status_code == 400


def test_ru_customs_invalid_fob():
    r = requests.get(f"{API}/ru-customs/calc", params={"fob_nzd": 0}, timeout=10)
    assert r.status_code == 400


def test_landed_defaults_for_any_vehicle():
    # Find any vehicle id
    r = requests.get(f"{API}/vehicles?limit=5", timeout=20)
    assert r.status_code == 200
    body = r.json()
    items = body.get("items") if isinstance(body, dict) else body
    assert items and len(items) > 0, "no vehicles seeded"
    vid = items[0]["id"]
    r2 = requests.get(f"{API}/vehicles/{vid}/landed-defaults", timeout=15)
    assert r2.status_code == 200, r2.text
    d = r2.json()
    assert d["vehicle_id"] == vid
    for k in ["fob_nzd", "age_years", "engine_cc", "scheme",
              "is_non_runner", "inspection", "forklift", "dismantling"]:
        assert k in d


def test_landed_defaults_404():
    r = requests.get(f"{API}/vehicles/__nope__/landed-defaults", timeout=10)
    assert r.status_code == 404


def test_chat_responds_in_russian():
    r = requests.post(f"{BASE_URL}/api/auto/chat",
                      json={"message": "Сколько стоит Toyota Camry под ключ в Россию?"},
                      timeout=60)
    assert r.status_code == 200, r.text
    body = r.json()
    txt = body.get("content") or body.get("reply") or ""
    assert len(txt) > 20
    # Should be Russian (Cyrillic)
    assert any("\u0400" <= ch <= "\u04FF" for ch in txt)
