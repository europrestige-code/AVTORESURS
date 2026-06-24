"""
АвтоРесурс — runtime-editable app settings.

A single-document collection (`app_settings`) holds all the operator-tunable
keys and switches that used to live in environment variables: payment keys,
email/SMS provider credentials, contact info, currency markup, social URLs,
etc. Settings are read by other services through `get_settings()` which
caches for 30 seconds (cheap reload after admin saves).

Security:
  - Reads are admin-only via /api/auto/admin/settings.
  - GET MASKS secrets (last 4 chars shown) before returning to the UI.
  - PUT only overwrites a key when the new value is non-empty AND not the
    "MASKED" placeholder — so the operator can leave a secret field blank
    in the form without zapping the stored value.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional

# Keys + their UI metadata. Tagged `secret` are masked when read.
SETTINGS_SCHEMA: List[Dict[str, Any]] = [
    # --- Contacts / public info ---
    {"key": "public_frontend_url",       "group": "contacts", "label": "Публичный URL фронтенда",  "type": "text"},
    {"key": "support_email",             "group": "contacts", "label": "Email поддержки",          "type": "text", "default": "europrestige@gmail.com"},
    {"key": "support_phone_nz",          "group": "contacts", "label": "Телефон NZ",               "type": "text", "default": "+64 21 425 233"},
    {"key": "support_phone_ru",          "group": "contacts", "label": "Телефон RU",               "type": "text", "default": "+7 913 512 1934"},
    {"key": "whatsapp_url",              "group": "contacts", "label": "WhatsApp URL",             "type": "text", "default": "https://wa.me/6421425233"},
    {"key": "telegram_url",              "group": "contacts", "label": "Telegram URL",             "type": "text", "default": "https://t.me/avtoresurs"},
    {"key": "office_address",            "group": "contacts", "label": "Адрес офиса",              "type": "text", "default": "Auckland, New Zealand"},

    # --- Currency ---
    {"key": "currency_markup_pct",       "group": "currency", "label": "Наценка к курсу Google (%)", "type": "number", "default": 3},
    {"key": "deposit_amount_nzd",        "group": "currency", "label": "Размер депозита (NZ$)",     "type": "number", "default": 1000},

    # --- Email provider ---
    {"key": "email_provider",            "group": "email",    "label": "Провайдер email",
        "type": "select", "options": ["stub", "sendsay", "mailchimp", "resend"], "default": "stub"},
    {"key": "email_provider_api_key",    "group": "email",    "label": "API ключ email-провайдера",  "type": "secret"},
    {"key": "email_from_address",        "group": "email",    "label": "From email",                 "type": "text", "default": "info@avtoresurs.nz"},
    {"key": "email_from_name",           "group": "email",    "label": "From имя",                   "type": "text", "default": "АвтоРесурс"},
    {"key": "email_campaigns_per_day",   "group": "email",    "label": "Кампаний в день (макс)",     "type": "number", "default": 2},
    {"key": "email_cars_per_campaign",   "group": "email",    "label": "Авто в кампании (макс)",     "type": "number", "default": 5},

    # --- SMS provider ---
    {"key": "sms_provider",              "group": "sms",      "label": "Провайдер SMS",
        "type": "select", "options": ["none", "twilio", "smsc"], "default": "none"},
    {"key": "sms_provider_account_sid",  "group": "sms",      "label": "Account SID / Логин",         "type": "secret"},
    {"key": "sms_provider_auth_token",   "group": "sms",      "label": "Auth token / Пароль",         "type": "secret"},
    {"key": "sms_from_number",           "group": "sms",      "label": "From номер",                  "type": "text"},

    # --- Payments ---
    {"key": "stripe_publishable_key",    "group": "payments", "label": "Stripe publishable key",      "type": "text"},
    {"key": "stripe_secret_key",         "group": "payments", "label": "Stripe secret key",           "type": "secret"},
    {"key": "stripe_webhook_secret",     "group": "payments", "label": "Stripe webhook secret",       "type": "secret"},

    # --- AI ---
    {"key": "ai_chat_persona_name",      "group": "ai",       "label": "Имя AI-ассистента",           "type": "text", "default": "Татьяна"},
    {"key": "ai_chat_enabled",           "group": "ai",       "label": "Чат включён",                  "type": "bool", "default": True},
]

SETTINGS_KEYS = [s["key"] for s in SETTINGS_SCHEMA]
SECRET_KEYS = {s["key"] for s in SETTINGS_SCHEMA if s.get("type") == "secret"}

_SINGLETON_ID = "default"
_TTL_SEC = 30.0
_cache: Optional[Dict[str, Any]] = None
_cache_at: float = 0.0
_lock = asyncio.Lock()


def _defaults() -> Dict[str, Any]:
    return {s["key"]: s.get("default") for s in SETTINGS_SCHEMA if "default" in s}


async def get_settings(db, *, force_refresh: bool = False) -> Dict[str, Any]:
    """Return the current settings dict (defaults merged in)."""
    global _cache, _cache_at
    async with _lock:
        now = time.time()
        if (not force_refresh) and _cache and (now - _cache_at) < _TTL_SEC:
            return dict(_cache)
        doc = await db.app_settings.find_one({"_sid": _SINGLETON_ID}) or {}
        doc.pop("_id", None)
        doc.pop("_sid", None)
        merged = {**_defaults(), **doc}
        _cache = merged
        _cache_at = now
        return dict(merged)


async def get_setting(db, key: str, default: Any = None) -> Any:
    s = await get_settings(db)
    return s.get(key, default)


def _mask(val: str) -> str:
    if not val:
        return ""
    s = str(val)
    if len(s) <= 4:
        return "****"
    return f"••••{s[-4:]}"


async def list_for_admin(db) -> Dict[str, Any]:
    """Like get_settings, but secrets masked."""
    s = await get_settings(db, force_refresh=True)
    safe = {}
    for k, v in s.items():
        if k in SECRET_KEYS:
            safe[k] = _mask(v)
        else:
            safe[k] = v
    return {"schema": SETTINGS_SCHEMA, "values": safe}


async def update_settings(db, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Apply partial updates. Secret fields that come back empty OR with the
    masked-placeholder value are preserved (not overwritten)."""
    current = await get_settings(db, force_refresh=True)
    final: Dict[str, Any] = {}
    for k, v in updates.items():
        if k not in SETTINGS_KEYS:
            continue
        if k in SECRET_KEYS:
            if v in (None, "", current.get(k)) or (isinstance(v, str) and v.startswith("••••")):
                continue   # keep existing
        final[k] = v
    if not final:
        return await list_for_admin(db)
    from datetime import datetime, timezone
    final["_updated_at"] = datetime.now(timezone.utc)
    await db.app_settings.update_one(
        {"_sid": _SINGLETON_ID},
        {"$set": {"_sid": _SINGLETON_ID, **final}},
        upsert=True,
    )
    # bust cache
    global _cache_at
    _cache_at = 0.0
    return await list_for_admin(db)
