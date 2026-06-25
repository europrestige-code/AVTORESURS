"""Payment-terms rules for АвтоРесурс.

Central place for the business policy that the user dictated:

1. Winning bidders must remit the **full balance within 24 hours** of the
   hammer drop, otherwise the win is forfeited and the deposit is held.
2. To bid on lots with a current price (or AI-estimated recommended bid)
   **above NZ$10,000** the user must deposit **30% of that price**, instead
   of the flat NZ$1,000 floor used for cheaper lots.

These constants are used both server-side (validating deposit + bid) and
exposed via `/api/auto/payment-terms` so the frontend can render a single
source-of-truth disclosure block on the vehicle page, bid modal, etc.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

# ----- Tunable knobs (could move to settings later) -----
BASE_DEPOSIT_NZD: float = 1000.0
TIER1_THRESHOLD_NZD: float = 20000.0   # > $20K  -> 20%
TIER1_PERCENT: float = 20.0
TIER2_THRESHOLD_NZD: float = 40000.0   # > $40K  -> 30%
TIER2_PERCENT: float = 30.0
FULL_PAYMENT_WINDOW_HOURS: int = 24
PAYMENT_TERMS_VERSION = "v2026.06.25.2"


def reference_price_nzd(vehicle: Optional[Dict[str, Any]]) -> float:
    """Pick the price we evaluate the «expensive» threshold against.

    Preference order:
      1. `current_price_nzd` if > 0 (live auction price)
      2. AI estimate `recommended_max_bid_nzd`
      3. `starting_price_nzd`
      4. 0
    """
    if not vehicle:
        return 0.0
    cur = float(vehicle.get("current_price_nzd") or 0)
    if cur > 0:
        return cur
    ai = (vehicle.get("ai_estimate") or {}).get("recommended_max_bid_nzd")
    if ai and float(ai) > 0:
        return float(ai)
    start = float(vehicle.get("starting_price_nzd") or 0)
    return max(start, 0.0)


def required_deposit_nzd(vehicle: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return the deposit required to bid on this vehicle along with a
    breakdown so the frontend can explain the number to the user.

    Tiered rules:
      • price ≤ NZ$20,000 → flat NZ$1,000 base deposit
      • NZ$20,000 < price ≤ NZ$40,000 → 20% of the reference price
      • price > NZ$40,000 → 30% of the reference price
    """
    price = reference_price_nzd(vehicle)
    if price > TIER2_THRESHOLD_NZD:
        amount = round(price * TIER2_PERCENT / 100.0, 2)
        return {
            "amount_nzd": amount,
            "is_percent": True,
            "tier": "tier2",
            "percent": TIER2_PERCENT,
            "reference_price_nzd": price,
            "threshold_nzd": TIER2_THRESHOLD_NZD,
            "explanation": (
                f"Премиум-лот (свыше NZ${int(TIER2_THRESHOLD_NZD):,}) — "
                f"депозит {int(TIER2_PERCENT)}% от цены = NZ${amount:,.0f}."
            ),
        }
    if price > TIER1_THRESHOLD_NZD:
        amount = round(price * TIER1_PERCENT / 100.0, 2)
        return {
            "amount_nzd": amount,
            "is_percent": True,
            "tier": "tier1",
            "percent": TIER1_PERCENT,
            "reference_price_nzd": price,
            "threshold_nzd": TIER1_THRESHOLD_NZD,
            "explanation": (
                f"Лот дороже NZ${int(TIER1_THRESHOLD_NZD):,} — "
                f"депозит {int(TIER1_PERCENT)}% от цены = NZ${amount:,.0f}."
            ),
        }
    return {
        "amount_nzd": BASE_DEPOSIT_NZD,
        "is_percent": False,
        "tier": "base",
        "percent": None,
        "reference_price_nzd": price,
        "threshold_nzd": TIER1_THRESHOLD_NZD,
        "explanation": (
            f"Базовый депозит NZ${int(BASE_DEPOSIT_NZD):,} (лот до "
            f"NZ${int(TIER1_THRESHOLD_NZD):,})."
        ),
    }


def payment_terms_summary() -> Dict[str, Any]:
    """JSON snapshot of the payment policy used by `/api/auto/payment-terms`
    and the frontend disclosure component."""
    return {
        "version": PAYMENT_TERMS_VERSION,
        "base_deposit_nzd": BASE_DEPOSIT_NZD,
        "tier1_threshold_nzd": TIER1_THRESHOLD_NZD,
        "tier1_percent": TIER1_PERCENT,
        "tier2_threshold_nzd": TIER2_THRESHOLD_NZD,
        "tier2_percent": TIER2_PERCENT,
        "full_payment_window_hours": FULL_PAYMENT_WINDOW_HOURS,
        "bullets_ru": [
            f"Базовый депозит для участия в торгах — NZ${int(BASE_DEPOSIT_NZD):,} (для лотов до NZ${int(TIER1_THRESHOLD_NZD):,}).",
            (
                f"Для лотов от NZ${int(TIER1_THRESHOLD_NZD):,} до NZ${int(TIER2_THRESHOLD_NZD):,} "
                f"требуется депозит {int(TIER1_PERCENT)}% от текущей цены."
            ),
            (
                f"Для премиум-лотов свыше NZ${int(TIER2_THRESHOLD_NZD):,} требуется депозит "
                f"{int(TIER2_PERCENT)}% от текущей цены."
            ),
            (
                f"После выигрыша ставки полная сумма должна поступить в течение "
                f"{FULL_PAYMENT_WINDOW_HOURS} часов, иначе лот возвращается на "
                f"аукцион, а депозит удерживается."
            ),
            "Все суммы — в NZ$. Конвертация в ₽ по курсу на момент оплаты + 3% (включает банковский спред).",
        ],
    }
