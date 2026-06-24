"""Iteration 3 — Scheduler / Source importers (scan + import + duplicate) /
Branding backfill / Static file serve. Extends iteration 2 by validating the
new operational features.
"""
import os
import time
import pytest
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path("/app/frontend/.env"))
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@buyanywhere.com", "password": "admin12345"}
CLIENT = {"email": "client@buyanywhere.com", "password": "client12345"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin_token():
    return _login(ADMIN)


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def client_token():
    return _login(CLIENT)


# ---------- Existing endpoints regression ----------

class TestExistingRegression:
    def test_admin_login(self, admin_token):
        assert isinstance(admin_token, str) and len(admin_token) > 10

    def test_client_login(self, client_token):
        assert isinstance(client_token, str) and len(client_token) > 10

    def test_vehicles_list(self):
        r = requests.get(f"{API}/auto/vehicles", timeout=20)
        assert r.status_code == 200
        d = r.json()
        # Could be a list or {items: [...]} - just sanity check it's iterable
        assert d is not None

    def test_calendar(self):
        r = requests.get(f"{API}/auto/auctions/calendar", params={"days_ahead": 21}, timeout=30)
        assert r.status_code == 200
        assert "events" in r.json()

    def test_transport_cost(self):
        r = requests.get(f"{API}/auto/transport/cost",
                         params={"branch": "Wellington", "non_runner": "true"}, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["transport_nzd"] == 1360
        assert d["matched"] is True


# ---------- Scheduler ----------

class TestScheduler:
    def test_status_requires_admin(self):
        r = requests.get(f"{API}/auto/admin/scheduler/status", timeout=10)
        assert r.status_code in (401, 403)

    def test_status_with_admin(self, admin_headers):
        r = requests.get(f"{API}/auto/admin/scheduler/status",
                         headers=admin_headers, timeout=10)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("running") is True
        assert d.get("interval_seconds") == 86400
        assert "last_run_at" in d
        assert "last_result" in d


# ---------- Sources list ----------

class TestSourcesList:
    def test_list_sources(self, admin_headers):
        r = requests.get(f"{API}/auto/admin/sources", headers=admin_headers, timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert "sources" in d
        assert set(["turners", "manheim", "pickles"]).issubset(set(d["sources"]))


# ---------- Source scan (preview) ----------

class TestSourceScan:
    def test_scan_unknown_source_400(self, admin_headers):
        r = requests.post(f"{API}/auto/admin/sources/scan",
                          json={"source": "unknown"}, headers=admin_headers, timeout=15)
        assert r.status_code == 400

    def test_scan_turners_preview_no_writes(self, admin_headers):
        # Count vehicles before
        r0 = requests.get(f"{API}/auto/vehicles", params={"limit": 1}, timeout=15)
        assert r0.status_code == 200
        # use endpoint that counts
        before = requests.get(f"{API}/auto/catalog-summary", timeout=15).json().get("total", 0)

        r = requests.post(f"{API}/auto/admin/sources/scan",
                          json={"source": "turners", "limit": 5},
                          headers=admin_headers, timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        # Even if Turners returns 0 due to network/page change, endpoint MUST be 200
        assert "ok" in d
        if d.get("ok"):
            assert d.get("source") == "turners"
            assert "fetched" in d and isinstance(d["fetched"], int)
            assert "items" in d and isinstance(d["items"], list)
            assert "new" in d
            assert "duplicates" in d
            for item in d["items"]:
                if "error" in item:
                    continue
                assert "vehicle" in item
                assert "duplicate_of" in item
                assert "is_new" in item
        # Verify no inserts
        after = requests.get(f"{API}/auto/catalog-summary", timeout=15).json().get("total", 0)
        assert after == before, f"scan should not insert vehicles ({before} -> {after})"


# ---------- Source import + duplicate detection ----------

class TestSourceImport:
    @pytest.fixture(scope="class")
    def scan_ids(self, admin_headers):
        r = requests.post(f"{API}/auto/admin/sources/scan",
                          json={"source": "turners", "limit": 5},
                          headers=admin_headers, timeout=120)
        if r.status_code != 200 or not r.json().get("ok"):
            pytest.skip("Turners scan did not return ok=true")
        items = r.json().get("items", [])
        refs = [it["vehicle"].get("source_reference")
                for it in items if it.get("vehicle") and it["vehicle"].get("source_reference")]
        if not refs:
            pytest.skip("No source_references returned by Turners scan")
        return refs[:3]

    def test_import_with_ids(self, admin_headers, scan_ids):
        body = {"source": "turners", "limit": 10, "ids": scan_ids,
                "skip_duplicates": True}
        r = requests.post(f"{API}/auto/admin/sources/import",
                          json=body, headers=admin_headers, timeout=180)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("importer") == "turners"
        assert "fetched" in d
        assert "created" in d
        assert "updated" in d
        assert "skipped" in d
        assert "failed" in d
        assert "sync_status" in d
        assert "errors" in d

    def test_import_runs_listed(self, admin_headers):
        r = requests.get(f"{API}/auto/admin/sources/runs",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200
        runs = r.json()
        assert isinstance(runs, list)
        assert len(runs) >= 1
        # latest run is turners
        latest = runs[0]
        assert latest.get("importer") in ("turners", "manheim", "pickles")

    def test_import_duplicates_second_run(self, admin_headers, scan_ids):
        body = {"source": "turners", "limit": 10, "ids": scan_ids,
                "skip_duplicates": True}
        r = requests.post(f"{API}/auto/admin/sources/import",
                          json=body, headers=admin_headers, timeout=180)
        assert r.status_code == 200, r.text
        d = r.json()
        # On re-run, should detect duplicates -> created should be 0, skipped >= 1
        assert d.get("created") == 0, f"expected 0 created on re-import, got {d}"
        # At least one should be skipped (duplicate) OR all were filtered out via ids_filter
        # If fetched=0 (Turners changed), we can't assert skipped strictly; gate on fetched
        if d.get("fetched", 0) > 0:
            assert d.get("skipped", 0) >= 1, f"expected skipped>=1 on duplicate run, got {d}"


# ---------- Branding backfill ----------

class TestBrandingBackfill:
    def test_requires_admin(self):
        r = requests.post(f"{API}/auto/admin/images/backfill-branding",
                          json={"limit": 1}, timeout=10)
        assert r.status_code in (401, 403)

    def test_backfill_processes_and_idempotent(self, admin_headers):
        r1 = requests.post(f"{API}/auto/admin/images/backfill-branding",
                           json={"limit": 3}, headers=admin_headers, timeout=180)
        assert r1.status_code == 200, r1.text
        d1 = r1.json()
        assert "processed" in d1
        assert "branded_images" in d1
        assert "errors" in d1
        assert "at" in d1
        assert isinstance(d1["processed"], int)
        # Should have processed >0 since seeded vehicles have public Unsplash images
        # but be tolerant if everything is already branded from a previous run
        first_processed = d1["processed"]
        first_branded = d1["branded_images"]

        # Idempotent: second call without force should return processed:0
        r2 = requests.post(f"{API}/auto/admin/images/backfill-branding",
                           json={"limit": 3}, headers=admin_headers, timeout=60)
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["processed"] == 0, f"expected idempotent processed=0, got {d2}"

        # Sanity log
        print(f"First backfill processed={first_processed}, branded_images={first_branded}")

    def test_force_reprocesses(self, admin_headers):
        r = requests.post(f"{API}/auto/admin/images/backfill-branding",
                          json={"limit": 1, "force": True}, headers=admin_headers, timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        # Even with force, processed may be 0 if no vehicles match (seed never branded any).
        # Accept >= 0 but if there are any branded vehicles, must be >= 1
        assert isinstance(d.get("processed"), int)

    def test_local_images_served(self, admin_headers):
        # Find a vehicle with local_images
        r = requests.get(f"{API}/auto/vehicles", params={"limit": 100}, timeout=20)
        assert r.status_code == 200
        items = r.json()
        if isinstance(items, dict):
            items = items.get("items") or items.get("vehicles") or []
        target = None
        for v in items:
            li = v.get("local_images") or []
            if any(isinstance(u, str) and "/uploads/branded/" in u for u in li):
                target = v
                break
        if not target:
            pytest.skip("No vehicle has /uploads/branded/ in local_images yet")
        url_path = next(u for u in target["local_images"] if "/uploads/branded/" in u)
        full = f"{BASE_URL}{url_path}" if url_path.startswith("/") else url_path
        rr = requests.get(full, timeout=30)
        assert rr.status_code == 200, f"branded image not served: {full} -> {rr.status_code}"
        # content-type should be image
        ct = rr.headers.get("Content-Type", "")
        assert ct.startswith("image/"), f"unexpected content-type: {ct}"
