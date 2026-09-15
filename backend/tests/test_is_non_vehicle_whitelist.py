"""Iter20 - title whitelist tests for is_non_vehicle + regression on cleanup and sold-history."""
import os
import sys
import pytest
import requests

sys.path.insert(0, "/app/backend")
from services.auto_source_importers import is_non_vehicle  # noqa: E402

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
MANHEIM_TRUCKS = "https://www.manheim.co.nz/trucks-machinery/xxx"
MANHEIM_PASS = "https://www.manheim.co.nz/passenger/xxx"


# ---------- whitelist: light-commercial vans / utes under /trucks-machinery/ ----------
@pytest.mark.parametrize("title", [
    "2015 Toyota Hiace ZL 3.0D",
    "2018 Ford Transit LWB",
    "2016 Mercedes-Benz Sprinter 519",
    "2019 Toyota Hilux SR5",
    "2020 Ford Ranger Wildtrak",
    "2017 Nissan Navara ST-X",
    "2018 Volkswagen Amarok TDI",
    "2015 Mazda BT-50 GSX",
])
def test_whitelist_vehicles_pass_under_trucks_url(title):
    assert is_non_vehicle({"title": title, "source_url": MANHEIM_TRUCKS}) is False


# ---------- blacklist wins over whitelist ----------
def test_blacklist_beats_whitelist():
    # "trailer chassis" is in _NON_VEHICLE_TITLE_WORDS and must win over "transit"
    assert is_non_vehicle({"title": "Ford Transit trailer chassis kit",
                          "source_url": MANHEIM_TRUCKS}) is True


# ---------- URL blacklist still drops plain non-vehicles ----------
@pytest.mark.parametrize("title", [
    "BG800 Steel Barrier",
    "Cement Mixer 400L",
])
def test_non_vehicle_titles_under_trucks_url_drop(title):
    assert is_non_vehicle({"title": title, "source_url": MANHEIM_TRUCKS}) is True


# ---------- passenger URL always passes ----------
def test_passenger_url_passes():
    assert is_non_vehicle({"title": "2015 Toyota Corolla",
                          "source_url": MANHEIM_PASS}) is False


# ---------- Regression: cleanup endpoint ----------
@pytest.fixture(scope="module")
def admin_token():
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not configured")
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": "admin@buyanywhere.com",
                            "password": "admin12345"},
                      timeout=15)
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code} {r.text[:120]}")
    tok = r.json().get("access_token") or r.json().get("token")
    if not tok:
        pytest.skip("no token in login response")
    return tok


def test_cleanup_non_vehicles_regression(admin_token):
    r = requests.post(
        f"{BASE_URL}/api/auto/admin/sources/cleanup-non-vehicles",
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=60,
    )
    assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
    data = r.json()
    assert "inspected" in data
    assert "deleted" in data
    assert data["deleted"] == 0, f"expected 0 deletions on clean DB, got {data}"


def test_sold_history_regression(admin_token):
    # grab a vehicle id then hit sold-history
    r = requests.get(f"{BASE_URL}/api/auto/vehicles?limit=1", timeout=15)
    if r.status_code != 200:
        pytest.skip(f"cannot list vehicles: {r.status_code}")
    body = r.json()
    if isinstance(body, list):
        items = body
    else:
        items = body.get("items") or body.get("vehicles") or []
    if not items:
        pytest.skip("no vehicles in DB")
    vid = items[0].get("id") or items[0].get("_id")
    if not vid:
        pytest.skip("vehicle has no id field")
    r2 = requests.get(f"{BASE_URL}/api/auto/vehicles/{vid}/sold-history", timeout=30)
    assert r2.status_code == 200, f"{r2.status_code} {r2.text[:200]}"
    data = r2.json()
    # either aggregated stats or {'status':'insufficient'} shape
    assert isinstance(data, dict)
