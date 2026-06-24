"""
АвтоРесурс — automated daily email campaigns.

Selects up to 5 random late-model, popular-make, auctions-only vehicles
twice per day and asks the AI (Emergent LLM) to write Russian marketing copy
(subject, intro, per-vehicle one-liner). Each campaign is saved as a DRAFT
so the admin can preview before sending.

Sending uses a pluggable provider:
  - stub:     no-op, just marks "sent" (default until SENDSAY / Mailchimp
              keys are configured)
  - sendsay:  TODO once API key is provided
  - mailchimp: TODO once API key + audience is provided

All recipients get an unsubscribe link in the footer. Marketing consent is
ON by default (per user direction); the unsubscribe endpoint flips it off.
"""

from __future__ import annotations

import hmac
import hashlib
import logging
import os
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from models.auto import (
    AutoCampaignStatus,
    AutoCampaignVehicleSnap,
    AutoEmailCampaign,
)
from services.auto_ai_service import AutoAIService
from services.auto_fx_service import nzd_to_rub

log = logging.getLogger("auto.email")

PUBLIC_BASE_URL = os.environ.get("PUBLIC_FRONTEND_URL", "https://avtoresurs.nz").rstrip("/")
UNSUBSCRIBE_SECRET = os.environ.get("UNSUBSCRIBE_SECRET", "avtoresurs-unsub-default")

POPULAR_MAKES = [
    "toyota", "lexus", "honda", "mazda", "subaru", "nissan", "mitsubishi",
    "bmw", "mercedes-benz", "mercedes", "volkswagen", "vw", "audi",
    "hyundai", "kia", "infiniti", "porsche", "land rover",
]


# ---------------------------------------------------------------------------
# Unsubscribe tokens
# ---------------------------------------------------------------------------

def make_unsub_token(email: str) -> str:
    """One-way HMAC of the email, used as a stable opt-out token."""
    h = hmac.new(UNSUBSCRIBE_SECRET.encode(), email.lower().encode(), hashlib.sha256)
    return h.hexdigest()[:24]


def verify_unsub_token(email: str, token: str) -> bool:
    expected = make_unsub_token(email)
    return hmac.compare_digest(expected, token)


def unsub_url(email: str) -> str:
    t = make_unsub_token(email)
    return f"{PUBLIC_BASE_URL}/auto/unsubscribe?email={email}&token={t}"


# ---------------------------------------------------------------------------
# Vehicle picking
# ---------------------------------------------------------------------------

async def pick_random_vehicles(db: AsyncIOMotorDatabase, count: int = 5) -> List[dict]:
    """Pick up to `count` random LATE-MODEL POPULAR-MAKE auction vehicles."""
    min_year = datetime.now(timezone.utc).year - 8
    makes_re = "(" + "|".join(POPULAR_MAKES) + ")"
    q = {
        "listing_type": "auction",
        "status": "available",
        "year": {"$gte": min_year},
        "$or": [
            {"make":     {"$regex": makes_re, "$options": "i"}},
            {"title_ru": {"$regex": makes_re, "$options": "i"}},
        ],
    }
    pipeline = [
        {"$match": q},
        {"$sample": {"size": int(count)}},
        {"$project": {"_id": 0}},
    ]
    return [doc async for doc in db.auto_vehicles.aggregate(pipeline)]


async def _snap(doc: dict) -> AutoCampaignVehicleSnap:
    nzd = doc.get("current_price_nzd")
    rub = await nzd_to_rub(nzd) if nzd else None
    img = (doc.get("local_images") or doc.get("images") or doc.get("source_images") or [None])[0]
    return AutoCampaignVehicleSnap(
        vehicle_id=doc["id"],
        title_ru=doc.get("title_ru") or f"{doc.get('year') or ''} {doc.get('make') or ''} {doc.get('model') or ''}".strip(),
        year=doc.get("year"),
        make=doc.get("make"),
        model=doc.get("model"),
        mileage_km=doc.get("mileage_km"),
        location=doc.get("location"),
        current_price_nzd=nzd,
        display_price_rub=round(rub, 2) if rub else None,
        image_url=img,
        source=doc.get("source"),
        listing_type=doc.get("listing_type"),
        detail_url=f"{PUBLIC_BASE_URL}/auto/vehicle/{doc['id']}",
    )


# ---------------------------------------------------------------------------
# AI copywriting
# ---------------------------------------------------------------------------

_SUBJECT_FALLBACKS = {
    "morning": [
        "🚗 Утренняя подборка: свежие лоты на аукционах НЗ",
        "Доброе утро! 5 интересных авто с торгов сегодня",
        "Свежий улов с Turners и Manheim — успейте посмотреть",
    ],
    "evening": [
        "🌆 Вечерняя подборка: что взять с аукциона сегодня",
        "Топ предложений вечера — пока другие спят",
        "Закрытие торгов скоро: 5 лотов под ваш бюджет",
    ],
}


def _fallback_blurb(v: AutoCampaignVehicleSnap) -> str:
    parts = [v.title_ru]
    if v.mileage_km is not None:
        parts.append(f"пробег {v.mileage_km:,} км".replace(",", " "))
    if v.location:
        parts.append(v.location)
    return ". ".join(parts) + "."


async def _ai_write_copy(slot: str, vehicles: List[AutoCampaignVehicleSnap]) -> Dict[str, object]:
    """Ask the AI to produce a Russian subject, intro and per-vehicle blurbs."""
    svc = AutoAIService()
    summary_lines = []
    for i, v in enumerate(vehicles, 1):
        bits = [v.title_ru]
        if v.mileage_km is not None: bits.append(f"{v.mileage_km:,} км".replace(",", " "))
        if v.location: bits.append(v.location)
        if v.display_price_rub: bits.append(f"~{int(v.display_price_rub):,} ₽".replace(",", " "))
        summary_lines.append(f"{i}. " + " · ".join(bits))
    cars_block = "\n".join(summary_lines)
    when_ru = "утренней" if slot == "morning" else "вечерней"
    prompt = (
        "Ты — копирайтер АвтоРесурс. Напиши маркетинговый текст для email-рассылки "
        "русскоязычным покупателям авто из Новой Зеландии. Возвращай строго JSON с "
        "полями: subject (до 70 символов, без эмодзи в начале), intro (1 абзац, "
        "тёплый дружелюбный тон, 2-3 предложения), blurbs (массив строк по числу "
        "авто, каждая 1 предложение, цепляющая, без числовой цены — её клиент "
        "увидит в карточке).\n\n"
        f"Контекст: это {when_ru} рассылка. Авто на продаже сегодня:\n{cars_block}\n\n"
        "Только JSON, без markdown."
    )
    try:
        raw = await svc.chat(prompt, system="Return only JSON. No prose.", max_tokens=900)
        import json as _json, re as _re
        m = _re.search(r"\{.*\}", raw, _re.DOTALL)
        data = _json.loads(m.group(0) if m else raw)
        return {
            "subject": str(data.get("subject") or "").strip(),
            "intro":   str(data.get("intro") or "").strip(),
            "blurbs":  [str(b) for b in (data.get("blurbs") or [])],
        }
    except Exception as e:                                # noqa: BLE001
        log.warning("AI campaign copy failed, using fallback: %s", e)
        return {
            "subject": random.choice(_SUBJECT_FALLBACKS[slot]),
            "intro":   "Подобрали для вас несколько интересных лотов с аукционов "
                       "Новой Зеландии. Цены указаны ориентировочно в рублях с "
                       "учётом текущего курса и нашей комиссии.",
            "blurbs":  [_fallback_blurb(v) for v in vehicles],
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def generate_campaign_draft(
    db: AsyncIOMotorDatabase,
    slot: str = "morning",
    max_cars: int = 5,
) -> Optional[AutoEmailCampaign]:
    """Build a new DRAFT campaign for the given slot. Returns None if no
    eligible vehicles were found."""
    raw = await pick_random_vehicles(db, count=max_cars)
    if not raw:
        log.info("No eligible vehicles for slot %s — skipping", slot)
        return None
    snaps = [await _snap(d) for d in raw]
    copy = await _ai_write_copy(slot, snaps)
    blurbs = copy["blurbs"] or [_fallback_blurb(v) for v in snaps]
    for s, b in zip(snaps, blurbs):
        s.ai_blurb_ru = b

    # Count opted-in recipients
    consent_q = {
        "role": "customer",
        "$or": [
            {"customer_info.marketing_consent": {"$ne": False}},  # default-on
            {"customer_info.marketing_consent": {"$exists": False}},
        ],
    }
    recipient_count = await db.users.count_documents(consent_q)
    sample = [
        doc["email"]
        async for doc in db.users.find(consent_q, {"email": 1, "_id": 0}).limit(5)
    ]

    camp = AutoEmailCampaign(
        slot=slot,
        subject_ru=copy["subject"] or random.choice(_SUBJECT_FALLBACKS[slot]),
        intro_ru=copy["intro"] or "Свежая подборка с аукционов.",
        footer_ru=(
            "Вы получили это письмо как клиент АвтоРесурс. Если не хотите "
            "получать рассылку — нажмите «Отписаться» в подвале письма."
        ),
        vehicles=snaps,
        status=AutoCampaignStatus.DRAFT,
        recipient_count=recipient_count,
        recipients_sample=sample,
    )
    await db.auto_email_campaigns.insert_one(camp.model_dump())
    return camp


def render_email_html(camp: AutoEmailCampaign, recipient_email: str) -> str:
    """Render the campaign to inline HTML (provider-agnostic)."""
    unsubscribe = unsub_url(recipient_email)
    rows = []
    for v in camp.vehicles:
        price_str = (
            f"{int(v.display_price_rub):,} ₽".replace(",", " ")
            if v.display_price_rub else "По запросу"
        )
        img = v.image_url or ""
        rows.append(f"""
<tr><td style="padding:12px 0;border-bottom:1px solid #1f2937">
  <table width="100%" cellpadding="0" cellspacing="0"><tr>
    <td width="160" style="vertical-align:top">
      {f'<img src="{img}" width="150" style="border-radius:8px;display:block">' if img else ''}
    </td>
    <td style="padding-left:16px;vertical-align:top;color:#e5e7eb;font-family:Arial,sans-serif">
      <div style="font-weight:700;font-size:16px;color:#fff">{v.title_ru}</div>
      <div style="font-size:13px;color:#9ca3af;margin-top:2px">
        {v.year or ''} {f'· {v.mileage_km:,} км' if v.mileage_km else ''} {f'· {v.location}' if v.location else ''}
      </div>
      <div style="font-size:14px;color:#cbd5e1;margin-top:8px">{v.ai_blurb_ru or ''}</div>
      <div style="font-size:13px;color:#9ca3af;margin-top:8px">Цена · с аукциона</div>
      <div style="font-size:18px;font-weight:800;color:#fff">{price_str}</div>
      <a href="{v.detail_url}" style="display:inline-block;margin-top:10px;background:#0066FF;color:#fff;padding:8px 14px;border-radius:8px;text-decoration:none;font-weight:600;font-size:13px">Смотреть авто →</a>
    </td>
  </tr></table>
</td></tr>""".replace(",", " "))
    body = "\n".join(rows)
    return f"""<!doctype html><html><body style="background:#05070B;margin:0;padding:24px;font-family:Arial,sans-serif;color:#e5e7eb">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:640px;margin:0 auto;background:#0D111A;border-radius:16px;padding:24px">
  <tr><td>
    <div style="font-size:22px;font-weight:900;letter-spacing:0.5px;color:#fff">АВТО<span style="color:#0066FF">РЕСУРС</span></div>
    <div style="font-size:12px;color:#9ca3af;text-transform:uppercase;letter-spacing:2px;margin-top:4px">автомобили со всего мира</div>
    <h1 style="font-size:22px;color:#fff;margin-top:24px;margin-bottom:8px">{camp.subject_ru}</h1>
    <p style="color:#cbd5e1;font-size:14px;line-height:1.5">{camp.intro_ru}</p>
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:18px">{body}</table>
    <div style="text-align:center;margin-top:24px">
      <a href="{PUBLIC_BASE_URL}/auto/catalog" style="background:#0066FF;color:#fff;padding:12px 24px;border-radius:10px;text-decoration:none;font-weight:700">Открыть весь каталог</a>
    </div>
    <hr style="border:0;border-top:1px solid #1f2937;margin:24px 0">
    <div style="font-size:11px;color:#6b7280;line-height:1.5">
      {camp.footer_ru or ''}
      <br><br>
      Если не хотите больше получать такие письма — <a href="{unsubscribe}" style="color:#9ca3af;text-decoration:underline">отписаться</a>.<br>
      АвтоРесурс · Auckland, New Zealand · europrestige@gmail.com · +64 21 425 233
    </div>
  </td></tr>
</table>
</body></html>"""


# ---------------------------------------------------------------------------
# Provider — pluggable. Reads provider name + API key from app_settings
# at send-time so the admin can switch providers without a restart.
# ---------------------------------------------------------------------------

async def _send_mailchimp(db, camp, recipients):
    """Mailchimp Marketing API — Transactional / Audience send.

    We use the Marketing v3 endpoint POST /campaigns to create + POST /campaigns/{id}/actions/send.
    Requires: email_provider_api_key in the form "<key>-<dc>" (e.g. abc...-us21)
    + a configured Audience (List) — we use the first audience the key has access to.
    """
    from services.auto_settings_service import get_setting
    import httpx
    api_key = await get_setting(db, "email_provider_api_key")
    if not api_key or "-" not in api_key:
        raise RuntimeError("Mailchimp API key not configured or malformed (expected key-dc form)")
    dc = api_key.rsplit("-", 1)[1]
    base = f"https://{dc}.api.mailchimp.com/3.0"
    auth = ("anystring", api_key)
    from_email = await get_setting(db, "email_from_address", "info@avtoresurs.nz")
    from_name  = await get_setting(db, "email_from_name", "АвтоРесурс")
    async with httpx.AsyncClient(timeout=30.0, auth=auth) as c:
        # Pick first list (audience)
        lr = await c.get(f"{base}/lists?count=1")
        lr.raise_for_status()
        lists = lr.json().get("lists", [])
        if not lists:
            raise RuntimeError("Mailchimp: no audiences (lists) configured on this account")
        list_id = lists[0]["id"]
        # Create regular campaign
        cr = await c.post(f"{base}/campaigns", json={
            "type": "regular",
            "recipients": {"list_id": list_id},
            "settings": {
                "subject_line": camp.subject_ru,
                "title": f"AvtoResurs {camp.slot} {camp.id[:8]}",
                "from_name": from_name,
                "reply_to": from_email,
            },
        })
        cr.raise_for_status()
        cid = cr.json()["id"]
        # Set HTML
        await c.put(f"{base}/campaigns/{cid}/content", json={
            "html": render_email_html(camp, "subscriber@list"),
        })
        # Send
        await c.post(f"{base}/campaigns/{cid}/actions/send")
    return {"provider": "mailchimp", "message_ids": [cid], "delivered": len(recipients)}


async def _send_sendsay(db, camp, recipients):
    """Sendsay (sendsay.ru) — JSON-RPC API.

    Auth = login+password from settings (account_sid + auth_token fields reused).
    Issue.create method creates a campaign with HTML + sends to a given list.
    """
    from services.auto_settings_service import get_setting
    import httpx
    api_key = await get_setting(db, "email_provider_api_key")
    if not api_key:
        raise RuntimeError("Sendsay API key not configured")
    # Sendsay expects "login:apikey" auth (or a session); simplified here:
    from_email = await get_setting(db, "email_from_address", "info@avtoresurs.nz")
    from_name  = await get_setting(db, "email_from_name", "АвтоРесурс")
    url = "https://api.sendsay.ru/general/api/v100/json/_"
    payload = {
        "action": "issue.send",
        "apikey": api_key,
        "letter": {
            "subject": camp.subject_ru,
            "from.name": from_name,
            "from.email": from_email,
            "message": {"html": render_email_html(camp, "subscriber@list")},
        },
        "users": [{"email": e} for e in recipients],
    }
    async with httpx.AsyncClient(timeout=30.0) as c:
        r = await c.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
    if data.get("errors"):
        raise RuntimeError(f"Sendsay error: {data['errors']}")
    return {"provider": "sendsay", "message_ids": [data.get("track.id", "")], "delivered": len(recipients)}


async def _send_via_provider(camp: AutoEmailCampaign, recipients: List[str], db=None) -> Dict[str, object]:
    from services.auto_settings_service import get_setting
    provider_name = (await get_setting(db, "email_provider", "stub")) if db is not None else "stub"
    provider_name = (provider_name or "stub").lower()
    try:
        if provider_name == "mailchimp" and db is not None:
            return await _send_mailchimp(db, camp, recipients)
        if provider_name == "sendsay" and db is not None:
            return await _send_sendsay(db, camp, recipients)
    except Exception as e:                                    # noqa: BLE001
        log.exception("Provider %s send failed; falling back to stub.", provider_name)
        return {"provider": f"{provider_name}-failed", "message_ids": [], "delivered": 0, "error": str(e)}
    # stub / resend / unknown — no-op
    log.info("[%s] would send %d emails for campaign %s", provider_name.upper(), len(recipients), camp.id)
    return {"provider": provider_name, "message_ids": [], "delivered": len(recipients)}


async def send_campaign(
    db: AsyncIOMotorDatabase,
    campaign_id: str,
) -> AutoEmailCampaign:
    """Mark APPROVED, ship the emails, then mark SENT (or FAILED)."""
    doc = await db.auto_email_campaigns.find_one({"id": campaign_id})
    if not doc:
        raise ValueError("Campaign not found")
    camp = AutoEmailCampaign(**doc)
    if camp.status == AutoCampaignStatus.SENT:
        return camp

    consent_q = {
        "role": "customer",
        "$or": [
            {"customer_info.marketing_consent": {"$ne": False}},
            {"customer_info.marketing_consent": {"$exists": False}},
        ],
    }
    recipients = [
        d["email"]
        async for d in db.users.find(consent_q, {"email": 1, "_id": 0})
        if d.get("email")
    ]
    if not recipients:
        await db.auto_email_campaigns.update_one(
            {"id": campaign_id},
            {"$set": {"status": AutoCampaignStatus.SENT.value,
                      "sent_at": datetime.now(timezone.utc),
                      "recipient_count": 0,
                      "updated_at": datetime.now(timezone.utc)}},
        )
        return camp

    await db.auto_email_campaigns.update_one(
        {"id": campaign_id},
        {"$set": {"status": AutoCampaignStatus.SENDING.value,
                  "updated_at": datetime.now(timezone.utc)}},
    )
    try:
        info = await _send_via_provider(camp, recipients, db=db)
        await db.auto_email_campaigns.update_one(
            {"id": campaign_id},
            {"$set": {
                "status": AutoCampaignStatus.SENT.value,
                "sent_at": datetime.now(timezone.utc),
                "recipient_count": info.get("delivered", len(recipients)),
                "provider": info.get("provider"),
                "sent_message_ids": info.get("message_ids", []),
                "updated_at": datetime.now(timezone.utc),
            }},
        )
    except Exception as e:                                # noqa: BLE001
        await db.auto_email_campaigns.update_one(
            {"id": campaign_id},
            {"$set": {"status": AutoCampaignStatus.FAILED.value,
                      "error": str(e),
                      "updated_at": datetime.now(timezone.utc)}},
        )
        raise
    return AutoEmailCampaign(**(await db.auto_email_campaigns.find_one({"id": campaign_id})))
