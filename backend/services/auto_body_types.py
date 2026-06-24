"""Canonical body-type taxonomy used by the public catalog filter strip.

Vehicles arrive from many sources (Turners EN, Manheim AU/EN, Pickles, manual
Russian entry, AI-translation) so the same body shape ends up stored under
multiple names: "Sedan", "Седан", "Saloon", "4dr". We collapse these into a
single canonical English key per shape and a stable display order.

Each entry exposes:
  key      — canonical lowercase id used in URL params (?body_type=sedan)
  label_ru — Russian label shown in the UI
  aliases  — list of case-insensitive substrings; if ANY appears in the stored
             body_type the vehicle counts towards this canonical type
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

import re

# Ordered to mirror the Turners-style strip the user requested.
BODY_TYPES: List[Dict[str, Any]] = [
    {
        "key": "convertible",
        "label_ru": "Кабриолет",
        "label_en": "Convertible",
        "aliases": ["convertible", "cabriolet", "roadster", "spider", "spyder",
                    "кабриолет", "родстер"],
    },
    {
        "key": "wagon",
        "label_ru": "Универсал",
        "label_en": "Wagon",
        "aliases": ["wagon", "estate", "tourer", "touring", "kombi",
                    "универсал"],
    },
    {
        "key": "utility",
        "label_ru": "Пикап",
        "label_en": "Utility",
        "aliases": ["utility", "ute", "pickup", "pick-up", "pick up", "truck",
                    "пикап", "грузовик"],
    },
    {
        "key": "coupe",
        "label_ru": "Купе",
        "label_en": "Coupe",
        "aliases": ["coupe", "coupé", "2dr", "2-door", "купе"],
    },
    {
        "key": "hatchback",
        "label_ru": "Хэтчбек",
        "label_en": "Hatchback",
        "aliases": ["hatchback", "hatch", "5dr", "3dr", "liftback",
                    "хэтчбек", "хетчбек", "лифтбек"],
    },
    {
        "key": "van",
        "label_ru": "Фургон",
        "label_en": "Van",
        "aliases": ["van", "minivan", "mpv", "people mover", "panel",
                    "фургон", "минивэн", "минивен"],
    },
    {
        "key": "sedan",
        "label_ru": "Седан",
        "label_en": "Sedan",
        "aliases": ["sedan", "saloon", "4dr", "4-door", "седан"],
    },
    {
        "key": "suv",
        "label_ru": "Внедорожник",
        "label_en": "SUV",
        "aliases": ["suv", "4wd", "4x4", "crossover", "off-road", "offroad",
                    "внедорожник", "кроссовер", "джип"],
    },
]


BY_KEY: Dict[str, Dict[str, Any]] = {b["key"]: b for b in BODY_TYPES}


def regex_for_key(key: str) -> Optional[str]:
    """Return a case-insensitive regex matching ANY alias for the given key."""
    b = BY_KEY.get(key.lower())
    if not b:
        return None
    parts = [re.escape(a) for a in b["aliases"]]
    return "(" + "|".join(parts) + ")"


def mongo_filter_for_key(key: str) -> Optional[Dict[str, Any]]:
    """Mongo $regex clause matching the stored body_type to a canonical key."""
    pattern = regex_for_key(key)
    if not pattern:
        return None
    return {"$regex": pattern, "$options": "i"}


async def counts_by_canonical(db) -> List[Dict[str, Any]]:
    """Return [{key, label_ru, label_en, count}, ...] in canonical order."""
    out: List[Dict[str, Any]] = []
    base = {"status": {"$ne": "hidden"}}
    for b in BODY_TYPES:
        flt = dict(base)
        flt["body_type"] = mongo_filter_for_key(b["key"]) or {"$exists": False}
        cnt = await db.auto_vehicles.count_documents(flt)
        out.append({
            "key": b["key"],
            "label_ru": b["label_ru"],
            "label_en": b["label_en"],
            "count": cnt,
        })
    return out
