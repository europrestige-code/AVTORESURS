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
  const ai = vehicle.ai_estimate || null;
  const cur = vehicle.current_price_nzd || vehicle.starting_price_nzd || 0;
  const estimateLow = ai?.estimate_low_nzd ?? vehicle.estimated_min_nzd ?? null;
  const estimateHigh = ai?.estimate_high_nzd ?? null;
  const recLow = ai?.recommended_max_bid_nzd
    ? Math.round(ai.recommended_max_bid_nzd * 0.9)
    : vehicle.recommended_bid_low_nzd || (cur > 0 ? cur : null);
  const recHigh = ai?.recommended_max_bid_nzd
    ?? vehicle.recommended_bid_high_nzd
    ?? (recLow ? Math.round(recLow * 1.15) : null);

  // Landed estimate in RUB. Use the existing breakdown if precomputed.
  const landedRub = vehicle.price_breakdown?.total_rub || null;

  const CONF_LABEL = {
    excellent_buy: { ru: "Отличная покупка", color: "var(--ar-success)" },
    good_buy:      { ru: "Хорошая покупка",  color: "var(--ar-success)" },
    average:       { ru: "Средняя оценка",    color: "var(--ar-warning)" },
    high_risk:     { ru: "Высокий риск",      color: "var(--ar-warning)" },
    avoid:         { ru: "Избегать",          color: "var(--ar-danger)" },
  };
  const conf = ai?.confidence && CONF_LABEL[ai.confidence];

  return (
    <div
      className="mb-3 rounded-2xl border border-white/10 bg-[var(--ar-card)] p-5"
      data-testid="price-guidance"
    >
      <div className="mb-3 flex items-center justify-between gap-2">
        <h3 className="text-base font-bold text-white">Оценка ИИ и ориентир по цене</h3>
        {conf && (
          <span
            className="rounded-full px-2.5 py-1 text-[11px] font-bold"
            style={{ background: conf.color + "22", color: conf.color }}
            data-testid="pg-confidence-badge"
          >
            {conf.ru}{ai.market_score != null ? ` · ${ai.market_score}/100` : ""}
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Row
          label="Оценка аукциона ИИ"
          value={
            estimateLow && estimateHigh
              ? `${fmtPrice(estimateLow)} – ${fmtPrice(estimateHigh)}`
              : estimateLow
                ? `от ${fmtPrice(estimateLow)}`
                : "—"
          }
          hint={ai ? `${ai.based_on_observations || 0} наблюдений · ${ai.model || "AI"}` : "по данным источника"}
          testid="pg-estimate"
        />
        <Row
          label="Рекомендуемая ставка"
          value={recLow && recHigh ? `${fmtPrice(recLow)} – ${fmtPrice(recHigh)}` : "—"}
          hint="макс. цена выигрыша"
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

      {ai?.reasoning && ai.reasoning.length > 0 && (
        <div className="mt-4 rounded-lg border border-blue-500/15 bg-blue-500/[0.05] p-3" data-testid="pg-reasoning">
          <div className="mb-1.5 text-[11px] uppercase tracking-wide text-blue-300">Почему ИИ так оценил</div>
          <ul className="space-y-1 text-[13px] leading-snug text-gray-200">
            {ai.reasoning.slice(0, 5).map((line, i) => (
              <li key={i} className="flex gap-2">
                <span className="text-blue-400">•</span>
                <span>{line}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="mt-4 text-[12px] leading-snug text-gray-500" data-testid="pg-disclaimer">
        Все суммы — оценочные. Финальная цена зависит от торгов, курса валют, доставки и дополнительных расходов.
        Оценка ИИ улучшается по мере накопления данных о наблюдениях с аукционов.
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
