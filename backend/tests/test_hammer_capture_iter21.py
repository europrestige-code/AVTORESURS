"""Iter21 hammer-price capture pipeline tests.

Covers:
- services.auto_hammer_capture.snapshot_current_listings (dedup + insertion)
- services.auto_hammer_capture.sweep_stale_as_sold (window guard + dedup + status flip)
- POST /api/auto/admin/sources/capture-hammer (admin auth)
- GET /api/auto/vehicles/{id}/sold-history regression (current_listings fallback)
- Scheduler wiring (HAMMER_* constants + status() key)
- is_non_vehicle whitelist regression (Hiace/Transit/etc)
"""
from __future__ import annotations

import os
import sys
import asyncio
from datetime import datetime, timedelta

import pytest
import requests
from dotenv import load_dotenv

BACKEND_DIR = "/app/backend"
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

load_dotenv(f"{BACKEND_DIR}/.env")
load_dotenv("/app/frontend/.env")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from services import auto_hammer_capture as hammer  # noqa: E402
from services import auto_scheduler  # noqa: E402
from services.auto_source_importers import is_non_vehicle  # noqa: E402


BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or "").rstrip("/")
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

ADMIN_EMAIL = "admin@buyanywhere.com"
ADMIN_PASSWORD = "admin12345"


def _run(async_fn):
    """Execute an async function with a fresh Motor client injected as `db`."""
    async def wrapped():
        client = AsyncIOMotorClient(MONGO_URL)
        try:
            return await async_fn(client[DB_NAME])
        finally:
            client.close()
    return asyncio.run(wrapped())


@pytest.fixture(scope="module")
def admin_token():
    try:
        r = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15,
        )
    except Exception as e:
        pytest.skip(f"Auth endpoint unreachable: {e}")
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code} {r.text[:200]}")
    tok = r.json().get("access_token")
    if not tok:
        pytest.skip("No access_token in login response")
    return tok


# ---------- 1. snapshot_current_listings ----------

def test_snapshot_current_listings_manheim():
    async def _t(db):
        before = await db.auction_observations.count_documents(
            {"source": "manheim", "source_type": "official_listing"}
        )
        r1 = await hammer.snapshot_current_listings(db, "manheim")
        assert r1["source"] == "manheim"
        assert r1["inspected"] >= 0
        after1 = await db.auction_observations.count_documents(
            {"source": "manheim", "source_type": "official_listing"}
        )
        assert after1 - before == r1["captured"], (before, after1, r1)

        if r1["captured"] > 0:
            obs = await db.auction_observations.find_one(
                {"source": "manheim", "source_type": "official_listing", "sold": False},
                sort=[("observed_at", -1)],
            )
            assert obs is not None
            assert obs["sold"] is False
            assert obs.get("lot_ref")
            if obs.get("vehicle_id"):
                v = await db.auto_vehicles.find_one({"id": obs["vehicle_id"]}, {"_id": 0})
                if v and v.get("current_price_nzd"):
                    assert float(obs["observed_price_nzd"]) == float(v["current_price_nzd"])

        # Second call within 24h: dedup should produce 0 captured
        r2 = await hammer.snapshot_current_listings(db, "manheim")
        assert r2["captured"] == 0, f"Expected dedup=0, got {r2}"
        print(f"snapshot: first_call={r1}, second_call={r2}")

    _run(_t)


# ---------- 2. sweep_stale_as_sold happy path ----------

TEST_LOT_1 = "TEST_LOT_ITER21_STALE"
TEST_VID_1 = "test-vehicle-iter21-stale"


def test_sweep_stale_as_sold_captures_stale():
    async def _t(db):
        now = datetime.utcnow()
        seed = {
            "id": TEST_VID_1,
            "source": "manheim",
            "source_reference": TEST_LOT_1,
            "status": "available",
            "current_price_nzd": 8500,
            "make": "Toyota",
            "model": "TestModel",
            "year": 2015,
            "last_sync_time": now - timedelta(hours=72),
            "first_seen": now - timedelta(days=3),
            "title_original": "Test Toyota TestModel",
        }
        await db.auto_vehicles.delete_many({"id": TEST_VID_1})
        await db.auction_observations.delete_many({"lot_ref": TEST_LOT_1})
        await db.auto_vehicles.insert_one(seed)
        try:
            r = await hammer.sweep_stale_as_sold(db, "manheim", stale_hours=48, active_window_days=5)
            print(f"sweep stale result: {r}")
            assert r["inspected"] >= 1, r
            assert r["captured"] >= 1, r
            assert r["marked_sold"] >= 1, r

            obs = await db.auction_observations.find_one({"lot_ref": TEST_LOT_1})
            assert obs is not None
            assert obs["sold"] is True
            assert obs["source_type"] == "public_archive"
            assert obs["source"] == "manheim"
            assert float(obs["observed_price_nzd"]) == 8500.0

            v_after = await db.auto_vehicles.find_one({"id": TEST_VID_1}, {"_id": 0})
            assert v_after["status"] == "sold"

            # Second call: dedup — captured 0
            await db.auto_vehicles.update_one(
                {"id": TEST_VID_1}, {"$set": {"status": "available"}}
            )
            r2 = await hammer.sweep_stale_as_sold(
                db, "manheim", stale_hours=48, active_window_days=5
            )
            assert r2["captured"] == 0, f"Dedup failed: {r2}"
        finally:
            await db.auto_vehicles.delete_many({"id": TEST_VID_1})
            await db.auction_observations.delete_many({"lot_ref": TEST_LOT_1})

    _run(_t)


# ---------- 3. Time-window guard ----------

TEST_LOT_2 = "TEST_LOT_ITER21_OUT_OF_WINDOW"
TEST_VID_2 = "test-vehicle-iter21-oow"


def test_sweep_skips_out_of_window():
    async def _t(db):
        now = datetime.utcnow()
        seed = {
            "id": TEST_VID_2,
            "source": "manheim",
            "source_reference": TEST_LOT_2,
            "status": "available",
            "current_price_nzd": 7000,
            "last_sync_time": now - timedelta(days=10),  # outside 5d window
            "first_seen": now - timedelta(days=15),
            "make": "Toyota",
            "model": "TestOOW",
            "year": 2014,
            "title_original": "Test OOW",
        }
        await db.auto_vehicles.delete_many({"id": TEST_VID_2})
        await db.auction_observations.delete_many({"lot_ref": TEST_LOT_2})
        await db.auto_vehicles.insert_one(seed)
        try:
            r = await hammer.sweep_stale_as_sold(
                db, "manheim", stale_hours=48, active_window_days=5
            )
            v_after = await db.auto_vehicles.find_one({"id": TEST_VID_2}, {"_id": 0})
            assert v_after["status"] == "available", f"OOW row was touched: {v_after}"
            obs = await db.auction_observations.find_one({"lot_ref": TEST_LOT_2})
            assert obs is None
            assert set(r.keys()) >= {"inspected", "captured", "marked_sold"}
            print(f"OOW guard result: {r}")
        finally:
            await db.auto_vehicles.delete_many({"id": TEST_VID_2})
            await db.auction_observations.delete_many({"lot_ref": TEST_LOT_2})

    _run(_t)


# ---------- 4. POST /admin/sources/capture-hammer ----------

def test_admin_capture_hammer_endpoint(admin_token):
    r = requests.post(
        f"{BASE_URL}/api/auto/admin/sources/capture-hammer",
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=90,
    )
    if r.status_code in (401, 403):
        pytest.skip(f"Admin blocked (2FA?): {r.status_code} {r.text[:200]}")
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    assert "snapshot" in body and "sweep" in body
    assert isinstance(body["snapshot"], list) and isinstance(body["sweep"], list)
    sources_snap = {e["source"] for e in body["snapshot"]}
    sources_sweep = {e["source"] for e in body["sweep"]}
    assert {"turners", "manheim"} <= sources_snap, sources_snap
    assert {"turners", "manheim"} <= sources_sweep, sources_sweep
    for e in body["snapshot"] + body["sweep"]:
        assert "source" in e and "inspected" in e and "captured" in e


# ---------- 5. sold-history regression ----------

def test_sold_history_falls_back_to_current_listings():
    async def _pick(db):
        return await db.auto_vehicles.find_one(
            {"make": {"$regex": "^Toyota$", "$options": "i"},
             "current_price_nzd": {"$gt": 0}},
            {"_id": 0, "id": 1, "make": 1, "model": 1, "year": 1},
        )
    v = _run(_pick)
    if not v:
        pytest.skip("No Toyota vehicle to test sold-history fallback")
    r = requests.get(
        f"{BASE_URL}/api/auto/vehicles/{v['id']}/sold-history", timeout=30
    )
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    print("sold-history payload:", data)
    assert isinstance(data, dict)
    stats = data.get("stats") if isinstance(data.get("stats"), dict) else data
    count = stats.get("count") if stats else None
    if count is None:
        count = data.get("count")
    # If backend uses different structure (list under 'items'), scan
    if count is None and isinstance(data.get("items"), list):
        count = len(data["items"])
    assert count is not None, f"No 'count' in response: {data}"
    if count and count > 0:
        candidates = {}
        for k in ("min_nzd", "max_nzd", "median_nzd", "min", "max", "median"):
            candidates[k] = stats.get(k) if stats else None
            if candidates[k] is None:
                candidates[k] = data.get(k)
        # At least one of min/max/median must be populated in either naming
        has_min = candidates.get("min_nzd") is not None or candidates.get("min") is not None
        has_max = candidates.get("max_nzd") is not None or candidates.get("max") is not None
        has_med = candidates.get("median_nzd") is not None or candidates.get("median") is not None
        assert has_min and has_max and has_med, f"Missing stats in {data}"


# ---------- 6. Scheduler wiring ----------

def test_scheduler_hammer_constants_and_status_key():
    assert auto_scheduler.HAMMER_INTERVAL_SECONDS == 6 * 60 * 60 == 21600
    assert auto_scheduler.HAMMER_STALE_HOURS == 48
    s = auto_scheduler.status()
    assert "hammer_capture" in s, s.keys()
    hc = s["hammer_capture"]
    for key in ("running", "interval_seconds", "stale_hours", "last_run_at", "last_result"):
        assert key in hc, f"missing '{key}' in hammer_capture status: {hc}"
    assert hc["interval_seconds"] == 21600
    assert hc["stale_hours"] == 48


# ---------- 7. is_non_vehicle regression ----------

@pytest.mark.parametrize("payload,expected", [
    ({"title": "Toyota Hiace 2015", "source_url": "https://www.turners.co.nz/trucks-machinery/xyz"}, False),
    ({"title": "Ford Transit Custom 2018", "source_url": "https://www.turners.co.nz/trucks-machinery/abc"}, False),
    ({"title": "Mercedes Sprinter Van", "source_url": "https://www.turners.co.nz/trucks-machinery/qwe"}, False),
    ({"title": "Toyota Hilux 4WD", "source_url": "https://www.turners.co.nz/trucks-machinery/hilux"}, False),
    ({"title": "Portable Building 6m", "source_url": "https://www.turners.co.nz/trucks-machinery/pb"}, True),
    ({"title": "Concrete Mixer", "source_url": "https://www.turners.co.nz/trucks-machinery/mx"}, True),
])
def test_is_non_vehicle_whitelist_regression(payload, expected):
    assert is_non_vehicle(payload) is expected, payload
