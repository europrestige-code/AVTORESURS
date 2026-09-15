"""Iteration 22: Scraper autoloop + van/pickup preset chip tests."""
import os
import re
import pytest
import requests

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL")
            or "https://auto-nz-bidding.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@buyanywhere.com"
ADMIN_PW = "admin12345"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PW}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code} {r.text}")
    return r.json().get("access_token") or r.json().get("token")


# ---- Preset counts ----
class TestPresetCounts:
    def test_preset_counts_shape_and_van_pickup(self):
        r = requests.get(f"{BASE_URL}/api/auto/preset-counts", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "items" in data
        items = data["items"]
        assert isinstance(items, list) and len(items) >= 1
        vp = next((i for i in items if i["key"] == "van_pickup"), None)
        assert vp is not None, "van_pickup preset missing"
        # Fields
        for k in ("key", "label_ru", "regex", "count"):
            assert k in vp
        # Count expectation
        assert vp["count"] > 100, f"van_pickup count too low: {vp['count']}"
        # Regex tokens
        rx = vp["regex"].lower()
        for tok in ["hiace", "transit", "sprinter", "hilux", "ranger", "navara", "amarok"]:
            assert tok in rx, f"token {tok} missing from regex"

    def test_van_pickup_vehicles_search_matches(self):
        # Fetch regex from preset endpoint
        pr = requests.get(f"{BASE_URL}/api/auto/preset-counts", timeout=30).json()
        vp = next(i for i in pr["items"] if i["key"] == "van_pickup")
        regex = vp["regex"]
        expected_count = vp["count"]
        r = requests.get(f"{BASE_URL}/api/auto/vehicles",
                         params={"search": regex, "limit": 12}, timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        # Response can be {items,total} or list — normalize
        if isinstance(data, dict):
            items = data.get("items") or data.get("vehicles") or []
            total = data.get("total")
        else:
            items = data
            total = None
        assert len(items) > 0, "no vehicles returned for van_pickup regex"
        # Total should be near preset count (within scrape drift)
        if total is not None:
            drift = abs(total - expected_count)
            assert drift <= max(20, int(expected_count * 0.1)), \
                f"total {total} drifted too far from preset count {expected_count}"
        # Every returned item's title should contain a van/pickup keyword
        pat = re.compile(regex, re.IGNORECASE)
        for v in items:
            title = " ".join([str(v.get("title_ru") or ""),
                              str(v.get("title_original") or ""),
                              str(v.get("model") or "")])
            assert pat.search(title), f"item title doesn't match preset regex: {title!r}"


# ---- Scheduler wiring ----
class TestSchedulerWiring:
    def test_scheduler_module_constants(self):
        from services import auto_scheduler
        assert auto_scheduler.SCRAPER_INTERVAL_SECONDS == 3600
        assert auto_scheduler.SCRAPER_LIMIT_PER_SOURCE == 50

    def test_scheduler_status_dict(self):
        from services import auto_scheduler
        s = auto_scheduler.status()
        assert "scraper_autoloop" in s
        sa = s["scraper_autoloop"]
        for k in ("running", "interval_seconds", "limit_per_source",
                  "last_run_at", "last_result"):
            assert k in sa, f"missing field {k}"
        assert sa["interval_seconds"] == 3600
        assert sa["limit_per_source"] == 50


# ---- Regression: body-type-counts ----
class TestBodyTypeCountsRegression:
    def test_body_type_counts_canonical(self):
        r = requests.get(f"{BASE_URL}/api/auto/body-type-counts", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        keys = {i.get("key") or i.get("value") or i.get("body_type") for i in data["items"]}
        # canonical bodies expected
        # Accept any of these key shapes; just make sure we have common bodies
        joined = " ".join(str(k or "").lower() for k in keys)
        for canon in ["sedan", "suv", "van"]:
            assert canon in joined, f"canonical {canon} missing in {keys}"


# ---- Regression: capture-hammer admin endpoint ----
class TestHammerCaptureRegression:
    def test_capture_hammer_admin(self, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        r = requests.post(f"{BASE_URL}/api/auto/admin/sources/capture-hammer",
                          headers=headers, timeout=120)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "snapshot" in body and "sweep" in body


# ---- Regression: sold-history ----
class TestSoldHistoryRegression:
    def test_sold_history_shape(self):
        # Pick any vehicle
        r = requests.get(f"{BASE_URL}/api/auto/vehicles", params={"limit": 1}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        items = data.get("items") if isinstance(data, dict) else data
        if not items:
            pytest.skip("no vehicles in catalog")
        vid = items[0]["id"]
        r2 = requests.get(f"{BASE_URL}/api/auto/vehicles/{vid}/sold-history", timeout=30)
        assert r2.status_code == 200, r2.text
        body = r2.json()
        assert body.get("source") in ("current_listings", "sold_observations", "insufficient")


# ---- Regression: is_non_vehicle whitelist ----
class TestIsNonVehicleWhitelist:
    def test_whitelist(self):
        from services.auto_source_importers import is_non_vehicle
        # Vans/pickups should not be filtered
        for title in ["Toyota Hiace 2015", "Ford Transit 2016 van",
                      "Mercedes-Benz Sprinter 2017", "Toyota Hilux 2018"]:
            assert is_non_vehicle({"title": title}) is False, f"{title} incorrectly filtered"
        # Non-vehicles
        for title in ["Portable Building 3x6m", "Cement Mixer trailer"]:
            assert is_non_vehicle({"title": title}) is True, f"{title} should be filtered"
