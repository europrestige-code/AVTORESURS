import React, { useEffect, useState } from "react";
import { TrendingUp, Info } from "lucide-react";
import autoApi from "../../services/autoApi";
import { formatRub } from "../../services/autoCurrency";

/**
 * Sold-history tile: «Похожие проданы за NZ$X-Y» when we have historical
 * hammer prices, or «Похожие выставлены за NZ$X-Y» when we fall back to
 * live listings. Silently hides when there's not enough data.
 */
export default function SoldHistory({ vehicleId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!vehicleId) return;
    let cancelled = false;
    setLoading(true);
    autoApi
      .get(`/vehicles/${vehicleId}/sold-history`)
      .then((r) => {
        if (!cancelled) setData(r.data);
      })
      .catch(() => {
        if (!cancelled) setData(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [vehicleId]);

  if (loading || !data || data.source === "insufficient") return null;

  const isSold = data.source === "sold_observations";
  const title = isSold ? "Похожие проданы за" : "Похожие выставлены за";
  const hint = isSold
    ? `по данным ${data.count} закрытых торгов за похожие ${data.make} ${data.model} ${data.year ? `${data.year - data.year_window}–${data.year + data.year_window}` : ""} г.`
    : `${data.count} активных лотов ${data.make} ${data.model}${data.year ? ` ${data.year - data.year_window}–${data.year + data.year_window} г.` : ""} сейчас в каталоге`;

  return (
    <div
      className="mb-3 rounded-2xl border border-white/10 bg-[var(--ar-card)] p-4"
      data-testid="sold-history"
    >
      <div className="flex items-start gap-3">
        <div
          className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg"
          style={{
            background: isSold ? "rgba(0,200,83,0.12)" : "rgba(58,134,255,0.12)",
            color: isSold ? "var(--ar-success)" : "var(--ar-blue, #3a86ff)",
          }}
        >
          <TrendingUp size={18} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <div className="text-[11px] uppercase tracking-wider text-gray-400">
              {title}
            </div>
            {!isSold && (
              <span
                className="rounded-full px-1.5 py-[1px] text-[9px] font-semibold uppercase tracking-wider"
                style={{ background: "rgba(255,152,0,0.12)", color: "var(--ar-warning)" }}
                data-testid="sold-history-fallback-badge"
              >
                активные лоты
              </span>
            )}
          </div>
          <div className="mt-1 font-mono text-[16px] font-bold text-white" data-testid="sold-history-range">
            {formatRub(data.min_nzd)} – {formatRub(data.max_nzd)}
          </div>
          <div className="mt-0.5 font-mono text-[11px] text-gray-500">
            NZ${fmtNz(data.min_nzd)} – NZ${fmtNz(data.max_nzd)} · медиана NZ${fmtNz(data.median_nzd)}
          </div>
          <div className="mt-1.5 flex items-start gap-1 text-[11px] leading-snug text-gray-500">
            <Info size={11} className="mt-0.5 shrink-0" />
            <span>{hint}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function fmtNz(v) {
  if (v == null) return "—";
  return Number(v).toLocaleString("en-NZ", { maximumFractionDigits: 0 });
}
