"""Encrypted credentials for source authentication (Turners, Manheim, Pickles).

Passwords are encrypted at rest using Fernet (symmetric AES) keyed off
SECRET_KEY in the environment. Only decrypted server-side when needed by the
Playwright session manager.

Design:
  • One row per (source, kind). kind = "buyer" usually, but can be e.g.
    "simulcast" if the platform requires a separate live login.
  • The decrypted password is NEVER returned over HTTP — the admin UI only
    sees "saved (****)" indicators. The admin can update by re-entering.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
import os
from cryptography.fernet import Fernet, InvalidToken
import base64
import hashlib
from pydantic import BaseModel, Field
import uuid


def _fernet() -> Fernet:
    """Derive a stable Fernet key from SECRET_KEY (avoids needing a separate
    env var). If SECRET_KEY is missing we still operate, but the credentials
    are effectively obfuscated rather than securely encrypted."""
    secret = os.environ.get("SECRET_KEY") or "fallback-dev-key-not-for-production"
    raw = hashlib.sha256(secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(raw))


def encrypt(plain: str) -> str:
    return _fernet().encrypt(plain.encode()).decode()


def decrypt(token: str) -> Optional[str]:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except (InvalidToken, ValueError):
        return None


class AutoSourceCredential(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str  # "turners" | "manheim_nz" | "manheim_au" | "pickles"
    kind: str = "buyer"
    label: Optional[str] = None
    username: str
    password_encrypted: str
    extra_json: Optional[str] = None  # e.g. dealer-account-id, TOTP secret
    enabled: bool = True
    last_login_at: Optional[datetime] = None
    last_status: Optional[str] = None  # "ok" | "login_failed" | "challenge_required"
    last_error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AutoSourceCredentialCreate(BaseModel):
    source: str
    kind: str = "buyer"
    label: Optional[str] = None
    username: str
    password: str  # plain — encrypted before storing
    extra_json: Optional[str] = None
    enabled: bool = True


def to_admin_view(doc: dict) -> dict:
    """Strip the encrypted blob before returning to the admin UI."""
    out = dict(doc)
    out.pop("password_encrypted", None)
    out.pop("_id", None)
    out["has_password"] = bool(doc.get("password_encrypted"))
    for k in ("created_at", "updated_at", "last_login_at"):
        v = out.get(k)
        if isinstance(v, datetime):
            out[k] = v.isoformat()
    return out
