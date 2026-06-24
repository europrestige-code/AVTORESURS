"""
АвтоРесурс — Russian customs / total-landed-cost calculator.

Purpose
-------
NZ auction prices we display are **FOB** (free-on-board at the seller). Russian
buyers ultimately care about the *delivered-to-Vladivostok-with-papers* price,
which includes:

    1. FOB price (NZD)         — what the customer wins / buys for at auction
    2. NZ-side fees             — auction premium, AvtoResurs commission,
                                  local transport from branch → Auckland port
                                  (Auckland $0 → Invercargill $1,950; ×2 if
                                  non-runner), optional inspection, forklift,
                                  dismantling/cut service (parts/EOL only),
                                  documents and short-term storage
    3. Freight to Vladivostok   — 2 cars per 40' container ≈ $5,000 / car
    4. Insurance (CIF)          — ~1.5% of FOB+freight
    5. Russian customs duty     — engine-displacement based (физлицо) OR
                                   15% + VAT + excise (юрлицо / commercial)
    6. Утилизационный сбор      — льготный 3,400/5,200 ₽ OR коммерческий
                                   (millions of ₽ for >160hp or >3000cc)
    7. НДС (VAT)                — 20% (юрлицо only — физлицо not charged)
    8. Excise (акциз)           — per-HP, applies for commercial / >150hp
    9. Declaration fee          — 775 ₽

Two import schemes are supported:
    - WHOLE car (целый) — gets ПТС, can be registered
    - PARTS  (распил / конструктор) — no ПТС, simplified ~15% duty + VAT

The frontend NEVER shows landed cost by default — it only appears in a
"Рассчитать под ключ в РФ" popup. For DAMAGED and END_OF_LIFE listings the
popup pre-selects the right extras (non-runner, forklift, dismantling).

⚠️  RATES ARE INDICATIVE — actual amounts depend on the declared engine
    displacement, HP, VIN, age and current FX, and can vary ±10%.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Literal, Optional

from services.auto_transport_service import transport_cost as nz_transport_cost


# ---------------------------------------------------------------------------
# FX assumptions (refreshed periodically — could be wired to currency_service)
# ---------------------------------------------------------------------------

DEFAULT_NZD_TO_USD = 0.60
DEFAULT_USD_TO_EUR = 0.92
DEFAULT_USD_TO_RUB = 95.0
DEFAULT_EUR_TO_RUB = DEFAULT_USD_TO_RUB / DEFAULT_USD_TO_EUR  # ≈ 103.2

# Freight: 2 cars per 40-ft container @ $5,000 / car (per user spec)
FREIGHT_PER_CAR_USD = 5000.0

# Insurance over FOB+freight
INSURANCE_PCT = 0.015

# NZ-side fees (buyer's premium + transport from auction yard → port)
NZ_BUYERS_PREMIUM_PCT = 0.10   # ~10% typical auction premium
NZ_LOCAL_TRANSPORT_NZD = 500.0  # average inland NZ transport (fallback if branch unknown)
AVTORESURS_COMMISSION_PCT = 0.20  # АвтоРесурс service fee on FOB

# Optional NZ-side service fees (per car) — applied when relevant
INSPECTION_FEE_NZD     = 200.0   # detailed pre-purchase inspection at yard
FORKLIFT_FEE_NZD       = 120.0   # forklift loading (for non-runners, damaged)
DISMANTLING_FEE_NZD    = 800.0   # cut / dismantle for parts scheme (EOL/parts)
DOCS_FEE_NZD           = 250.0   # NZ export documents
STORAGE_PER_DAY_NZD    = 50.0    # yard storage per day waiting for container

DECLARATION_FEE_RUB = 775.0


# ---------------------------------------------------------------------------
# Custom duty schedules (€ / cm³ — ETS for individuals)
# ---------------------------------------------------------------------------

# Cars >5 years old — per-cm³ ONLY (no percentage)
DUTY_OLD_PER_CC_EUR: List[tuple] = [
    (1000,  3.0),
    (1500,  3.2),
    (1800,  3.5),
    (2300,  4.8),
    (3000,  5.0),
    (10_000, 5.7),
]

# Cars 3-5 years old — per-cm³ ONLY
DUTY_3_5_PER_CC_EUR: List[tuple] = [
    (1000,  1.5),
    (1500,  1.7),
    (1800,  2.5),
    (2300,  2.7),
    (3000,  3.0),
    (10_000, 3.6),
]

# Cars <3 years (new) — percentage of CIF, with a per-cm³ minimum
DUTY_NEW_BANDS: List[tuple] = [
    # (max_cif_eur, pct, min_eur_per_cc)
    (8_500,    0.54, 2.5),
    (16_700,   0.48, 3.5),
    (42_300,   0.48, 5.5),
    (84_500,   0.48, 7.5),
    (169_000,  0.48, 15.0),
    (10_000_000, 0.48, 20.0),
]


def _pick_per_cc(table: List[tuple], cc: int) -> float:
    for cap, rate in table:
        if cc <= cap:
            return rate
    return table[-1][1]


def _pick_new_band(table: List[tuple], cif_eur: float) -> tuple:
    for cap, pct, per_cc in table:
        if cif_eur <= cap:
            return (pct, per_cc)
    return (table[-1][1], table[-1][2])


# ---------------------------------------------------------------------------
# Утильсбор coefficients (passenger cars)
# ---------------------------------------------------------------------------

UTILSBOR_BASE_RUB = 20_000.0

# Льготная (личное пользование) ставка — fixed, regardless of engine
UTILSBOR_PERSONAL_NEW_RUB = 3_400.0   # ≤3 yrs
UTILSBOR_PERSONAL_USED_RUB = 5_200.0  # >3 yrs

# Conditions for льгота: engine ≤3000 cc AND power ≤160 HP AND personal use
UTILSBOR_PERSONAL_CC_LIMIT = 3000
UTILSBOR_PERSONAL_HP_LIMIT = 160

# Commercial coefficients (October 2024 schedule, applied when льгота not met
# OR for legal entities). Coefficient × 20,000 ₽ base.
# Approximate consolidated table:
UTILSBOR_COMMERCIAL_NEW: List[tuple] = [
    # (max_cc, coefficient)
    (1000,  10.0),
    (2000,  75.34),
    (3000,  150.7),
    (3500,  178.0),
    (10_000, 268.9),
]
UTILSBOR_COMMERCIAL_USED: List[tuple] = [
    (1000,  26.44),
    (2000,  152.74),
    (3000,  283.05),
    (3500,  300.0),
    (10_000, 372.6),
]


def _pick_utilsbor_coeff(cc: int, used: bool) -> float:
    table = UTILSBOR_COMMERCIAL_USED if used else UTILSBOR_COMMERCIAL_NEW
    for cap, coeff in table:
        if cc <= cap:
            return coeff
    return table[-1][1]


# ---------------------------------------------------------------------------
# Excise (акциз) — per HP, applied to legal-entity imports
# ---------------------------------------------------------------------------

EXCISE_PER_HP_RUB: List[tuple] = [
    # (max_hp, rub_per_hp)  — 2025 federal rates
    (90,    0),
    (150,   63),
    (200,   745),
    (300,   1_211),
    (400,   2_062),
    (500,   2_133),
    (10_000, 2_204),
]


def _pick_excise_per_hp(hp: int) -> float:
    for cap, rate in EXCISE_PER_HP_RUB:
        if hp <= cap:
            return rate
    return EXCISE_PER_HP_RUB[-1][1]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

ImporterType = Literal["personal", "commercial"]
Scheme = Literal["whole", "parts"]


@dataclass
class FxRates:
    nzd_to_usd: float = DEFAULT_NZD_TO_USD
    usd_to_eur: float = DEFAULT_USD_TO_EUR
    usd_to_rub: float = DEFAULT_USD_TO_RUB

    @property
    def eur_to_rub(self) -> float:
        return self.usd_to_rub / self.usd_to_eur


@dataclass
class RuCustomsResult:
    # inputs echo
    fob_nzd: float
    age_years: int
    engine_cc: int
    engine_hp: int
    importer_type: ImporterType
    scheme: Scheme

    # NZ side
    nz_buyers_premium_nzd: float
    avtoresurs_commission_nzd: float
    nz_local_transport_nzd: float
    nz_local_transport_branch: Optional[str]
    nz_local_transport_non_runner: bool
    inspection_fee_nzd: float
    forklift_fee_nzd: float
    dismantling_fee_nzd: float
    docs_fee_nzd: float
    storage_days: int
    storage_fee_nzd: float
    nz_extras_total_nzd: float

    freight_usd: float
    insurance_usd: float
    cif_usd: float
    cif_eur: float
    cif_rub: float

    # RU customs
    duty_rub: float
    excise_rub: float
    vat_rub: float
    utilsbor_rub: float
    declaration_fee_rub: float
    customs_total_rub: float

    # Final
    landed_total_nzd: float
    landed_total_usd: float
    landed_total_rub: float

    fx: Dict[str, float]
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, float]:
        d = asdict(self)
        # round all numerics to whole/2dp for UI
        for k, v in list(d.items()):
            if isinstance(v, float):
                d[k] = round(v, 2)
        d["fx"] = {k: round(v, 4) for k, v in self.fx.items()}
        return d


# ---------------------------------------------------------------------------
# Public calculator
# ---------------------------------------------------------------------------

def calculate_ru_landed_cost(
    fob_nzd: float,
    *,
    age_years: int,
    engine_cc: int,
    engine_hp: int = 0,
    importer_type: ImporterType = "personal",
    scheme: Scheme = "whole",
    fx: Optional[FxRates] = None,
    include_nz_buyers_premium: bool = True,
    include_avtoresurs_commission: bool = True,
    freight_per_car_usd: float = FREIGHT_PER_CAR_USD,
    # NZ-side options
    nz_branch: Optional[str] = None,
    is_non_runner: bool = False,
    inspection: bool = False,
    forklift: bool = False,
    dismantling: bool = False,
    docs_fee: bool = True,
    storage_days: int = 0,
) -> RuCustomsResult:
    """Return a full landed-cost breakdown for a NZ→Vladivostok import.

    NZ extras (per car):
        nz_branch        — Turners/Manheim/Pickles branch the car ships from.
                            Drives the real local-transport cost via
                            `auto_transport_service.transport_cost`.
        is_non_runner    — non-runner ⇒ ×2 transport (towing surcharge) and
                            usually requires forklift loading.
        inspection       — NZ$200 pre-purchase inspection.
        forklift         — NZ$120 forklift loading (auto-on for non-runner).
        dismantling      — NZ$800 cut / dismantle (parts scheme / EOL).
        docs_fee         — NZ$250 NZ export paperwork (default on).
        storage_days     — yard storage days × NZ$50.
    """
    fx = fx or FxRates()
    notes: List[str] = []
    used = age_years >= 3

    # ----- NZ side fees (everything we add on top of FOB before shipping) -----
    fob_usd = fob_nzd * fx.nzd_to_usd

    nz_premium_nzd = fob_nzd * NZ_BUYERS_PREMIUM_PCT if include_nz_buyers_premium else 0.0
    commission_nzd = fob_nzd * AVTORESURS_COMMISSION_PCT if include_avtoresurs_commission else 0.0

    # Local transport — branch-aware
    if nz_branch:
        tcost = nz_transport_cost(nz_branch, is_non_runner=is_non_runner)
        local_transport_nzd = float(tcost["transport_nzd"])
        if not tcost["matched"]:
            notes.append(
                f"Бранч «{nz_branch}» не найден в тарифной таблице — "
                f"использован усреднённый транспорт NZ${local_transport_nzd:.0f}."
            )
    else:
        local_transport_nzd = NZ_LOCAL_TRANSPORT_NZD * (2 if is_non_runner else 1)
        notes.append("Бранч не указан — взят средний NZ-транспорт.")

    if is_non_runner:
        notes.append("Авто НЕ НА ХОДУ — транспорт ×2 (буксировка), форклифт обязателен.")
        forklift = True  # forklift is mandatory for non-runners

    inspection_fee = INSPECTION_FEE_NZD if inspection else 0.0
    forklift_fee   = FORKLIFT_FEE_NZD if forklift else 0.0
    dismantling_fee = DISMANTLING_FEE_NZD if dismantling else 0.0
    docs_fee_nzd   = DOCS_FEE_NZD if docs_fee else 0.0
    storage_fee    = STORAGE_PER_DAY_NZD * max(0, int(storage_days))

    nz_extras_total = (
        nz_premium_nzd + commission_nzd + local_transport_nzd
        + inspection_fee + forklift_fee + dismantling_fee
        + docs_fee_nzd + storage_fee
    )
    nz_extras_usd = nz_extras_total * fx.nzd_to_usd

    # ----- Ocean freight + insurance -----
    freight_usd = freight_per_car_usd
    insurance_usd = (fob_usd + nz_extras_usd + freight_usd) * INSURANCE_PCT

    cif_usd = fob_usd + nz_extras_usd + freight_usd + insurance_usd
    cif_eur = cif_usd * fx.usd_to_eur
    cif_rub = cif_usd * fx.usd_to_rub

    # ----- Customs duty / VAT / excise / утильсбор -----
    duty_rub = 0.0
    excise_rub = 0.0
    vat_rub = 0.0
    utilsbor_rub = 0.0

    if scheme == "parts":
        # Parts / распил-конструктор: 15% of value + VAT 20%, no util sbor,
        # no ПТС. Excise not applied as parts are not «transport».
        duty_rub = cif_rub * 0.15
        vat_rub = (cif_rub + duty_rub) * 0.20
        notes.append(
            "Схема «запчасти» (распил/конструктор): без ПТС, регистрация в "
            "ГИБДД невозможна. Подходит только как донор/на запчасти."
        )
    else:
        # Whole car
        if importer_type == "personal":
            # ETS (единая таможенная ставка) — only duty, no VAT, no excise
            if age_years < 3:
                pct, per_cc = _pick_new_band(DUTY_NEW_BANDS, cif_eur)
                duty_pct = cif_eur * pct
                duty_cc = engine_cc * per_cc
                duty_eur = max(duty_pct, duty_cc)
            elif age_years <= 5:
                duty_eur = engine_cc * _pick_per_cc(DUTY_3_5_PER_CC_EUR, engine_cc)
            else:
                duty_eur = engine_cc * _pick_per_cc(DUTY_OLD_PER_CC_EUR, engine_cc)
            duty_rub = duty_eur * fx.eur_to_rub

            # Утильсбор
            qualifies_for_lgota = (
                engine_cc <= UTILSBOR_PERSONAL_CC_LIMIT
                and engine_hp <= UTILSBOR_PERSONAL_HP_LIMIT
            )
            if qualifies_for_lgota:
                utilsbor_rub = (
                    UTILSBOR_PERSONAL_USED_RUB if used else UTILSBOR_PERSONAL_NEW_RUB
                )
                notes.append(
                    "Применена ЛЬГОТНАЯ ставка утильсбора (физлицо, личное "
                    "пользование, двигатель ≤3000 см³ и ≤160 л.с.). При "
                    "несоблюдении хотя бы одного условия применяется "
                    "коммерческая ставка — это +1–4 млн ₽."
                )
            else:
                coeff = _pick_utilsbor_coeff(engine_cc, used)
                utilsbor_rub = UTILSBOR_BASE_RUB * coeff
                notes.append(
                    "Льгота утильсбора НЕ применена (двигатель >3000 см³ "
                    "или >160 л.с.) — действует коммерческий коэффициент. "
                    "Это резко увеличивает итог."
                )
        else:
            # commercial / юрлицо: 15% duty + excise + 20% VAT + commercial utilsbor
            duty_rub = cif_rub * 0.15
            excise_per_hp = _pick_excise_per_hp(engine_hp or 0)
            excise_rub = excise_per_hp * (engine_hp or 0)
            vat_rub = (cif_rub + duty_rub + excise_rub) * 0.20
            coeff = _pick_utilsbor_coeff(engine_cc, used)
            utilsbor_rub = UTILSBOR_BASE_RUB * coeff
            notes.append(
                "Ввоз как юрлицо: 15% пошлина + акциз по л.с. + 20% НДС + "
                "коммерческий утильсбор. Для большинства легковых авто это "
                "значительно дороже схемы физлица."
            )

    customs_total_rub = duty_rub + excise_rub + vat_rub + utilsbor_rub + DECLARATION_FEE_RUB

    # ----- Final totals (RUB / USD / NZD) -----
    landed_rub = cif_rub + customs_total_rub
    landed_usd = landed_rub / fx.usd_to_rub
    landed_nzd = landed_usd / fx.nzd_to_usd

    return RuCustomsResult(
        fob_nzd=fob_nzd,
        age_years=age_years,
        engine_cc=engine_cc,
        engine_hp=engine_hp,
        importer_type=importer_type,
        scheme=scheme,
        nz_buyers_premium_nzd=nz_premium_nzd,
        avtoresurs_commission_nzd=commission_nzd,
        nz_local_transport_nzd=local_transport_nzd,
        nz_local_transport_branch=nz_branch,
        nz_local_transport_non_runner=is_non_runner,
        inspection_fee_nzd=inspection_fee,
        forklift_fee_nzd=forklift_fee,
        dismantling_fee_nzd=dismantling_fee,
        docs_fee_nzd=docs_fee_nzd,
        storage_days=int(storage_days or 0),
        storage_fee_nzd=storage_fee,
        nz_extras_total_nzd=nz_extras_total,
        freight_usd=freight_usd,
        insurance_usd=insurance_usd,
        cif_usd=cif_usd,
        cif_eur=cif_eur,
        cif_rub=cif_rub,
        duty_rub=duty_rub,
        excise_rub=excise_rub,
        vat_rub=vat_rub,
        utilsbor_rub=utilsbor_rub,
        declaration_fee_rub=DECLARATION_FEE_RUB,
        customs_total_rub=customs_total_rub,
        landed_total_nzd=landed_nzd,
        landed_total_usd=landed_usd,
        landed_total_rub=landed_rub,
        fx={
            "nzd_to_usd": fx.nzd_to_usd,
            "usd_to_eur": fx.usd_to_eur,
            "usd_to_rub": fx.usd_to_rub,
            "eur_to_rub": fx.eur_to_rub,
        },
        notes=notes,
    )


def suggest_defaults_for_listing(listing_type: str = "auction",
                                   damage_type: Optional[str] = None,
                                   condition: Optional[str] = None) -> Dict[str, object]:
    """Return sensible defaults the modal can preselect from a vehicle row.

    Damaged or End-of-Life vehicles automatically get non-runner + forklift,
    and EOL gets the 'parts' scheme + dismantling fee.
    """
    listing_type = (listing_type or "").lower()
    damage_type = (damage_type or "").lower()
    condition = (condition or "").lower()
    is_damaged = listing_type == "damaged" or "damage" in damage_type or "accident" in condition
    is_eol = listing_type == "end_of_life" or "eol" in damage_type or "scrap" in condition or "donor" in condition
    if is_eol:
        return {
            "scheme": "parts",
            "is_non_runner": True,
            "forklift": True,
            "dismantling": True,
            "inspection": False,
        }
    if is_damaged:
        return {
            "scheme": "whole",
            "is_non_runner": True,
            "forklift": True,
            "dismantling": False,
            "inspection": True,
        }
    return {
        "scheme": "whole",
        "is_non_runner": False,
        "forklift": False,
        "dismantling": False,
        "inspection": False,
    }
