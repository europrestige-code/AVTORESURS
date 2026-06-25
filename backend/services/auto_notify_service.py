"""Email + Telegram notifications for the АвтоРесурс platform.

Both transports are best-effort and never raise – the saved-search runner
needs to keep iterating even if a single delivery fails.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

_RESEND_KEY = os.environ.get("RESEND_API_KEY")
_SENDER = os.environ.get("SENDER_EMAIL") or "onboarding@resend.dev"
_TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
_FX_FALLBACK = 57.68


def _fmt_rub(nzd: Optional[float], rate: float) -> str:
    if not nzd or nzd <= 0:
        return "—"
    rub = round(nzd * rate)
    return f"{rub:,}".replace(",", " ") + " ₽"


def _format_email_html(
    user_name: str,
    search_name: str,
    matches: List[Dict[str, Any]],
    fx_rate: float,
    public_url: str,
) -> str:
    """Build a self-contained, table-based HTML email (no external CSS)."""
    cards_html: List[str] = []
    for v in matches[:8]:
        price_rub = _fmt_rub(v.get("current_price_nzd"), fx_rate)
        price_nzd = (
            f"NZ${int(v.get('current_price_nzd') or 0):,}"
            if v.get("current_price_nzd") else ""
        )
        img = v.get("image") or ""
        title = v.get("title_ru") or v.get("title") or "—"
        link = f"{public_url}/auto/vehicle/{v.get('id')}"
        cards_html.append(f"""
<table width="100%" cellpadding="0" cellspacing="0" style="background:#111;border-radius:12px;margin-bottom:14px;border:1px solid #222;">
  <tr>
    <td width="160" style="padding:14px;vertical-align:top;">
      {'<img src="' + img + '" width="140" style="border-radius:8px;display:block;" />' if img else ''}
    </td>
    <td style="padding:14px 14px 14px 0;color:#fff;font-family:Arial,sans-serif;vertical-align:top;">
      <div style="font-size:16px;font-weight:bold;line-height:1.3;margin-bottom:6px;">
        <a href="{link}" style="color:#3a86ff;text-decoration:none;">{title}</a>
      </div>
      <div style="font-size:13px;color:#aaa;margin-bottom:8px;">
        {v.get('year') or ''} · {v.get('country') or ''}
        {(' · ' + str(round((v.get('mileage_km') or 0)/1000)) + ' тыс. км') if v.get('mileage_km') else ''}
      </div>
      <div style="font-size:18px;font-weight:bold;color:#fff;">{price_rub}</div>
      <div style="font-size:11px;color:#888;">{price_nzd}</div>
      <a href="{link}" style="display:inline-block;margin-top:10px;background:#3a86ff;color:#fff;padding:8px 14px;border-radius:8px;text-decoration:none;font-size:13px;font-weight:bold;">Открыть</a>
    </td>
  </tr>
</table>""")

    return f"""
<!doctype html>
<html><body style="margin:0;padding:0;background:#000;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#000;">
  <tr><td align="center" style="padding:20px;">
    <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;">
      <tr><td style="padding-bottom:18px;">
        <div style="color:#3a86ff;font-size:13px;font-weight:bold;letter-spacing:0.08em;text-transform:uppercase;">АвтоРесурс · подписка</div>
        <div style="color:#fff;font-size:22px;font-weight:bold;margin-top:4px;">Новые авто по подписке «{search_name}»</div>
        <div style="color:#888;font-size:13px;margin-top:6px;">Привет, {user_name}! Мы нашли {len(matches)} {('авто' if len(matches)==1 else 'авто, подходящих под')} ваш сохранённый поиск. Откройте, чтобы посмотреть подробности.</div>
      </td></tr>
      <tr><td>{''.join(cards_html)}</td></tr>
      <tr><td style="padding-top:14px;color:#666;font-size:11px;line-height:1.5;">
        Цены в ₽ рассчитаны по курсу {fx_rate:.2f} ₽/NZ$ (с учётом нашей надбавки 3%).
        Чтобы отписаться или изменить параметры — войдите на сайте → «Мои подписки».
      </td></tr>
    </table>
  </td></tr>
</table>
</body></html>"""


async def send_email(
    to: str,
    subject: str,
    html: str,
) -> Dict[str, Any]:
    """Send a single transactional email via Resend (best-effort)."""
    if not _RESEND_KEY:
        logger.warning("RESEND_API_KEY not configured — email skipped")
        return {"status": "skipped", "reason": "no_key"}
    import resend
    resend.api_key = _RESEND_KEY
    params = {"from": _SENDER, "to": [to], "subject": subject, "html": html}
    try:
        result = await asyncio.to_thread(resend.Emails.send, params)
        return {"status": "sent", "id": (result or {}).get("id")}
    except Exception as e:
        logger.warning(f"Resend send failed for {to}: {e}")
        return {"status": "error", "error": str(e)[:200]}


async def send_telegram_message(
    chat_id: int,
    text: str,
    parse_mode: str = "HTML",
    disable_preview: bool = False,
) -> Dict[str, Any]:
    if not _TG_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not configured — message skipped")
        return {"status": "skipped"}
    url = f"https://api.telegram.org/bot{_TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_preview,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(url, json=payload)
        return {"status": "sent" if r.status_code == 200 else "error", "raw": r.json()}
    except Exception as e:
        logger.warning(f"Telegram sendMessage failed: {e}")
        return {"status": "error", "error": str(e)[:200]}


async def send_telegram_photo(
    chat_id: int,
    photo: str,
    caption: str,
    parse_mode: str = "HTML",
) -> Dict[str, Any]:
    if not _TG_TOKEN:
        return {"status": "skipped"}
    url = f"https://api.telegram.org/bot{_TG_TOKEN}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": photo,
        "caption": caption[:1024],
        "parse_mode": parse_mode,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(url, json=payload)
        return {"status": "sent" if r.status_code == 200 else "error", "raw": r.json()}
    except Exception as e:
        logger.warning(f"Telegram sendPhoto failed: {e}")
        return {"status": "error", "error": str(e)[:200]}


def format_telegram_match(
    v: Dict[str, Any], fx_rate: float, public_url: str
) -> str:
    price_rub = _fmt_rub(v.get("current_price_nzd"), fx_rate)
    title = v.get("title_ru") or v.get("title") or "—"
    link = f"{public_url}/auto/vehicle/{v.get('id')}"
    extra = []
    if v.get("year"):
        extra.append(str(v["year"]))
    if v.get("country"):
        extra.append(v["country"])
    if v.get("mileage_km"):
        extra.append(f"{round(v['mileage_km']/1000)} тыс. км")
    meta = " · ".join(extra)
    return (
        f"<b>{title}</b>\n"
        f"{meta}\n"
        f"<b>{price_rub}</b>"
        + (f" (NZ${int(v['current_price_nzd']):,})" if v.get("current_price_nzd") else "")
        + f"\n<a href=\"{link}\">Открыть лот</a>"
    )


async def deliver_match_batch(
    *,
    user_name: str,
    search_name: str,
    matches: List[Dict[str, Any]],
    fx_rate: float,
    email: Optional[str],
    telegram_chat_id: Optional[int],
    public_url: str,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {"email": None, "telegram": None}
    if not matches:
        return out
    if email:
        html = _format_email_html(user_name, search_name, matches, fx_rate, public_url)
        subj = f"АвтоРесурс — {len(matches)} новых авто по подписке «{search_name}»"
        out["email"] = await send_email(email, subj, html)
    if telegram_chat_id:
        head = (
            f"🚗 <b>{len(matches)} новых авто</b> по подписке «{search_name}»\n"
            f"Открой, чтобы посмотреть детали."
        )
        out["telegram"] = await send_telegram_message(
            telegram_chat_id, head, disable_preview=True
        )
        # Send up to 5 detailed cards
        for v in matches[:5]:
            caption = format_telegram_match(v, fx_rate, public_url)
            img = v.get("image")
            if img and img.startswith("http"):
                await send_telegram_photo(telegram_chat_id, img, caption)
            else:
                await send_telegram_message(telegram_chat_id, caption, disable_preview=False)
    return out
