"""
АвтоРесурс — transport cost engine for NZ branches.

The auction lot ships from a Turners/Manheim/Pickles branch (e.g. Dunedin)
to the export container port in Auckland. The cost depends on:
  • branch / city of the lot,
  • whether the vehicle is a runner (drives) or non-runner (must be towed),
  • per-job surcharges (forklift, etc.) handled elsewhere.

Pricing baseline: indicative PTS Vehicle Logistics / Carstars-style NZ
transport rates as of 2026. Operators should periodically calibrate these
values; they are designed to be conservative for the client (slight
over-estimate) so the final invoice never surprises.

NON-RUNNER rule (per product spec):
  cost_non_runner = 2 × cost_runner

The default "local_transport_nzd" of NZ$500 in pricing.calculate_price_breakdown
is used only when no branch is known.
"""

from __future__ import annotations

from typing import Dict, Optional

# Base "runner" delivery cost to Auckland port (NZD).
# Auckland-area branches: $0 (already at the port).
RUNNER_TRANSPORT_NZD: Dict[str, float] = {
    # Auckland & immediate suburbs
    "auckland": 0.0,
    "otahuhu": 0.0,
    "north shore": 0.0,
    "westgate": 0.0,
    "botany": 0.0,
    "manukau": 0.0,
    "penrose": 0.0,
    "penrose - great south road": 0.0,
    "manukau city": 0.0,

    # Northland
    "whangarei": 220.0,

    # Waikato
    "hamilton": 220.0,
    "avalon drive": 220.0,
    "te rapa road": 220.0,
    "hamilton avalon cars": 220.0,

    # Bay of Plenty
    "tauranga": 280.0,
    "rotorua": 320.0,

    # Hawke's Bay
    "napier": 420.0,
    "hastings": 430.0,

    # Taranaki
    "new plymouth": 520.0,

    # Manawatu / Wellington
    "palmerston north": 540.0,
    "porirua": 650.0,
    "wellington": 680.0,
    "wellington - porirua": 650.0,

    # Top of South Island
    "nelson": 1050.0,
    "blenheim": 1100.0,

    # Canterbury
    "christchurch": 1250.0,
    "hornby": 1250.0,
    "moorhouse ave": 1250.0,
    "wairakei rd": 1250.0,
    "wairakei road": 1250.0,
    "timaru": 1450.0,

    # Otago / Southland
    "dunedin": 1650.0,
    "invercargill": 1950.0,
    "queenstown": 1800.0,
}


def _normalise(name: Optional[str]) -> str:
    return (name or "").strip().lower()


def transport_cost(branch_or_city: Optional[str], is_non_runner: bool = False) -> Dict[str, object]:
    """Return the indicative local-transport cost for a vehicle.

    Returns a dict so callers can show the breakdown to the customer:
        {
          "branch": "Wellington",
          "matched": True,
          "runner_nzd": 680.0,
          "is_non_runner": True,
          "multiplier": 2.0,
          "transport_nzd": 1360.0,
        }
    """
    n = _normalise(branch_or_city)
    runner = None
    if n:
        if n in RUNNER_TRANSPORT_NZD:
            runner = RUNNER_TRANSPORT_NZD[n]
        else:
            # Try a fuzzy contains match (e.g. "Porirua Cars" → "porirua")
            for key, value in RUNNER_TRANSPORT_NZD.items():
                if key in n or n in key:
                    runner = value
                    break
    matched = runner is not None
    if runner is None:
        runner = 500.0  # legacy default for unknown branches
    multiplier = 2.0 if is_non_runner else 1.0
    total = round(runner * multiplier, 2)
    return {
        "branch": branch_or_city or None,
        "matched": matched,
        "runner_nzd": round(runner, 2),
        "is_non_runner": bool(is_non_runner),
        "multiplier": multiplier,
        "transport_nzd": total,
    }


def list_branches() -> Dict[str, float]:
    """Public read-only copy of the pricing table for admin tooling."""
    return dict(RUNNER_TRANSPORT_NZD)
