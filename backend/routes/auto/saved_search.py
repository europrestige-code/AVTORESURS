"""Saved-search endpoints + Telegram binding flow.

Telegram binding works like this:
1. Logged-in user clicks «Привязать Telegram» on the «Мои подписки» page.
2. We hand them a deep link `https://t.me/<bot_username>?start=link_<token>`.
3. They open the bot and press Start → Telegram pings our webhook with the
   `text="/start link_<token>"` payload.
4. We look the token up in `auto_tg_link_tokens`, attach the user's chat_id
   to their user record and to all their existing saved searches, then reply
   in the chat «Привязка успешна».

The bot username is configured via env var; for testing the user can also
paste their chat id directly via a POST endpoint.
"""
from __future__ import annotations

import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request

from models.auto_saved_search import (
    SavedSearchCreate,
    SavedSearchFilters,
)

from ._deps import get_db, require_admin, require_user

logger = logging.getLogger(__name__)
router = APIRouter()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------- Saved-search CRUD ----------

@router.post("/saved-searches")
async def create_saved_search(
    payload: SavedSearchCreate,
    user: Dict[str, Any] = Depends(require_user),
    db=Depends(get_db),
):
    from services.auto_saved_search_service import AutoSavedSearchService
    svc = AutoSavedSearchService(db)
    res = await svc.create(
        payload,
        user_id=user["id"],
        email=user.get("email"),
        telegram_chat_id=user.get("auto_tg_chat_id"),
    )
    return res


@router.get("/saved-searches")
async def list_saved_searches(
    user: Dict[str, Any] = Depends(require_user),
    db=Depends(get_db),
):
    from services.auto_saved_search_service import AutoSavedSearchService
    svc = AutoSavedSearchService(db)
    return {"items": await svc.list_for_user(user["id"])}


@router.delete("/saved-searches/{search_id}")
async def delete_saved_search(
    search_id: str,
    user: Dict[str, Any] = Depends(require_user),
    db=Depends(get_db),
):
    from services.auto_saved_search_service import AutoSavedSearchService
    svc = AutoSavedSearchService(db)
    if not await svc.delete(search_id, user["id"]):
        raise HTTPException(404, "Подписка не найдена.")
    return {"ok": True}


@router.patch("/saved-searches/{search_id}/toggle")
async def toggle_saved_search(
    search_id: str,
    payload: Dict[str, Any] = Body(...),
    user: Dict[str, Any] = Depends(require_user),
    db=Depends(get_db),
):
    from services.auto_saved_search_service import AutoSavedSearchService
    svc = AutoSavedSearchService(db)
    r = await svc.toggle(search_id, user["id"], bool(payload.get("enabled", True)))
    if not r:
        raise HTTPException(404, "Подписка не найдена.")
    return r


@router.post("/saved-searches/preview")
async def preview_matches(
    payload: SavedSearchFilters,
    db=Depends(get_db),
):
    """Anonymous-friendly: returns the top vehicles that would match the
    given filters right now. Used by the «Save search» modal to show what
    the user will get notified about."""
    from services.auto_fx_service import get_fx_rate
    from services.auto_saved_search_service import AutoSavedSearchService
    fx = await get_fx_rate()
    rate = float(fx.get("nzd_to_rub_display") or 57.68)
    svc = AutoSavedSearchService(db)
    matches = await svc.preview_matches(payload, fx_rate=rate, limit=6)
    return {"matches": matches, "fx_rate": rate}


# ---------- Admin run trigger ----------

@router.post("/admin/saved-searches/run")
async def admin_run_saved_searches(
    _: Dict[str, Any] = Depends(require_admin),
    db=Depends(get_db),
):
    """Manually trigger the saved-search run (otherwise driven by the
    scheduler)."""
    from services.auto_saved_search_service import AutoSavedSearchService
    return await AutoSavedSearchService(db).run_all()


# ---------- Telegram binding ----------

_BOT_USERNAME = os.environ.get("TELEGRAM_BOT_USERNAME") or "AvtoresursAlertsBot"


@router.post("/telegram/start-binding")
async def start_telegram_binding(
    user: Dict[str, Any] = Depends(require_user),
    db=Depends(get_db),
):
    """Issue a short-lived deep-link token. Frontend renders the resulting
    `t.me/<bot>?start=link_<token>` URL as a QR + button."""
    token = secrets.token_urlsafe(12)
    await db.auto_tg_link_tokens.insert_one({
        "token": token,
        "user_id": user["id"],
        "created_at": _now(),
        "expires_at": _now() + timedelta(minutes=15),
        "used": False,
    })
    deep_link = f"https://t.me/{_BOT_USERNAME}?start=link_{token}"
    return {"deep_link": deep_link, "token": token, "bot_username": _BOT_USERNAME}


@router.get("/telegram/binding-status")
async def telegram_binding_status(
    user: Dict[str, Any] = Depends(require_user),
    db=Depends(get_db),
):
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0, "auto_tg_chat_id": 1})
    chat_id = (u or {}).get("auto_tg_chat_id")
    return {"bound": bool(chat_id), "chat_id": chat_id}


@router.post("/telegram/unbind")
async def telegram_unbind(
    user: Dict[str, Any] = Depends(require_user),
    db=Depends(get_db),
):
    await db.users.update_one({"id": user["id"]}, {"$unset": {"auto_tg_chat_id": ""}})
    await db.auto_saved_searches.update_many(
        {"user_id": user["id"]}, {"$unset": {"telegram_chat_id": ""}}
    )
    return {"ok": True}


@router.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    db=Depends(get_db),
):
    """Telegram pushes every update here. We only care about /start link_<token>
    payloads and ignore the rest."""
    from services.auto_notify_service import send_telegram_message
    try:
        update = await request.json()
    except Exception:
        return {"ok": True}
    message = (update or {}).get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = (message.get("text") or "").strip()
    if not chat_id:
        return {"ok": True}

    # /start link_<token>
    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        payload = parts[1] if len(parts) > 1 else ""
        if payload.startswith("link_"):
            token = payload[5:]
            doc = await db.auto_tg_link_tokens.find_one({"token": token, "used": False})
            expires = (doc or {}).get("expires_at")
            if expires and expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if not doc or (expires and expires < _now()):
                await send_telegram_message(
                    chat_id, "❌ Ссылка устарела. Запросите новую на сайте."
                )
                return {"ok": True}
            await db.users.update_one(
                {"id": doc["user_id"]},
                {"$set": {"auto_tg_chat_id": int(chat_id)}},
            )
            await db.auto_saved_searches.update_many(
                {"user_id": doc["user_id"]},
                {"$set": {"telegram_chat_id": int(chat_id)}},
            )
            await db.auto_tg_link_tokens.update_one(
                {"token": token},
                {"$set": {"used": True, "used_at": _now(), "chat_id": int(chat_id)}},
            )
            await send_telegram_message(
                chat_id,
                "✅ <b>Привязка успешна!</b>\nТеперь я буду присылать сюда новые "
                "авто по вашим подпискам АвтоРесурс."
            )
            return {"ok": True}

    # Generic welcome
    await send_telegram_message(
        chat_id,
        "👋 Привет! Я бот <b>АвтоРесурс</b>. Чтобы получать уведомления, "
        "войдите на сайте → «Мои подписки» → «Привязать Telegram»."
    )
    return {"ok": True}


@router.post("/admin/telegram/set-webhook")
async def admin_set_telegram_webhook(
    payload: Optional[Dict[str, Any]] = Body(None),
    _: Dict[str, Any] = Depends(require_admin),
):
    """Idempotent helper that registers our /api/auto/telegram/webhook URL
    with Telegram. Pass {"url": "https://..."} to override the auto-detected
    public URL."""
    import httpx
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise HTTPException(400, "TELEGRAM_BOT_TOKEN не настроен.")
    payload = payload or {}
    base = (
        payload.get("url")
        or os.environ.get("PUBLIC_BACKEND_URL")
        or os.environ.get("PUBLIC_FRONTEND_URL")
        or "https://auto-nz-bidding.preview.emergentagent.com"
    ).rstrip("/")
    webhook_url = f"{base}/api/auto/telegram/webhook"
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(
            f"https://api.telegram.org/bot{token}/setWebhook",
            json={"url": webhook_url, "drop_pending_updates": True},
        )
    return {"webhook_url": webhook_url, "telegram": r.json()}
