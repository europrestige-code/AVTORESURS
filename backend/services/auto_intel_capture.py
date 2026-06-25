"""Buyer-session capture harness.

Logs into Turners / Manheim / Pickles using saved credentials and crawls the
buyer-visible inventory + post-auction results. Captured rows are stored in
`auction_observations` for the AI estimator to learn from.

THIS FILE IS THE FRAMEWORK. The per-source DOM selectors and live-Simulcast
websocket parsers are platform-specific and are stubbed out below with clear
TODO markers — they require a dedicated dev session per source because the
HTML and WS payloads change.

Usage (admin endpoint or scheduler):
    from services.auto_intel_capture import capture_for_source
    await capture_for_source(db, "turners")
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from models.auto_credentials import decrypt
from models.auto_intelligence import AuctionObservation

LOGIN_URL = {
    "turners":    "https://www.turners.co.nz/Login",
    "manheim_nz": "https://www.manheim.co.nz/login",
    "manheim_au": "https://www.manheim.com.au/login",
    "pickles":    "https://www.pickles.com.au/login",
}


async def _load_credential(db, source: str) -> Optional[Dict[str, str]]:
    row = await db.auto_source_credentials.find_one({"source": source, "enabled": True})
    if not row:
        return None
    plain = decrypt(row.get("password_encrypted", ""))
    if not plain:
        return None
    return {
        "username": row["username"],
        "password": plain,
        "row_id": row["id"],
    }


async def _record_status(db, source: str, status: str, error: Optional[str] = None) -> None:
    await db.auto_source_credentials.update_one(
        {"source": source},
        {"$set": {
            "last_login_at": datetime.now(timezone.utc),
            "last_status": status,
            "last_error": error,
        }},
    )


async def capture_for_source(db, source: str, *, limit: int = 200) -> Dict[str, Any]:
    """Top-level driver. Returns a summary dict.

    Per-source implementations live in the TODO blocks below. Each must:
      1. Launch Playwright Chromium.
      2. Authenticate using `cred["username"] / cred["password"]`.
      3. Persist cookies so subsequent runs can skip the login flow.
      4. Visit the buyer-listings + post-results pages and yield observation
         dicts that are written to `auction_observations`.
    """
    cred = await _load_credential(db, source)
    if not cred:
        return {"source": source, "ok": False, "error": "no_credentials"}

    try:
        # Lazy import — Playwright is heavy and shouldn't block service start.
        from playwright.async_api import async_playwright
    except ImportError:
        return {
            "source": source,
            "ok": False,
            "error": "playwright_not_installed",
            "hint": "pip install playwright && playwright install chromium",
        }

    captured = 0
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120 Safari/537.36"
            ),
        )
        page = await ctx.new_page()
        try:
            # 1. LOGIN — every source has a different form. The structure is
            #    deliberately verbose so future devs can swap selectors quickly.
            login_ok = await _login(page, source, cred)
            if not login_ok:
                await _record_status(db, source, "login_failed", "selector mismatch or captcha")
                return {"source": source, "ok": False, "error": "login_failed"}

            # 2. CRAWL — fan out to listing + results URLs.
            observations = await _crawl(page, source, limit=limit)

            # 3. STORE.
            for obs in observations:
                doc = AuctionObservation(source=source, **obs).model_dump()
                await db.auction_observations.insert_one(doc)
                captured += 1

            await _record_status(db, source, "ok", None)
            return {"source": source, "ok": True, "captured": captured}
        except Exception as e:
            await _record_status(db, source, "error", str(e)[:300])
            return {"source": source, "ok": False, "error": str(e)[:300]}
        finally:
            await ctx.close()
            await browser.close()


# ---------------------------------------------------------------------------
# Per-source login (PLATFORM-SPECIFIC TODOs)
# ---------------------------------------------------------------------------
async def _login(page, source: str, cred: Dict[str, str]) -> bool:
    url = LOGIN_URL.get(source)
    if not url:
        return False
    await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

    # Common attempt: input[name=username] / input[name=password].
    # Each source has its own real selectors — replace these defaults during
    # the per-source integration sprint.
    try:
        await page.fill("input[name='username'], input[type='email'], #username, #email", cred["username"], timeout=10_000)
        await page.fill("input[name='password'], input[type='password'], #password", cred["password"], timeout=10_000)
        await page.click("button[type='submit'], button:has-text('Login'), button:has-text('Sign in')")
        await page.wait_for_load_state("networkidle", timeout=15_000)
        # Heuristic — if the URL still contains /login, the form failed.
        return "/login" not in page.url.lower()
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Per-source crawl (PLATFORM-SPECIFIC TODOs)
# ---------------------------------------------------------------------------
async def _crawl(page, source: str, *, limit: int) -> list:
    """Returns a list of dicts compatible with AuctionObservation fields.

    The DOM structure differs per source. Below is a generic skeleton that
    extracts every visible auction row and best-guesses common fields. The
    *per-source* integration replaces this with deterministic selectors and
    drives the live Simulcast websocket (Turners: live.turners.co.nz,
    Manheim: simulcast.manheim.co.nz).
    """
    # NB: The default crawl returns an empty list rather than wrong data —
    # that's intentional. Phase 2 lands per-source selectors here.
    return []
