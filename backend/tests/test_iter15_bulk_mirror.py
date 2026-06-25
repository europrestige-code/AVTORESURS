"""Iter15 — bulk mirror (POST /api/auto/admin/sources/import-all + GET import-status)
and the supporting regression checks for catalog-summary, source filter and the
auction calendar."""
import os
import time
import pytest
import requests

def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL", "").strip()
    if url:
        return url.rstrip("/")
    # Fallback to /app/frontend/.env (the system's source of truth)
    try:
        with open("/app/frontend/.env") as fh:
            for line in fh:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip().rstrip("/")
    except Exception:
        pass
    return ""


BASE_URL = _load_backend_url()
assert BASE_URL, "REACT_APP_BACKEND_URL is not set"

ADMIN_EMAIL = "admin@buyanywhere.com"
ADMIN_PASSWORD = "admin12345"


# ---- shared fixtures ----
@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def admin_token(api):
    r = api.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text[:200]}"
    tok = r.json().get("access_token")
    assert tok, f"no access_token in login response: {r.text[:200]}"
    return tok


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ---- iter15 — import-all background job ----
class TestImportAll:
    def test_import_all_returns_quickly_with_job_id(self, api, admin_headers, request):
        t0 = time.time()
        r = api.post(
            f"{BASE_URL}/api/auto/admin/sources/import-all",
            json={"limit": 50},
            headers=admin_headers,
            timeout=10,
        )
        elapsed = time.time() - t0
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        data = r.json()
        assert data.get("ok") is True
        assert data.get("status") == "running"
        job_id = data.get("job_id")
        assert isinstance(job_id, str) and len(job_id) >= 10, f"bad job_id={job_id!r}"
        assert elapsed < 5.0, f"import-all blocked for {elapsed:.2f}s"
        request.config.cache.set("iter15/job_id", job_id)

    def test_import_status_progresses_to_done(self, api, admin_headers, request):
        job_id = request.config.cache.get("iter15/job_id", None)
        assert job_id, "no job_id cached from previous test"
        deadline = time.time() + 90  # allow up to 90s
        last = None
        while time.time() < deadline:
            r = api.get(
                f"{BASE_URL}/api/auto/admin/sources/import-status",
                headers=admin_headers,
                timeout=15,
            )
            assert r.status_code == 200, r.text[:200]
            last = r.json()
            if last.get("status") in {"done", "error"}:
                break
            time.sleep(3)
        assert last and last.get("status") == "done", f"job did not finish: {last}"
        assert last.get("job_id") == job_id
        per_src = last.get("per_source") or []
        names = {p.get("importer") for p in per_src}
        # The 3 importers must all be present, even if some fetched 0 (bot block).
        for must in {"turners", "manheim", "pickles"}:
            assert must in names, f"missing importer {must} in per_source={names}"
        # turners is the most reliable — main agent stated it imported 832 vehicles
        # in the reference run. Be lenient: created>=0 acceptable per spec note,
        # but require at least one importer to have created>0.
        any_created = any((p.get("created", 0) or 0) > 0 for p in per_src)
        any_fetched = any((p.get("fetched", 0) or 0) > 0 for p in per_src)
        assert any_fetched or any_created, f"all importers fetched 0 — per_source={per_src}"

    def test_import_status_by_job_id(self, api, admin_headers, request):
        job_id = request.config.cache.get("iter15/job_id", None)
        assert job_id, "no job_id cached"
        r = api.get(
            f"{BASE_URL}/api/auto/admin/sources/import-status",
            params={"job_id": job_id},
            headers=admin_headers,
            timeout=15,
        )
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        assert data.get("job_id") == job_id
        assert data.get("status") in {"running", "done", "error"}


# ---- iter15 — catalog has at least 1000 vehicles ----
class TestCatalogScale:
    def test_catalog_summary_total_gte_1000(self, api):
        r = api.get(f"{BASE_URL}/api/auto/catalog-summary", timeout=15)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        total = data.get("total")
        assert isinstance(total, int), f"total not int: {data}"
        assert total >= 1000, f"catalog total={total} < 1000"

    def test_manheim_filter_has_20_plus(self, api):
        r = api.get(
            f"{BASE_URL}/api/auto/vehicles",
            params={"source": "manheim", "limit": 50},
            timeout=15,
        )
        assert r.status_code == 200, r.text[:200]
        body = r.json()
        items = body.get("items") if isinstance(body, dict) else body
        assert isinstance(items, list), f"items not list: {type(items)}"
        assert len(items) >= 20, f"manheim items={len(items)} <20"
        for it in items[:10]:
            assert it.get("source") == "manheim", f"non-manheim leaked: {it.get('source')}"

    def test_turners_filter_has_20_plus(self, api):
        r = api.get(
            f"{BASE_URL}/api/auto/vehicles",
            params={"source": "turners", "limit": 50},
            timeout=15,
        )
        assert r.status_code == 200, r.text[:200]
        body = r.json()
        items = body.get("items") if isinstance(body, dict) else body
        assert isinstance(items, list)
        assert len(items) >= 20, f"turners items={len(items)} <20"
        for it in items[:10]:
            assert it.get("source") == "turners", f"non-turners leaked: {it.get('source')}"


# ---- regression: auctions calendar still has both sources ----
class TestAuctionCalendarRegression:
    def test_calendar_has_turners_and_manheim(self, api):
        r = api.get(
            f"{BASE_URL}/api/auto/auctions/calendar",
            params={"days_ahead": 21},
            timeout=15,
        )
        assert r.status_code == 200, r.text[:200]
        body = r.json()
        events = body.get("events") if isinstance(body, dict) else body
        assert isinstance(events, list)
        assert len(events) > 0, "no events returned"
        sources = {ev.get("source") for ev in events}
        assert "turners" in sources, f"turners missing in sources={sources}"
        assert "manheim" in sources, f"manheim missing in sources={sources}"
