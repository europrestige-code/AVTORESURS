"""Iteration 18 backend tests.

Focus:
  1. landed_estimate on vehicle detail endpoint (with RU customs baked in).
  2. sanitize_ai_estimate applied on list + detail; auction_stage tagging.
  3. Payment terms v2026.06.27.1 — 72h window, 24h grace, updated bullets_ru[3].
  4. RU customs calc endpoint sanity.
  5. Landed defaults for damaged / end_of_life listings.
  6. Quiz meta + submit endpoints.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api/auto"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def sample_vehicles(session):
    """Return the plain first-5 list — used to verify default catalog response."""
    r = session.get(f"{API}/vehicles", params={"limit": 5}, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    items = data.get("items") or data.get("vehicles") or data
    assert isinstance(items, list) and len(items) > 0, f"No vehicles: {data}"
    return items


@pytest.fixture(scope="module")
def priced_vehicle(session):
    """Find any vehicle with a real price so landed_estimate can be computed.
    The DB has ~1608 rows but many have no price; scan several pages."""
    for offset in (0, 500, 800, 1000, 1300, 1500):
        r = session.get(f"{API}/vehicles", params={"limit": 100, "offset": offset}, timeout=30)
        if r.status_code != 200:
            continue
        for v in r.json().get("items", []):
            if float(v.get("current_price_nzd") or 0) >= 500 or float(v.get("buy_now_price_nzd") or 0) >= 500:
                return v
    pytest.skip("no priced vehicle found in DB")


@pytest.fixture(scope="module")
def ai_vehicles(session):
    """Vehicles that have ai_estimate — needed to check sanitize rules."""
    acc = []
    for offset in (1400, 1500, 1550):
        r = session.get(f"{API}/vehicles", params={"limit": 100, "offset": offset}, timeout=30)
        if r.status_code != 200:
            continue
        for v in r.json().get("items", []):
            if v.get("ai_estimate"):
                acc.append(v)
        if len(acc) >= 20:
            break
    return acc


# ---------- 1. landed_estimate on GET /vehicles/{id} ----------
class TestLandedEstimate:
    def test_landed_estimate_present_and_realistic(self, session, priced_vehicle):
        target = priced_vehicle
        vid = target["id"]
        r = session.get(f"{API}/vehicles/{vid}", timeout=30)
        assert r.status_code == 200, r.text
        doc = r.json()
        le = doc.get("landed_estimate")
        assert le is not None, f"landed_estimate missing on vehicle {vid}"
        for k in ("landed_total_rub", "landed_total_nzd", "landed_total_usd",
                  "fob_nzd", "scheme", "assumed_engine_cc", "assumed_age_years"):
            assert k in le, f"missing field {k}: {le}"
        assert le["landed_total_rub"] >= 500_000, (
            f"landed_total_rub={le['landed_total_rub']} too low — RU customs likely not added"
        )
        assert le["scheme"] in ("whole", "parts")
        assert isinstance(le["assumed_engine_cc"], int) and le["assumed_engine_cc"] > 0
        assert isinstance(le["assumed_age_years"], int)


# ---------- 2. sanitize_ai_estimate + auction_stage ----------
class TestAiSanitize:
    def test_list_estimates_sanitized(self, session, ai_vehicles):
        if not ai_vehicles:
            pytest.skip("no ai_estimate-carrying vehicles in DB slice")
        checked = 0
        for v in ai_vehicles[:20]:
            ai = v.get("ai_estimate")
            if not ai:
                continue
            checked += 1
            cur = float(v.get("current_price_nzd") or 0)
            buy = float(v.get("buy_now_price_nzd") or 0)
            assert ai.get("auction_stage") in ("opening", "active", "peaking"), (
                f"auction_stage missing/invalid on {v['id']}: {ai.get('auction_stage')}"
            )
            low = ai.get("estimate_low_nzd")
            high = ai.get("estimate_high_nzd")
            if cur > 0 and low is not None:
                assert float(low) >= cur - 0.5, (
                    f"low={low} < current={cur} on {v['id']}"
                )
            if high is not None and low is not None:
                candidates = []
                if cur > 0:
                    candidates.append(cur * 4.0)
                if buy > 0:
                    candidates.append(buy * 1.10)
                candidates.append(float(low) * 1.6)
                cap = max(candidates)
                assert float(high) <= cap + 1, (
                    f"high={high} > cap={cap} on {v['id']}"
                )
        assert checked > 0, "no vehicles with ai_estimate in sample — sanitize not exercised"


# ---------- 3. Payment terms ----------
class TestPaymentTerms:
    def test_payment_terms_v2(self, session):
        r = session.get(f"{API}/payment-terms", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("full_payment_window_hours") == 72, data
        assert data.get("full_payment_grace_hours") == 24, data
        assert data.get("version") == "v2026.06.27.1", data
        bullets = data.get("bullets_ru") or []
        assert len(bullets) >= 4, bullets
        b3 = bullets[3].lower()
        assert "штраф" in b3, f"bullets_ru[3] missing 'штраф': {bullets[3]}"
        assert "72" in b3, f"bullets_ru[3] missing '72': {bullets[3]}"


# ---------- 4. RU customs calc ----------
class TestRuCustomsCalc:
    def test_calc_breakdown(self, session):
        r = session.get(
            f"{API}/ru-customs/calc",
            params={"fob_nzd": 1300, "age_years": 4, "engine_cc": 2000},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        for k in ("landed_total_rub", "duty_rub", "utilsbor_rub", "cif_rub"):
            assert k in data, f"missing {k}: {data}"
            assert isinstance(data[k], (int, float)), data
        assert data["landed_total_rub"] > 0
        assert data["duty_rub"] > 0
        assert data["utilsbor_rub"] > 0


# ---------- 5. Landed defaults ----------
class TestLandedDefaults:
    def _find_by(self, session, **filters):
        r = session.get(f"{API}/vehicles", params={"limit": 50, **filters}, timeout=30)
        assert r.status_code == 200
        items = r.json().get("items") or []
        return items

    def test_damaged_defaults(self, session):
        # try a few damaged listings
        candidates = self._find_by(session, damage_type="damaged")
        if not candidates:
            # fallback: iterate broader page and filter locally
            r = session.get(f"{API}/vehicles", params={"limit": 100}, timeout=30)
            items = r.json().get("items") or []
            candidates = [v for v in items if (v.get("damage_type") or "").lower() in ("damaged", "accident")]
        if not candidates:
            pytest.skip("no damaged vehicles found in sample")
        v = candidates[0]
        r = session.get(f"{API}/vehicles/{v['id']}/landed-defaults", timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("is_non_runner") is True, d
        assert d.get("forklift") is True, d
        assert d.get("inspection") is True, d

    def test_end_of_life_defaults(self, session):
        r = session.get(f"{API}/vehicles", params={"limit": 200}, timeout=30)
        items = r.json().get("items") or []
        eol = [v for v in items if (v.get("listing_type") or "").lower() in ("end_of_life", "eol")
               or (v.get("damage_type") or "").lower() in ("end_of_life", "eol")]
        if not eol:
            pytest.skip("no end_of_life vehicles found in sample")
        v = eol[0]
        r = session.get(f"{API}/vehicles/{v['id']}/landed-defaults", timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("is_non_runner") is True, d
        assert d.get("scheme") == "parts", d
        assert d.get("dismantling") is True, d


# ---------- 6. Quiz ----------
class TestQuiz:
    def test_quiz_meta(self, session):
        r = session.get(f"{API}/quiz/meta", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        for k in ("budgets", "purposes", "urgencies", "countries", "repairs", "buyer_types"):
            assert k in data, f"missing {k}"
            assert isinstance(data[k], list) and len(data[k]) > 0, f"{k} empty"

    def test_quiz_submit(self, session):
        # Fetch meta to pick valid keys
        meta = session.get(f"{API}/quiz/meta", timeout=15).json()
        def key(lst):
            item = lst[0]
            if isinstance(item, dict):
                return item.get("key") or item.get("value") or item.get("id")
            return item
        payload = {
            "name": "TEST_QuizUser",
            "contact": "test@example.com",
            "purpose": key(meta["purposes"]),
            "body_types": ["sedan"],
            "budget_key": key(meta["budgets"]),
            "country": key(meta["countries"]),
            "urgency": key(meta["urgencies"]),
            "repair": key(meta["repairs"]),
            "buyer_type": key(meta["buyer_types"]),
        }
        r = session.post(f"{API}/quiz/submit", json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "lead" in data, data
        assert "matches" in data, data
        assert "match_count" in data, data
        lead = data["lead"]
        assert "budget_nzd_max" in lead, lead
        assert "body_types" in lead, lead
        assert "country" in lead, lead
        assert "repair" in lead, lead
