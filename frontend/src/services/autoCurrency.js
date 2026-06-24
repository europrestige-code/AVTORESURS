/**
 * АвтоРесурс — public currency display utilities.
 *
 * The catalogue stores prices in NZD (the auction currency), but Russian
 * customers always see RUB. We fetch the live NZD→RUB rate (Google/spot)
 * from /api/auto/fx-rate, apply the +3% convenience markup server-side, and
 * cache the response in-memory for an hour.
 */
import autoApi from "./autoApi";

let _cache = null;       // { nzd_to_rub_display, ... }
let _cacheAt = 0;
let _pending = null;
const TTL_MS = 60 * 60 * 1000;

export async function getFxRate({ force = false } = {}) {
  const now = Date.now();
  if (!force && _cache && now - _cacheAt < TTL_MS) return _cache;
  if (_pending) return _pending;
  _pending = (async () => {
    try {
      const r = await autoApi.get("/fx-rate");
      _cache = r.data;
      _cacheAt = Date.now();
      return _cache;
    } catch {
      // ultra-safe fallback so the UI never crashes
      _cache = {
        nzd_to_rub_spot: 56,
        nzd_to_rub_display: 57.68,   // 56 × 1.03
        markup_pct: 0.03,
        source: "fallback",
      };
      _cacheAt = Date.now();
      return _cache;
    } finally {
      _pending = null;
    }
  })();
  return _pending;
}

/** Synchronous formatter — assumes you've called getFxRate() at startup. */
export function formatRub(nzd, { fallback = "—" } = {}) {
  if (nzd == null || isNaN(nzd)) return fallback;
  const rate = _cache?.nzd_to_rub_display ?? 57.68;
  const rub = Number(nzd) * Number(rate);
  return `${Math.round(rub).toLocaleString("ru-RU")} ₽`;
}

/** Convert + format, with provided rate (handy in components that already
 *  have the rate via React state). */
export function nzdToRub(nzd, rate) {
  if (nzd == null) return null;
  return Number(nzd) * Number(rate || _cache?.nzd_to_rub_display || 57.68);
}

export function fmtRubAmount(rub, { fallback = "—" } = {}) {
  if (rub == null || isNaN(rub)) return fallback;
  return `${Math.round(rub).toLocaleString("ru-RU")} ₽`;
}
