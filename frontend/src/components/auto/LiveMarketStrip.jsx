import React, { useEffect, useState } from "react";
import autoApi from "../../services/autoApi";
import { TrendingUp, Gavel, AlertTriangle, ShoppingCart, Clock, Users } from "lucide-react";

/* Live market strip — sits on the homepage just under the hero.
 * Shows real DB counts (auto_vehicles + auto_interests) so the site feels
 * like a live market, not a static catalogue. Updates on every page load
 * (cheap aggregate query on the backend).
 */
export default function LiveMarketStrip() {
  const [data, setData] = useState(null);

  useEffect(() => {
    let cancel = false;
    autoApi
      .get("/market-summary")
      .then((r) => { if (!cancel) setData(r.data); })
      .catch(() => {});
    return () => { cancel = true; };
  }, []);

  if (!data) return null;
  const fmt = (n) => Number(n || 0).toLocaleString("ru-RU");

  const items = [
    { icon: <TrendingUp size={16} />, label: "Доступно авто", val: fmt(data.available) },
    { icon: <Gavel size={16} />, label: "Аукционов", val: fmt(data.auctions_total) },
    { icon: <Clock size={16} className="text-[#FFB84D]" />, label: "Заканчиваются", val: fmt(data.ending_soon), warn: true },
    { icon: <AlertTriangle size={16} className="text-[#FF7A6F]" />, label: "Повреждённых", val: fmt(data.damaged) },
    { icon: <ShoppingCart size={16} />, label: "Купить сейчас", val: fmt(data.buynow) },
    { icon: <Users size={16} />, label: "Заявок сегодня", val: fmt(data.interests_today) },
  ];

  return (
    <section
      className="mx-auto mt-6 max-w-7xl rounded-2xl border border-white/10 bg-[#0D111A] p-3 sm:p-4"
      data-testid="live-market-strip"
    >
      <div className="flex gap-3 overflow-x-auto sm:grid sm:grid-cols-3 sm:gap-4 lg:grid-cols-6">
        {items.map((i) => (
          <div
            key={i.label}
            className="flex min-w-[150px] items-center gap-3 rounded-xl bg-white/[0.03] px-3 py-2 sm:min-w-0"
            data-testid={`market-stat-${i.label}`}
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-500/15 text-blue-400">
              {i.icon}
            </div>
            <div className="min-w-0">
              <div className={`font-mono text-base font-bold ${i.warn ? "text-[#FFB84D]" : "text-white"}`}>
                {i.val}
              </div>
              <div className="truncate text-[11px] uppercase tracking-wide text-gray-400">
                {i.label}
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
