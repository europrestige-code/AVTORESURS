"""Admin 2FA service — TOTP (RFC 6238) compatible with Google Authenticator,
Authy, 1Password, etc.

The secret is stored on the admin's user document (`auto_totp_secret`,
`auto_totp_enabled`). After password login the admin exchanges a 6-digit
OTP for a short-lived MFA token (1h) that the `require_admin` dependency
validates on every protected request.
"""
from __future__ import annotations

import base64
import io
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import pyotp
import qrcode

# Symmetric secret for signing MFA tokens. Reuse JWT_SECRET if present.
_MFA_SECRET = (
    os.environ.get("ADMIN_MFA_SECRET")
    or os.environ.get("JWT_SECRET")
    or "buyanywhere-admin-mfa-2026"
)
MFA_TOKEN_TTL_SECONDS = 60 * 60  # 1 hour
ISSUER_LABEL = "AvtoResurs Admin"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def make_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(secret: str, account: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=account, issuer_name=ISSUER_LABEL)


def qr_data_url(uri: str) -> str:
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def verify_code(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    # ±1 window (~90s) to tolerate clock drift
    return pyotp.TOTP(secret).verify(code.strip(), valid_window=1)


# ---------- MFA token (HMAC-based, JWT-like) ----------

def issue_mfa_token(user_id: str) -> str:
    import hmac
    import hashlib
    import json
    payload = {"uid": user_id, "exp": int(time.time()) + MFA_TOKEN_TTL_SECONDS,
               "iat": int(time.time()), "nonce": secrets.token_hex(6)}
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    sig = hmac.new(_MFA_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def verify_mfa_token(token: Optional[str]) -> Optional[Dict[str, Any]]:
    if not token or "." not in token:
        return None
    import hmac
    import hashlib
    import json
    body, sig = token.rsplit(".", 1)
    expected = hmac.new(_MFA_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        padded = body + "=" * (-len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode()))
    except Exception:
        return None
    if payload.get("exp", 0) < time.time():
        return None
    return payload


# ---------- DB helpers ----------

class Admin2FAService:
    def __init__(self, db):
        self.db = db

    async def status(self, user_id: str) -> Dict[str, Any]:
        u = await self.db.users.find_one({"id": user_id}, {"_id": 0, "auto_totp_enabled": 1, "auto_totp_secret": 1})
        return {
            "enabled": bool((u or {}).get("auto_totp_enabled")),
            "has_pending_secret": bool((u or {}).get("auto_totp_secret")) and not bool((u or {}).get("auto_totp_enabled")),
        }

    async def start_setup(self, user_id: str, email: str) -> Dict[str, Any]:
        """Generate (or reuse pending) secret and return QR-code data URL."""
        u = await self.db.users.find_one({"id": user_id}, {"_id": 0, "auto_totp_secret": 1, "auto_totp_enabled": 1})
        if u and u.get("auto_totp_enabled") and u.get("auto_totp_secret"):
            # Already enabled — refuse to leak the existing secret.
            return {"enabled": True, "qr_data_url": None, "secret": None}
        secret = (u or {}).get("auto_totp_secret") or make_secret()
        await self.db.users.update_one(
            {"id": user_id},
            {"$set": {"auto_totp_secret": secret, "auto_totp_enabled": False,
                      "auto_totp_setup_started_at": _now()}},
        )
        uri = provisioning_uri(secret, account=email)
        return {"enabled": False, "secret": secret, "qr_data_url": qr_data_url(uri),
                "provisioning_uri": uri, "issuer": ISSUER_LABEL}

    async def verify_and_enable(self, user_id: str, code: str) -> bool:
        u = await self.db.users.find_one({"id": user_id}, {"_id": 0, "auto_totp_secret": 1})
        if not u or not u.get("auto_totp_secret"):
            return False
        if not verify_code(u["auto_totp_secret"], code):
            return False
        await self.db.users.update_one(
            {"id": user_id},
            {"$set": {"auto_totp_enabled": True, "auto_totp_enabled_at": _now()}},
        )
        return True

    async def disable(self, user_id: str, code: str) -> bool:
        u = await self.db.users.find_one({"id": user_id}, {"_id": 0, "auto_totp_secret": 1, "auto_totp_enabled": 1})
        if not u or not u.get("auto_totp_enabled"):
            return False
        if not verify_code(u.get("auto_totp_secret"), code):
            return False
        await self.db.users.update_one(
            {"id": user_id},
            {"$set": {"auto_totp_enabled": False},
             "$unset": {"auto_totp_secret": "", "auto_totp_enabled_at": ""}},
        )
        return True

    async def exchange_code_for_token(self, user_id: str, code: str) -> Optional[str]:
        u = await self.db.users.find_one({"id": user_id}, {"_id": 0, "auto_totp_secret": 1, "auto_totp_enabled": 1})
        if not u or not u.get("auto_totp_enabled") or not u.get("auto_totp_secret"):
            return None
        if not verify_code(u["auto_totp_secret"], code):
            return None
        return issue_mfa_token(user_id)
