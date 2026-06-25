import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Clock } from "lucide-react";
import autoApi from "../../services/autoApi";
import { formatRub } from "../../services/autoCurrency";
import { fmtPrice } from "./VehicleCard";

/* Ending-soon carousel — horizontal strip of auctions that close in the
 * next 72h. Each card shows the live countdown. Sits between the body-type
 * strip and "Хиты дня" — strongest urgency signal we have.
 */
export default function EndingSoonCarousel() {
  const [items, setItems] = useState([]);
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    let cancel = false;
    autoApi
      .get("/ending-soon?limit=8")
      .then((r) => { if (!cancel) setItems(r.data?.items || []); })
      .catch(() => {});
    return () => { cancel = true; };
  }, []);

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  if (items.length === 0) return null;

  return (
    <section
      className="mx-auto mt-8 max-w-7xl px-6"
      data-testid="ending-soon-carousel"
    >
      <div className="mb-4 flex items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold text-white">Заканчиваются сегодня</h2>
          <p className="mt-1 text-sm text-gray-400">
            Аукционы, которые закроются в ближайшие 72 часа
          </p>
        </div>
        <Link
          to="/auto/auctions"
          className="text-sm font-semibold text-blue-400 hover:text-blue-300"
          data-testid="ending-soon-all"
        >
          Все аукционы →
        </Link>
      </div>

      <div className="flex gap-3 overflow-x-auto pb-2 sm:gap-4">
        {items.map((v) => (
          <EndingCard key={v.id} v={v} now={now} />
        ))}
      </div>
    </section>
  );
}

function EndingCard({ v, now }) {
  const end = v.auction_ends_at ? new Date(v.auction_ends_at).getTime() : 0;
  const diff = end - now;
  const lessThanDay = diff > 0 && diff < 24 * 3600 * 1000;
  const closed = diff <= 0;

  let countdown = "—";
  if (!closed && end) {
    const h = Math.floor(diff / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    countdown = h >= 24
      ? `${Math.floor(h / 24)}д ${h % 24}ч`
      : `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  } else if (closed) {
    countdown = "закрыт";
  }

  const cover =
    (v.local_images && v.local_images[0]) ||
    (v.images && v.images[0]) ||
    (v.source_images && v.source_images[0]) ||
    null;
  const price = v.current_price_nzd || v.starting_price_nzd || 0;

  return (
    <Link
      to={`/auto/vehicle/${v.id}`}
      className="group relative block w-[260px] shrink-0 overflow-hidden rounded-xl border border-white/10 bg-[#0B0F17] transition hover:-translate-y-0.5 hover:border-blue-500/50"
      data-testid={`ending-card-${v.id}`}
    >
      <div className="relative aspect-[4/3] w-full overflow-hidden">
        {cover ? (
          <img
            src={cover}
            alt={v.title_ru || v.make}
            loading="lazy"
            className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-[#0B1424] text-blue-500/70">
            <span className="text-3xl font-black tracking-tight">{(v.make || "AR").slice(0, 2).toUpperCase()}</span>
          </div>
        )}
        <span
          className={`absolute left-2 top-2 inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-bold ${
            lessThanDay ? "bg-[var(--ar-danger)] text-white" : "bg-black/65 text-white"
          }`}
        >
          <Clock size={10} />
          {countdown}
        </span>
      </div>
      <div className="p-3">
        <div className="line-clamp-1 text-sm font-bold text-white">
          {v.title_ru || `${v.year || ""} ${v.make || ""} ${v.model || ""}`.trim()}
        </div>
        <div className="mt-0.5 line-clamp-1 text-[11px] text-gray-400">
          {v.year ? `${v.year} · ` : ""}{v.mileage_km != null ? `${Number(v.mileage_km).toLocaleString("ru-RU")} км` : "—"}
        </div>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="font-mono text-sm font-bold text-white">{price ? fmtPrice(price) : "—"}</span>
          {price > 0 && (
            <span className="text-[11px] text-gray-500">{formatRub(price)}</span>
          )}
        </div>
      </div>
    </Link>
  );
}
