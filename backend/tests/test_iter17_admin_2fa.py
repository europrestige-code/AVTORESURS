"""Iter17 — Admin 2FA (TOTP) backend coverage.

Flow:
  1. Login as admin → grab JWT.
  2. GET /admin/2fa/status → enabled:False.
  3. POST /admin/2fa/setup → secret + qr_data_url + provisioning_uri.
  4. POST /admin/2fa/verify-setup with wrong code → 400; with correct → ok+mfa_token.
  5. Subsequent /admin/* call WITHOUT MFA header → 401 (mentions "двухфакторной").
  6. POST /admin/2fa/login wrong → 401, correct → fresh mfa_token.
  7. /admin/* WITH MFA header → 200.
  8. Customer hitting /admin/2fa/setup → 403.
  9. Cleanup: disable 2FA with correct code → ok and status flips back.
"""
from __future__ import annotations

import os
import time

import pyotp
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://auto-nz-bidding.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@buyanywhere.com"
ADMIN_PASS = "admin12345"
CLIENT_EMAIL = "client@buyanywhere.com"
CLIENT_PASS = "client12345"


def _login(email: str, password: str) -> str:
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, f"login failed for {email}: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_token() -> str:
    return _login(ADMIN_EMAIL, ADMIN_PASS)


@pytest.fixture(scope="module")
def client_token() -> str:
    return _login(CLIENT_EMAIL, CLIENT_PASS)


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


def _force_disable(admin_headers):
    """Best-effort reset using current secret if 2FA is on."""
    s = requests.get(f"{API}/auto/admin/2fa/status", headers=admin_headers, timeout=15)
    if s.status_code == 200 and s.json().get("enabled"):
        # try to fetch secret via setup (refuses if enabled). Use direct disable via fresh code.
        # We have to know the secret — if we don't, we cannot disable without re-enabling.
        pytest.skip("2FA already enabled with unknown secret — manual reset required.")


def test_01_status_initially_disabled(admin_headers):
    _force_disable(admin_headers)
    r = requests.get(f"{API}/auto/admin/2fa/status", headers=admin_headers, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["enabled"] is False
    assert "has_pending_secret" in data


def test_02_setup_returns_secret_qr_and_uri(admin_headers):
    r = requests.post(f"{API}/auto/admin/2fa/setup", headers=admin_headers, timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["enabled"] is False
    assert isinstance(d["secret"], str) and len(d["secret"]) == 32
    assert d["qr_data_url"].startswith("data:image/png;base64,")
    assert d["provisioning_uri"].startswith("otpauth://")
    assert d["issuer"] == "AvtoResurs Admin"
    # stash on module so subsequent tests can read it
    pytest.SECRET = d["secret"]


def test_03_setup_idempotent_same_secret(admin_headers):
    r = requests.post(f"{API}/auto/admin/2fa/setup", headers=admin_headers, timeout=15)
    assert r.status_code == 200
    # The endpoint reuses the pending secret
    assert r.json()["secret"] == pytest.SECRET


def test_04_verify_setup_wrong_code_400(admin_headers):
    r = requests.post(f"{API}/auto/admin/2fa/verify-setup", json={"code": "000000"}, headers=admin_headers, timeout=15)
    assert r.status_code == 400, r.text


def test_05_verify_setup_correct_returns_mfa_token(admin_headers):
    code = pyotp.TOTP(pytest.SECRET).now()
    r = requests.post(f"{API}/auto/admin/2fa/verify-setup", json={"code": code}, headers=admin_headers, timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["ok"] is True
    assert "mfa_token" in d
    body, _, sig = d["mfa_token"].partition(".")
    assert body and sig
    pytest.MFA_TOKEN = d["mfa_token"]


def test_06_admin_endpoint_without_mfa_header_401(admin_headers):
    r = requests.get(f"{API}/auto/admin/clients?limit=1", headers=admin_headers, timeout=15)
    assert r.status_code == 401, r.text
    assert "двухфакторной" in r.text


def test_07_admin_endpoint_with_mfa_header_200(admin_headers):
    h = {**admin_headers, "X-Admin-MFA-Token": pytest.MFA_TOKEN}
    r = requests.get(f"{API}/auto/admin/clients?limit=1", headers=h, timeout=20)
    assert r.status_code == 200, r.text


def test_08_login_wrong_code_401(admin_headers):
    r = requests.post(f"{API}/auto/admin/2fa/login", json={"code": "000000"}, headers=admin_headers, timeout=15)
    assert r.status_code == 401, r.text


def test_09_login_correct_returns_fresh_token(admin_headers):
    code = pyotp.TOTP(pytest.SECRET).now()
    r = requests.post(f"{API}/auto/admin/2fa/login", json={"code": code}, headers=admin_headers, timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert "mfa_token" in d
    assert d["expires_in"] == 3600


def test_10_customer_cannot_setup_2fa(client_token):
    r = requests.post(
        f"{API}/auto/admin/2fa/setup",
        headers={"Authorization": f"Bearer {client_token}"},
        timeout=15,
    )
    assert r.status_code == 403, r.text


def test_11_status_does_not_require_mfa_header(admin_headers):
    # Status itself must work even when 2FA is enabled, no MFA header.
    r = requests.get(f"{API}/auto/admin/2fa/status", headers=admin_headers, timeout=15)
    assert r.status_code == 200
    assert r.json()["enabled"] is True


def test_12_disable_with_correct_code(admin_headers):
    # ensure a fresh OTP window to avoid reusing the verify-setup code
    time.sleep(1)
    code = pyotp.TOTP(pytest.SECRET).now()
    r = requests.post(f"{API}/auto/admin/2fa/disable", json={"code": code}, headers=admin_headers, timeout=15)
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True
    # Status flips back
    s = requests.get(f"{API}/auto/admin/2fa/status", headers=admin_headers, timeout=15)
    assert s.status_code == 200
    assert s.json()["enabled"] is False


# ---------- Regression (iter14/15/16) ----------

def test_R1_catalog_at_least_1000():
    r = requests.get(f"{API}/auto/vehicles?limit=1", timeout=20)
    assert r.status_code == 200
    j = r.json()
    total = j.get("total") or j.get("count") or 0
    assert total >= 1000, f"catalog dropped below 1000: {total}"


def test_R2_payment_terms_tiered():
    r = requests.get(f"{API}/auto/payment-terms", timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert d["base_deposit_nzd"] == 1000
    assert d["tier1_percent"] == 20
    assert d["tier2_percent"] == 30
