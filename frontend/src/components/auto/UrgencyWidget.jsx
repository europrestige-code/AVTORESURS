import React, { useEffect, useState } from "react";
import autoApi from "../../services/autoApi";
import { Eye, Heart, MessageSquare, Clock } from "lucide-react";

/* Urgency widget — countdown + live engagement stats.
 * Three signals shown:
 *   1. Countdown to auction end (if applicable)
 *   2. # users on the watchlist
 *   3. # users who expressed interest
 * All numbers are pulled from real DB counts so they remain truthful even
 * when small. We deliberately do NOT inflate ("12 человек смотрят") without
 * a real visitor-tracking pipeline — that's V2.
 */
export default function UrgencyWidget({ vehicle }) {
  const [counts, setCounts] = useState({ watchers: 0, interested: 0, offers: 0, bids: 0 });
  const [remaining, setRemaining] = useState("");

  useEffect(() => {
    if (!vehicle?.id) return;
    let cancel = false;
    autoApi
      .get(`/vehicles/${vehicle.id}/engagement`)
      .then((r) => {
        if (!cancel) setCounts(r.data || {});
      })
      .catch(() => {});
    return () => { cancel = true; };
  }, [vehicle?.id]);

  // Countdown
  useEffect(() => {
    if (!vehicle?.auction_ends_at) return;
    const target = new Date(vehicle.auction_ends_at).getTime();
    const tick = () => {
      const diff = target - Date.now();
      if (diff <= 0) {
        setRemaining("Аукцион закрыт");
        return;
      }
      const d = Math.floor(diff / 86400000);
      const h = Math.floor((diff % 86400000) / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      setRemaining(
        d > 0
          ? `${d}д ${h}ч ${m}м`
          : `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`
      );
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [vehicle?.auction_ends_at]);

  const isAuction = vehicle?.listing_type === "auction";
  const endingSoon =
    vehicle?.auction_ends_at &&
    new Date(vehicle.auction_ends_at).getTime() - Date.now() < 24 * 3600 * 1000;

  return (
    <div
      className="mb-3 rounded-2xl border border-white/10 bg-[var(--ar-card)] p-4"
      data-testid="urgency-widget"
    >
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {isAuction && (
          <Stat
            icon={<Clock size={16} className={endingSoon ? "text-[var(--ar-warning)]" : "text-blue-400"} />}
            label="До окончания"
            value={remaining || "—"}
            tone={endingSoon ? "warning" : "default"}
            testid="urgency-countdown"
          />
        )}
        <Stat
          icon={<Heart size={16} className="text-blue-400" />}
          label="В избранном"
          value={counts.watchers || 0}
          testid="urgency-watchers"
        />
        <Stat
          icon={<MessageSquare size={16} className="text-blue-400" />}
          label="Интерес"
          value={counts.interested || 0}
          testid="urgency-interested"
        />
        <Stat
          icon={<Eye size={16} className="text-blue-400" />}
          label="Предложений"
          value={counts.offers || 0}
          testid="urgency-offers"
        />
      </div>
      {endingSoon && isAuction && (
        <div
          className="mt-3 inline-flex items-center gap-2 rounded-full bg-[var(--ar-warning)]/15 px-3 py-1 text-[12px] font-bold text-[#FFB84D]"
          data-testid="urgency-ending-soon"
        >
          <Clock size={12} />
          Заканчивается сегодня
        </div>
      )}
    </div>
  );
}

function Stat({ icon, label, value, tone = "default", testid }) {
  return (
    <div data-testid={testid} className="flex flex-col gap-1">
      <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wide text-gray-400">
        {icon}
        <span>{label}</span>
      </div>
      <div className={`font-mono text-base font-bold ${tone === "warning" ? "text-[#FFB84D]" : "text-white"}`}>
        {value}
      </div>
    </div>
  );
}
