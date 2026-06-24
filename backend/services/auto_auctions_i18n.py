"""Russian translations for the auction calendar.

Turners writes auction titles and branch names in English. We display them in
RU on the public calendar by rewriting strings server-side. Anything we don't
know is left untouched.
"""

from __future__ import annotations
import re
from typing import Any, Dict

# Branches that include "Cars" / "Avalon" / etc. are normalised down to
# their city in Russian. Keep keys lowercase for case-insensitive matching.
BRANCH_RU = {
    "whangarei": "Уонгареи",
    "north shore": "Норт-Шор",
    "westgate": "Уэстгейт",
    "otahuhu": "Отахуху",
    "manukau": "Манукау",
    "penrose": "Пенроуз",
    "botany": "Ботани",
    "avalon": "Гамильтон (Avalon Drive)",
    "te rapa": "Гамильтон (Te Rapa)",
    "hamilton": "Гамильтон",
    "tauranga": "Тауранга",
    "rotorua": "Роторуа",
    "napier": "Нэйпир",
    "new plymouth": "Нью-Плимут",
    "palmerston north": "Палмерстон-Норт",
    "porirua": "Порируа",
    "wellington": "Веллингтон",
    "nelson": "Нельсон",
    "blenheim": "Бленем",
    "hornby": "Крайстчёрч (Hornby)",
    "wairakei rd": "Крайстчёрч (Wairakei Rd)",
    "moorhouse ave": "Крайстчёрч (Moorhouse Ave)",
    "christchurch": "Крайстчёрч",
    "timaru": "Тимару",
    "dunedin": "Данидин",
    "invercargill": "Инверкаргилл",
}

CITY_RU = {
    "Whangarei": "Уонгареи",
    "North Shore": "Норт-Шор",
    "Westgate": "Уэстгейт",
    "Otahuhu": "Отахуху",
    "Manukau": "Манукау",
    "Penrose": "Пенроуз",
    "Botany": "Ботани",
    "Hamilton": "Гамильтон",
    "Tauranga": "Тауранга",
    "Rotorua": "Роторуа",
    "Napier": "Нэйпир",
    "New Plymouth": "Нью-Плимут",
    "Palmerston North": "Палмерстон-Норт",
    "Porirua": "Порируа",
    "Wellington": "Веллингтон",
    "Nelson": "Нельсон",
    "Blenheim": "Бленем",
    "Christchurch": "Крайстчёрч",
    "Timaru": "Тимару",
    "Dunedin": "Данидин",
    "Invercargill": "Инверкаргилл",
    "Auckland": "Окленд",
}

# Day-of-week and other recurring vocab in titles. Applied as whole-word
# substitutions; case-insensitive. ORDER MATTERS — multi-word/compound
# phrases MUST appear before single-word weekday matches, otherwise the
# weekday gets translated first and the compound never matches.
TITLE_TERMS = [
    # ---- compound phrases (must run first) ----
    (r"\bbig wednesday auction\b", "Большая среда — аукцион"),
    (r"\bbig thursday\b",          "Большой четверг"),
    (r"\bbig tuesday\b",           "Большой вторник"),
    (r"\bbig monday\b",            "Большой понедельник"),
    (r"\blow price tuesday\b",     "Дешёвый вторник"),
    (r"\ball\s*in\s*thursday auction\b", "Четверг — всё подряд"),
    (r"\ball in auction\b",        "Аукцион — всё подряд"),
    (r"\ball vehicles,?\s*all prices\b", "Все авто, все цены"),
    (r"\ball vehicles\s*&\s*all prices\b", "Все авто, все цены"),
    (r"\ball prices\b",            "Все цены"),
    (r"\ball makes and models\b",  "Все марки и модели"),
    (r"\bquality\s*&\s*commercial auction\b", "Качественные и коммерческие"),
    (r"\bcars,\s*commercials\s*&\s*4wd's?\b", "Легковые, коммерческие и внедорожники"),
    (r"\b4wd\s*&\s*light commercial\b",  "Внедорожники и лёгкая коммерция"),
    (r"\bjdm specialit?y\b",       "JDM-спецификация"),
    # "& Over / & Above / & Below" — must run BEFORE generic & translation
    (r"&\s*over\b",                "и выше"),
    (r"&\s*above\b",               "и выше"),
    (r"&\s*below\b",               "и ниже"),
    (r"\bvehicles under\b",        "Авто до"),
    (r"\bnorth west auckland\b",   "Северо-Запад Окленда"),
    (r"\bcentral/?south auckland\b", "Центр/Юг Окленда"),
    (r"\bsouth auckland\b",        "Юг Окленда"),
    (r"\bhamilton,?\s*tauranga\s*&\s*rotorua\b", "Гамильтон, Тауранга и Роторуа"),
    # ---- city / branch single-word ----
    (r"\bwellington\b",            "Веллингтон"),
    (r"\bnelson\b",                "Нельсон"),
    (r"\bpalmerston north\b",      "Палмерстон-Норт"),
    (r"\bnapier\b",                "Нэйпир"),
    (r"\bchristchurch\b",          "Крайстчёрч"),
    (r"\bwhangarei\b",             "Уонгареи"),
    (r"\bhornby\b",                "Крайстчёрч (Hornby)"),
    (r"\botahuhu\b",               "Отахуху"),
    (r"\bnorth shore\b",           "Норт-Шор"),
    (r"\bauckland\b",              "Окленд"),
    (r"\bhamilton\b",              "Гамильтон"),
    (r"\btauranga\b",              "Тауранга"),
    (r"\brotorua\b",               "Роторуа"),
    (r"\bdunedin\b",               "Данидин"),
    (r"\bnew plymouth\b",          "Нью-Плимут"),
    (r"\bporirua\b",               "Порируа"),
    # ---- weekdays (after compound phrases) ----
    (r"\bmonday\b",                "Понедельник"),
    (r"\btuesday\b",               "Вторник"),
    (r"\bwednesday\b",             "Среда"),
    (r"\bthursday\b",              "Четверг"),
    (r"\bfriday\b",                "Пятница"),
    (r"\bsaturday\b",              "Суббота"),
    (r"\bsunday\b",                "Воскресенье"),
    # ---- common single words ----
    (r"\bcars\b",                  "Легковые"),
    (r"\bcommercials?\b",          "Коммерческие"),
    (r"\btender\b",                "Тендер"),
    (r"\bauction\b",               "Аукцион"),
    (r"\bover\b",                  "и выше"),
    (r"\bunder\b",                 "до"),
    (r"\band below\b",             "и ниже"),
    (r"\band above\b",             "и выше"),
    # &-marker only when it's a stand-alone connector
    (r"\s+&\s+",                   " и "),
]


def _translate_title(t: str) -> str:
    if not t:
        return t
    out = t
    for pat, rep in TITLE_TERMS:
        out = re.sub(pat, rep, out, flags=re.IGNORECASE)
    # Collapse repeated whitespace artefacts
    out = re.sub(r"\s+", " ", out).strip()
    return out


def _translate_branch(b: str) -> str:
    if not b:
        return b
    nb = b.lower()
    for key, ru in BRANCH_RU.items():
        if key in nb:
            return ru
    return b


def translate_event_doc(d: Dict[str, Any]) -> Dict[str, Any]:
    """Return a *copy* of the event doc with title/branch/city in Russian.

    The English originals are preserved under `*_en` keys so the admin /
    debugging UI can still see the source string.
    """
    if not d:
        return d
    out = dict(d)
    if d.get("title"):
        out["title_en"] = d["title"]
        out["title"] = _translate_title(d["title"])
    if d.get("branch"):
        out["branch_en"] = d["branch"]
        out["branch"] = _translate_branch(d["branch"])
    if d.get("city"):
        out["city_en"] = d["city"]
        out["city"] = CITY_RU.get(d["city"], d["city"])
    return out
