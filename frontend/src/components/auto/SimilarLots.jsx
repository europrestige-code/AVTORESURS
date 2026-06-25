import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import autoApi from "../../services/autoApi";
import { formatRub } from "../../services/autoCurrency";

/* Compact "Similar lots" widget for the vehicle detail page.
 * Backed by GET /api/auto/vehicles/{id}/similar — returns up to 4 lots
 * ranked by make + model overlap + ±3y window.
 *
 * Keeps the visual language consistent with HotCard from AutoHome but lighter
 * (smaller media, no badges) so it slots cleanly under the main detail grid.
 */
export default function SimilarLots({ vehicleId }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!vehicleId) return;
    let cancel = false;
    setLoading(true);
    autoApi
      .get(`/vehicles/${vehicleId}/similar?limit=4`)
      .then((r) => { if (!cancel) setItems(r.data?.items || []); })
      .catch(() => { if (!cancel) setItems([]); })
      .finally(() => { if (!cancel) setLoading(false); });
    return () => { cancel = true; };
  }, [vehicleId]);

  if (!loading && items.length === 0) return null;

  return (
    <section
      className="mt-8 rounded-2xl border border-white/10 bg-[var(--ar-card)] p-5"
      data-testid="similar-lots"
    >
      <div className="mb-4 flex items-end justify-between gap-3">
        <h2 className="text-xl font-bold text-white">Похожие лоты</h2>
        <Link
          to="/auto/catalog"
          className="text-sm font-semibold text-blue-400 hover:text-blue-300"
          data-testid="similar-lots-all"
        >
          Весь каталог →
        </Link>
      </div>

      {loading ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-56 animate-pulse rounded-xl border border-white/10 bg-white/[0.03]"
            />
          ))}
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {items.map((v) => (
            <SimilarCard key={v.id} v={v} />
          ))}
        </div>
      )}
    </section>
  );
}

function SimilarCard({ v }) {
  const cover =
    (v.local_images && v.local_images[0]) ||
    (v.images && v.images[0]) ||
    (v.source_images && v.source_images[0]) ||
    null;
  const initials =
    `${(v.make || "").slice(0, 1)}${(v.model || "").slice(0, 1)}`.toUpperCase() ||
    "AR";

  return (
    <Link
      to={`/auto/vehicle/${v.id}`}
      className="group block overflow-hidden rounded-xl border border-white/10 bg-[#0B0F17] transition hover:-translate-y-0.5 hover:border-blue-500/50"
      data-testid={`similar-card-${v.id}`}
    >
      <div className="relative aspect-[4/3] w-full overflow-hidden">
        {cover ? (
          <img
            src={cover}
            alt={v.title_ru}
            loading="lazy"
            className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
          />
        ) : (
          <div
            className="flex h-full w-full items-center justify-center"
            style={{
              background:
                "radial-gradient(circle at 30% 30%, rgba(0,102,255,0.35), transparent 60%), linear-gradient(135deg, #0B1424 0%, var(--ar-black) 100%)",
            }}
          >
            <span className="font-black text-blue-500/70 text-3xl tracking-tight">
              {initials}
            </span>
          </div>
        )}
        {v.country && (
          <span className="absolute right-2 top-2 inline-block rounded-md bg-black/55 px-1.5 py-0.5 text-[10px] font-bold text-white backdrop-blur-sm">
            {v.country}
          </span>
        )}
      </div>
      <div className="p-3">
        <div className="line-clamp-1 text-sm font-bold leading-tight text-white">
          {v.title_ru ||
            `${v.year || ""} ${v.make || ""} ${v.model || ""}`.trim()}
        </div>
        <div className="mt-0.5 line-clamp-1 text-[11px] text-gray-400">
          {v.year ? `${v.year} · ` : ""}
          {v.mileage_km != null
            ? `${Number(v.mileage_km).toLocaleString("ru-RU")} км`
            : "—"}
        </div>
        <div className="mt-2 font-mono text-sm font-bold text-white">
          {v.current_price_nzd ? (
            formatRub(v.current_price_nzd)
          ) : (
            <span className="text-gray-400">По запросу</span>
          )}
        </div>
      </div>
    </Link>
  );
}
