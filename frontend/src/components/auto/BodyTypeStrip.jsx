import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import autoApi from "../../services/autoApi";

/* Eight minimalist body-shape silhouettes — drawn from the same family so
 * they share line weight, baseline, and bounding box. They're inline SVG
 * (no external dependency) and inherit `currentColor` so the active/idle
 * state can be themed via Tailwind text colour. */

const ICONS = {
  convertible: (p) => (
    <svg viewBox="0 0 64 28" {...p}>
      <path d="M8 21h48" />
      <path d="M10 21l4-7c1-2 3-3 5-3h22c2 0 4 1 5 3l4 7" />
      <circle cx="18" cy="22" r="3" />
      <circle cx="46" cy="22" r="3" />
      <path d="M19 11l4-3h12l4 3" strokeDasharray="2 2" />
    </svg>
  ),
  wagon: (p) => (
    <svg viewBox="0 0 64 28" {...p}>
      <path d="M6 21h52" />
      <path d="M8 21V14l8-7h32l8 7v7" />
      <path d="M16 14h40" />
      <path d="M30 7v7" />
      <circle cx="18" cy="22" r="3" />
      <circle cx="46" cy="22" r="3" />
    </svg>
  ),
  utility: (p) => (
    <svg viewBox="0 0 64 28" {...p}>
      <path d="M6 21h52" />
      <path d="M8 21v-7l5-7h14l3 7h28v7" />
      <path d="M13 14h17" />
      <circle cx="18" cy="22" r="3" />
      <circle cx="46" cy="22" r="3" />
    </svg>
  ),
  coupe: (p) => (
    <svg viewBox="0 0 64 28" {...p}>
      <path d="M6 21h52" />
      <path d="M8 21l3-7c1-2 3-3 5-3l8-6c2-1 4-1 6 0l14 9h12v7" />
      <circle cx="18" cy="22" r="3" />
      <circle cx="46" cy="22" r="3" />
    </svg>
  ),
  hatchback: (p) => (
    <svg viewBox="0 0 64 28" {...p}>
      <path d="M6 21h52" />
      <path d="M8 21v-7l6-7h20l12 7h10v7" />
      <path d="M14 14h28" />
      <circle cx="18" cy="22" r="3" />
      <circle cx="46" cy="22" r="3" />
    </svg>
  ),
  van: (p) => (
    <svg viewBox="0 0 64 28" {...p}>
      <path d="M6 21h52" />
      <path d="M8 21V8h36l10 6v7" />
      <path d="M14 12h26v6H14z" />
      <circle cx="18" cy="22" r="3" />
      <circle cx="46" cy="22" r="3" />
    </svg>
  ),
  sedan: (p) => (
    <svg viewBox="0 0 64 28" {...p}>
      <path d="M6 21h52" />
      <path d="M8 21l4-7 8-4h20l10 4 6 7" />
      <path d="M16 14h28" />
      <circle cx="18" cy="22" r="3" />
      <circle cx="46" cy="22" r="3" />
    </svg>
  ),
  suv: (p) => (
    <svg viewBox="0 0 64 28" {...p}>
      <path d="M6 21h52" />
      <path d="M8 21V12l6-5h32l8 5v9" />
      <path d="M14 12h40" />
      <path d="M28 7v5" />
      <circle cx="18" cy="22" r="3.2" />
      <circle cx="46" cy="22" r="3.2" />
    </svg>
  ),
};

function Icon({ id, className = "" }) {
  const Cmp = ICONS[id];
  if (!Cmp) return null;
  return (
    <Cmp
      width="56"
      height="24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    />
  );
}

export default function BodyTypeStrip({
  activeKey = null,
  onSelect = null,
  className = "",
}) {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        const r = await autoApi.get("/body-type-counts");
        if (!cancel) setItems(r.data?.items || []);
      } catch {
        if (!cancel) setItems([]);
      } finally {
        if (!cancel) setLoading(false);
      }
    })();
    return () => { cancel = true; };
  }, []);

  if (loading || items.length === 0) {
    return (
      <div className={`flex gap-2 overflow-x-auto px-1 py-2 ${className}`} aria-hidden>
        {Array.from({ length: 8 }).map((_, i) => (
          <div
            key={i}
            className="h-[68px] w-[110px] shrink-0 animate-pulse rounded-xl border border-white/10 bg-white/5"
          />
        ))}
      </div>
    );
  }

  const handle = (key) => {
    if (onSelect) { onSelect(key); return; }
    navigate(`/auto/catalog?body_type=${encodeURIComponent(key)}`);
  };

  return (
    <div
      className={`flex gap-2 overflow-x-auto px-1 py-2 sm:gap-3 ${className}`}
      data-testid="body-type-strip"
      role="tablist"
    >
      {items.map((b) => {
        const active = activeKey && activeKey.toLowerCase() === b.key;
        return (
          <button
            key={b.key}
            type="button"
            onClick={() => handle(b.key)}
            role="tab"
            aria-selected={!!active}
            data-testid={`body-type-${b.key}`}
            className={[
              "group flex shrink-0 flex-col items-center justify-center gap-1 rounded-xl border px-4 py-2 transition",
              "min-w-[110px]",
              active
                ? "border-blue-500/70 bg-blue-500/10 text-white shadow-[0_0_0_3px_rgba(0,102,255,0.15)]"
                : "border-white/10 bg-[#0D111A] text-gray-300 hover:border-blue-500/40 hover:bg-white/[0.05] hover:text-white",
            ].join(" ")}
          >
            <Icon id={b.key} className={active ? "text-blue-400" : "text-gray-300 group-hover:text-blue-400"} />
            <div className="flex items-baseline gap-1">
              <span className="text-xs font-semibold">{b.label_ru}</span>
              <span className="text-[11px] font-mono text-gray-500">
                ({(b.count || 0).toLocaleString("ru-RU")})
              </span>
            </div>
          </button>
        );
      })}
    </div>
  );
}
