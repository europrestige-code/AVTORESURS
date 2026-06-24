"""Iteration 6 — verify FX, hot-daily (max 2), landed-defaults, ru-customs/calc."""
import os
import requests
import pytest

def _load_url():
    v = os.environ.get("REACT_APP_BACKEND_URL")
    if v:
        return v.rstrip("/")
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip().rstrip("/")
    except Exception:
        pass
    raise RuntimeError("REACT_APP_BACKEND_URL not found")

BASE = _load_url()
API = f"{BASE}/api/auto"


def test_fx_rate_shape():
    r = requests.get(f"{API}/fx-rate", timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    for k in ("nzd_to_rub_spot", "nzd_to_rub_display", "markup_pct", "source"):
        assert k in d, f"missing {k} in {d}"
    assert d["markup_pct"] == 0.03
    # display ≈ spot × 1.03
    assert abs(d["nzd_to_rub_display"] - d["nzd_to_rub_spot"] * 1.03) < 0.01


def test_hot_daily_max_2_and_labels():
    r = requests.get(f"{API}/hot-daily", timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    items = d.get("items", [])
    assert len(items) <= 2
    from datetime import datetime
    min_year = datetime.utcnow().year - 5
    labels_seen = set()
    for it in items:
        assert it.get("listing_type") == "auction", f"non-auction in hot picks: {it.get('id')}"
        assert it.get("status") == "available"
        assert (it.get("year") or 0) >= min_year, f"year {it.get('year')} < {min_year}"
        assert "pick_label" in it
        assert it["pick_label"] in ("Самый свежий", "Самый выгодный")
        labels_seen.add(it["pick_label"])
    if len(items) == 2:
        assert labels_seen == {"Самый свежий", "Самый выгодный"}


def test_ru_customs_calc_with_extras():
    r = requests.get(f"{API}/ru-customs/calc", params={
        "fob_nzd": 5000, "age_years": 4, "engine_cc": 1800, "engine_hp": 140,
        "importer_type": "personal", "scheme": "whole",
        "nz_branch": "Wellington", "is_non_runner": True, "inspection": True,
        "forklift": True, "dismantling": False, "docs_fee": True, "storage_days": 3,
    }, timeout=20)
    assert r.status_code == 200, r.text
    d = r.json()
    for k in ("fob_nzd", "nz_buyers_premium_nzd", "avtoresurs_commission_nzd",
              "nz_local_transport_nzd", "inspection_fee_nzd", "forklift_fee_nzd",
              "nz_extras_total_nzd", "freight_usd", "insurance_usd",
              "cif_rub", "duty_rub", "utilsbor_rub", "customs_total_rub",
              "landed_total_rub", "landed_total_nzd", "landed_total_usd"):
        assert k in d, f"missing {k}"
    assert d["landed_total_rub"] > 0
    # non-runner should double NZ local transport
    assert d.get("nz_local_transport_non_runner") is True


def _find_vehicle(condition=None, damage_type=None):
    r = requests.get(f"{API}/vehicles", params={"limit": 100}, timeout=15)
    if r.status_code != 200:
        return None
    items = r.json() or []
    if isinstance(items, dict):
        items = items.get("items") or items.get("vehicles") or []
    for v in items:
        ok = True
        if condition and v.get("condition") != condition:
            ok = False
        if damage_type:
            dt = v.get("damage_type") or ""
            if not dt or dt == "Без повреждений":
                ok = False
        if ok:
            return v
    return None


def test_landed_defaults_clean_auction():
    r = requests.get(f"{API}/vehicles", params={"limit": 50, "listing_type": "auction"}, timeout=15)
    assert r.status_code == 200
    items = r.json() or []
    if isinstance(items, dict):
        items = items.get("items") or items.get("vehicles") or []
    # find a clean (no damage_type) auction
    clean = None
    for v in items:
        if not (v.get("damage_type") and v.get("damage_type") != "Без повреждений"):
            if v.get("condition") not in ("Повреждённое", "На запчасти"):
                clean = v
                break
    if not clean:
        pytest.skip("no clean auction in seed")
    r = requests.get(f"{API}/vehicles/{clean['id']}/landed-defaults", timeout=10)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("scheme") in (None, "whole")
    assert d.get("is_non_runner") in (False, None)
    assert d.get("forklift") in (False, None)
    assert d.get("dismantling") in (False, None)


def test_landed_defaults_damaged():
    v = _find_vehicle(damage_type="any") or _find_vehicle(condition="Повреждённое")
    if not v:
        pytest.skip("no damaged vehicle in seed")
    r = requests.get(f"{API}/vehicles/{v['id']}/landed-defaults", timeout=10)
    assert r.status_code == 200, r.text
    d = r.json()
    # Expected per iter5 bug fix request
    assert d.get("is_non_runner") is True, f"damaged should preselect non_runner: {d}"
    assert d.get("inspection") is True, f"damaged should preselect inspection: {d}"
    assert d.get("forklift") is True, f"damaged should preselect forklift: {d}"


def test_chat_russian_response():
    r = requests.post(f"{API}/chat", json={
        "message": "Сколько стоит привезти Toyota Aqua из Новой Зеландии под ключ?",
        "history": [],
    }, timeout=60)
    assert r.status_code == 200, r.text
    d = r.json()
    txt = (d.get("content") or "").lower()
    assert len(txt) > 20
    # at least one of the expected concepts should appear
    has_concept = any(k in txt for k in ("калькул", "под ключ", "fob", "владивосток", "растамож"))
    assert has_concept, f"chat reply lacks expected concepts: {txt[:300]}"
