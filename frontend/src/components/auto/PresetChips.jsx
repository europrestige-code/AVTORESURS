import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Truck } from "lucide-react";
import autoApi from "../../services/autoApi";

/**
 * Preset filter chips — one-tap access to popular narrow slices of stock
 * (vans + pickups today; more chips can be added server-side via
 * PRESET_FILTERS in auto_routes.py). Renders under BodyTypeStrip on
 * Home / Catalog so buyers can jump straight to Hiace / Transit /
 * Sprinter / Hilux / Ranger / Navara etc. without hunting via the
 * generic filters.
 */
const ICONS = {
  van_pickup: Truck,
};

export default function PresetChips({ activeKey = null, onSelect = null, className = "" }) {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        const r = await autoApi.get("/preset-counts");
        if (!cancel) setItems(r.data?.items || []);
      } catch {
        if (!cancel) setItems([]);
      } finally {
        if (!cancel) setLoading(false);
      }
    })();
    return () => { cancel = true; };
  }, []);

  if (loading || items.length === 0) return null;

  const handle = (chip) => {
    if (onSelect) {
      onSelect(chip);
      return;
    }
    navigate(`/auto/catalog?search=${encodeURIComponent(chip.regex)}&preset=${chip.key}`);
  };

  return (
    <div
      className={`flex gap-2 overflow-x-auto px-1 py-1 ${className}`}
      data-testid="preset-chips"
      role="tablist"
    >
      {items.map((chip) => {
        const Icon = ICONS[chip.key] || Truck;
        const active = activeKey === chip.key;
        return (
          <button
            key={chip.key}
            type="button"
            onClick={() => handle(chip)}
            role="tab"
            aria-selected={!!active}
            data-testid={`preset-chip-${chip.key}`}
            className={[
              "group inline-flex shrink-0 items-center gap-2 rounded-full border px-3.5 py-1.5 transition",
              active
                ? "border-blue-500/70 bg-blue-500/10 text-white shadow-[0_0_0_3px_rgba(0,102,255,0.15)]"
                : "border-white/10 bg-[var(--ar-card)] text-gray-300 hover:border-blue-500/40 hover:bg-white/[0.05] hover:text-white",
            ].join(" ")}
          >
            <Icon size={14} className={active ? "text-blue-400" : "text-gray-400 group-hover:text-blue-400"} />
            <span className="text-[13px] font-semibold">{chip.label_ru}</span>
            <span className="font-mono text-[11px] text-gray-500">
              {(chip.count || 0).toLocaleString("ru-RU")}
            </span>
          </button>
        );
      })}
    </div>
  );
}
