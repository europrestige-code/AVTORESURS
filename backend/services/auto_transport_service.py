"""
АвтоРесурс — transport cost engine for NZ branches.

The auction lot ships from a Turners/Manheim/Pickles branch (e.g. Dunedin)
to the export container port in Auckland. The cost depends on:
  • branch / city of the lot,
  • whether the vehicle is a runner (drives) or non-runner (must be towed),
  • per-job surcharges (forklift, etc.) handled elsewhere.

Pricing baseline: PTS Vehicle Logistics / Conroy-style NZ rates per
operator specification (2026):
    Auckland / immediate suburbs ... NZ$0
    ~1 hour from Auckland ......... NZ$250  (Hamilton, Whangarei)
    ~6 hours from Auckland ........ NZ$750  (Palmerston North area)
    Wellington → Auckland ......... NZ$790
    Christchurch (incl. ferry) .... NZ$1,100
    further South Island adds ~NZ$200 per leg.

NON-RUNNER rule (per product spec):
    cost_non_runner = 2 × cost_runner
"""

from __future__ import annotations

from typing import Dict, Optional

# Base "runner" delivery cost to Auckland port (NZD).
# Calibrated to PTS-style pricing as of 2026.
RUNNER_TRANSPORT_NZD: Dict[str, float] = {
    # Auckland & immediate suburbs (already at port)
    "auckland": 0.0,
    "otahuhu": 0.0,
    "north shore": 0.0,
    "westgate": 0.0,
    "botany": 0.0,
    "manukau": 0.0,
    "penrose": 0.0,
    "penrose - great south road": 0.0,
    "manukau city": 0.0,

    # Northland (~2h)
    "whangarei": 300.0,

    # Waikato (~1.5h)
    "hamilton": 250.0,
    "avalon drive": 250.0,
    "te rapa road": 250.0,
    "hamilton avalon cars": 250.0,

    # Bay of Plenty (~3h)
    "tauranga": 400.0,
    "rotorua": 450.0,

    # Hawke's Bay (~5h)
    "napier": 650.0,
    "hastings": 660.0,

    # Taranaki (~4.5h)
    "new plymouth": 600.0,

    # Manawatu (~7h)
    "palmerston north": 750.0,

    # Wellington (~8h, ferry-staging hub)
    "porirua": 770.0,
    "wellington": 790.0,
    "wellington - porirua": 770.0,

    # Top of South Island (Wellington + ferry)
    "nelson": 1050.0,
    "blenheim": 1090.0,

    # Canterbury (incl. ferry crossing)
    "christchurch": 1100.0,
    "hornby": 1100.0,
    "moorhouse ave": 1100.0,
    "wairakei rd": 1100.0,
    "wairakei road": 1100.0,
    "timaru": 1250.0,

    # Otago / Southland
    "dunedin": 1450.0,
    "invercargill": 1700.0,
    "queenstown": 1550.0,
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
