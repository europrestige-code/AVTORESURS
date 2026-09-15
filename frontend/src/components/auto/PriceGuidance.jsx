import React from "react";
import { fmtRubAmount, formatRub } from "../../services/autoCurrency";

/* Price guidance block — three transparent values + disclaimer.
 *
 * Three columns, all in roubles (primary) with NZD shown small underneath:
 *   1) «Прогноз цены ухода»  — AI estimate of the FINAL hammer price.
 *   2) «Ваш потолок ставки»  — recommended max bid (don't overpay above it).
 *   3) «Ориентир под ключ»   — landed cost in RF (FOB + RU customs + freight).
 *
 * Critical UX: the customer must never read this as "the site wants me to
 * pay 5× the current bid". When the current bid << AI estimate (auction has
 * just opened), we surface a pill «Торги только открылись» so the gap is
 * explained, not perceived as a markup.
 */
export default function PriceGuidance({ vehicle }) {
  const ai = vehicle.ai_estimate || null;
  const cur = vehicle.current_price_nzd || vehicle.starting_price_nzd || 0;
  const estimateLow = ai?.estimate_low_nzd ?? vehicle.estimated_min_nzd ?? null;
  const estimateHigh = ai?.estimate_high_nzd ?? null;
  const recMax = ai?.recommended_max_bid_nzd
    ?? vehicle.recommended_bid_high_nzd
    ?? (estimateHigh ? Math.round(estimateHigh) : null);
  const recLow = ai?.recommended_max_bid_nzd
    ? Math.round(ai.recommended_max_bid_nzd * 0.92)
    : vehicle.recommended_bid_low_nzd || (cur > 0 ? Math.round(cur * 1.05) : null);

  // New full landed-cost field (includes RU customs + freight, not just FOB).
  const landedRub = vehicle.landed_estimate?.landed_total_rub || null;
  const landedNzd = vehicle.landed_estimate?.landed_total_nzd || null;

  const CONF_LABEL = {
    excellent_buy: { ru: "Отличная покупка", color: "var(--ar-success)" },
    good_buy:      { ru: "Хорошая покупка",  color: "var(--ar-success)" },
    average:       { ru: "Средняя оценка",    color: "var(--ar-warning)" },
    high_risk:     { ru: "Высокий риск",      color: "var(--ar-warning)" },
    avoid:         { ru: "Избегать",          color: "var(--ar-danger)" },
  };
  const conf = ai?.confidence && CONF_LABEL[ai.confidence];

  const stage = ai?.auction_stage;
  const stagePill = stage === "opening"
    ? { text: "Торги только открылись — финальная цена будет выше", tone: "amber" }
    : stage === "peaking"
      ? { text: "Торги близки к финалу — ставка уже у потолка", tone: "blue" }
      : null;

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

      {stagePill && (
        <div
          className={`mb-3 rounded-lg border px-3 py-2 text-[12px] leading-snug ${
            stagePill.tone === "amber"
              ? "border-amber-500/30 bg-amber-500/[0.08] text-amber-200"
              : "border-blue-500/30 bg-blue-500/[0.08] text-blue-200"
          }`}
          data-testid="pg-auction-stage"
        >
          {stagePill.text}
        </div>
      )}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Row
          label="Прогноз цены ухода"
          rub={
            estimateLow && estimateHigh
              ? `${formatRub(estimateLow)} – ${formatRub(estimateHigh)}`
              : estimateLow
                ? `от ${formatRub(estimateLow)}`
                : null
          }
          nzd={
            estimateLow && estimateHigh
              ? `NZ$${fmtNz(estimateLow)} – NZ$${fmtNz(estimateHigh)}`
              : estimateLow
                ? `от NZ$${fmtNz(estimateLow)}`
                : null
          }
          hint="ожидаемая финальная цена на торгах"
          testid="pg-estimate"
        />
        <Row
          label="Ваш потолок ставки"
          rub={recLow && recMax ? `${formatRub(recLow)} – ${formatRub(recMax)}` : null}
          nzd={recLow && recMax ? `NZ$${fmtNz(recLow)} – NZ$${fmtNz(recMax)}` : null}
          hint="выше — переплата"
          testid="pg-recommended"
        />
        <Row
          label="Ориентир под ключ"
          rub={landedRub ? `от ${fmtRubAmount(landedRub)}` : null}
          nzd={landedNzd ? `от NZ$${fmtNz(landedNzd)}` : null}
          hint="всё включено: таможня РФ + доставка до Владивостока"
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
        «Прогноз цены ухода» — ожидаемая итоговая цена молотка на торгах, а не сумма, которую
        вы платите дополнительно. «Ориентир под ключ» уже включает таможню и доставку до
        Владивостока. Финальные суммы зависят от хода торгов и курса валют.
      </p>
    </div>
  );
}

function fmtNz(v) {
  return Number(v).toLocaleString("en-NZ", { maximumFractionDigits: 0 });
}

function Row({ label, rub, nzd, hint, testid }) {
  return (
    <div data-testid={testid}>
      <div className="text-[11px] uppercase tracking-wide text-gray-400">{label}</div>
      <div className="mt-1 font-mono text-[15px] font-bold leading-tight text-white">
        {rub || "—"}
      </div>
      {nzd && (
        <div className="mt-0.5 font-mono text-[11px] text-gray-500">{nzd}</div>
      )}
      {hint && <div className="mt-0.5 text-[11px] text-gray-500">{hint}</div>}
    </div>
  );
}
