import React from "react";
import { formatRub, fmtRubAmount } from "../../services/autoCurrency";
import { fmtPrice } from "./VehicleCard";

/* Price guidance block — three transparent values + disclaimer.
 *
 * The spec wants users to see:
 *   - Оценка аукциона (estimate from)         — fallback bands when no auction price
 *   - Рекомендуемая ставка (low–high range)  — derived from the current/estimated price
 *   - Ориентир под ключ (in RUB)             — from price_breakdown if available, otherwise computed
 *
 * Everything is presented as an *estimate* with a clear disclaimer so we
 * never imply a binding price.
 */
export default function PriceGuidance({ vehicle }) {
  const cur = vehicle.current_price_nzd || vehicle.starting_price_nzd || 0;
  const estimate = vehicle.estimated_min_nzd || cur || 0;

  // Recommended bid range — heuristic when not provided by source.
  // Defaults to the current price as the lower bound and +25 % as the upper.
  const recLow = vehicle.recommended_bid_low_nzd || (cur > 0 ? cur : Math.round(estimate * 1.05));
  const recHigh = vehicle.recommended_bid_high_nzd || Math.round((recLow || estimate) * 1.25);

  // Landed estimate in RUB. Use the existing breakdown if precomputed.
  const landedRub = vehicle.price_breakdown?.total_rub || null;

  return (
    <div
      className="mb-3 rounded-2xl border border-white/10 bg-[var(--ar-card)] p-5"
      data-testid="price-guidance"
    >
      <div className="mb-3 flex items-center justify-between gap-2">
        <h3 className="text-base font-bold text-white">Ориентир по цене</h3>
        <span className="text-[10px] uppercase tracking-wide text-gray-500">оценка</span>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Row
          label="Оценка аукциона"
          value={estimate ? `от ${fmtPrice(estimate)}` : "—"}
          hint="по данным источника"
          testid="pg-estimate"
        />
        <Row
          label="Рекомендуемая ставка"
          value={recLow && recHigh ? `${fmtPrice(recLow)} – ${fmtPrice(recHigh)}` : "—"}
          hint="диапазон для победы"
          testid="pg-recommended"
        />
        <Row
          label="Ориентир под ключ"
          value={
            landedRub
              ? `от ${fmtRubAmount(landedRub)}`
              : cur
                ? `от ${formatRub(cur)}`
                : "—"
          }
          hint="до Владивостока"
          testid="pg-landed"
        />
      </div>

      <p className="mt-4 text-[12px] leading-snug text-gray-500" data-testid="pg-disclaimer">
        Финальная цена зависит от торгов, курса валют, доставки и дополнительных расходов.
        Все суммы приведены справочно.
      </p>
    </div>
  );
}

function Row({ label, value, hint, testid }) {
  return (
    <div data-testid={testid}>
      <div className="text-[11px] uppercase tracking-wide text-gray-400">{label}</div>
      <div className="mt-1 font-mono text-base font-bold text-white">{value}</div>
      {hint && <div className="text-[11px] text-gray-500">{hint}</div>}
    </div>
  );
}
