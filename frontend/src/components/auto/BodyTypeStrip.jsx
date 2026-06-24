import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import autoApi from "../../services/autoApi";

/* Professional filled side-profile silhouettes — modelled on real car body
 * shapes. Each icon is a single filled path (body) + two wheel circles to
 * keep things crisp at small sizes. Stroke-less for a clean Turners-like look.
 * Unified 80×32 viewBox so every shape sits on the same ground line. */

const ICONS = {
  // Sedan — long bonnet, 3-box silhouette with separate boot.
  sedan: (p) => (
    <svg viewBox="0 0 80 32" {...p}>
      <path d="M3 22h74v-3c0-1-1-2-2-2l-6-1-9-7c-1-1-3-2-5-2H32c-2 0-3 1-5 2l-9 5H8c-2 0-4 1-5 3l-2 3v2z M30 17l-7 4h17v-4H30z M43 17v4h17l-8-4H43z" />
      <circle cx="20" cy="24" r="5" />
      <circle cx="60" cy="24" r="5" />
      <circle cx="20" cy="24" r="2" fill="#05070B" />
      <circle cx="60" cy="24" r="2" fill="#05070B" />
    </svg>
  ),

  // SUV — taller body, raised stance, near-vertical rear.
  suv: (p) => (
    <svg viewBox="0 0 80 32" {...p}>
      <path d="M2 21h76v-4c0-2-2-3-4-3h-3V8c0-1-1-2-3-2H22c-2 0-3 1-3 2v6h-9c-3 0-5 1-6 3l-2 2v2z M22 8h16v6H22V8z M40 8h14v6H40V8z" />
      <circle cx="20" cy="24" r="5" />
      <circle cx="60" cy="24" r="5" />
      <circle cx="20" cy="24" r="2" fill="#05070B" />
      <circle cx="60" cy="24" r="2" fill="#05070B" />
    </svg>
  ),

  // Wagon — estate body, roofline extends all the way to the rear.
  wagon: (p) => (
    <svg viewBox="0 0 80 32" {...p}>
      <path d="M2 21h76v-3c0-1-1-2-2-2h-4V9c0-1-1-2-2-2H24c-2 0-3 1-4 2l-5 7H8c-3 0-5 2-6 3v2z M24 9h14v7H24V9z M40 9h26v7H40V9z" />
      <circle cx="20" cy="24" r="5" />
      <circle cx="60" cy="24" r="5" />
      <circle cx="20" cy="24" r="2" fill="#05070B" />
      <circle cx="60" cy="24" r="2" fill="#05070B" />
    </svg>
  ),

  // Hatchback — compact body, steep sloping liftgate at the rear.
  hatchback: (p) => (
    <svg viewBox="0 0 80 32" {...p}>
      <path d="M3 21h70v-3c0-1-1-2-2-2l-5-1-7-7c-1-1-2-2-4-2H26c-2 0-4 1-5 3l-5 7H10c-3 0-5 1-6 3l-1 2z M28 11l-5 5h14v-5H28z M40 11v5h22l-5-5H40z" />
      <circle cx="20" cy="24" r="5" />
      <circle cx="58" cy="24" r="5" />
      <circle cx="20" cy="24" r="2" fill="#05070B" />
      <circle cx="58" cy="24" r="2" fill="#05070B" />
    </svg>
  ),

  // Coupe — 2-door, low sleek fastback profile.
  coupe: (p) => (
    <svg viewBox="0 0 80 32" {...p}>
      <path d="M3 22h74v-3c0-1-1-2-2-2l-4-1-11-9c-2-1-4-2-7-2H30c-2 0-4 1-5 2l-10 7H10c-3 0-5 1-7 3v5z M30 16l8-6h8c2 0 3 1 5 2l9 4H30z" />
      <circle cx="20" cy="24" r="5" />
      <circle cx="60" cy="24" r="5" />
      <circle cx="20" cy="24" r="2" fill="#05070B" />
      <circle cx="60" cy="24" r="2" fill="#05070B" />
    </svg>
  ),

  // Convertible — open top, low slung, no roof line.
  convertible: (p) => (
    <svg viewBox="0 0 80 32" {...p}>
      <path d="M3 22h74v-3c0-1-1-2-2-2l-6-1-7-3c-2-1-4-2-7-2H34c-2 0-4 1-6 2l-10 5h-8c-3 0-5 1-6 2l-1 2z" />
      {/* windshield + roll bar hint */}
      <path d="M36 12l-3 5h6v-5h-3z" />
      <path d="M50 11v6h5l-2-4-3-2z" />
      <circle cx="20" cy="24" r="5" />
      <circle cx="60" cy="24" r="5" />
      <circle cx="20" cy="24" r="2" fill="#05070B" />
      <circle cx="60" cy="24" r="2" fill="#05070B" />
    </svg>
  ),

  // Van — tall single-box body, square back, sliding door hint.
  van: (p) => (
    <svg viewBox="0 0 80 32" {...p}>
      <path d="M2 21h76v-4c0-2-2-3-4-3V7c0-1-1-2-3-2H17c-2 0-3 1-3 2v7h-3c-3 0-5 1-6 3l-3 2v2z M17 7h26v7H17V7z M45 7h21v7H45V7z" />
      <circle cx="20" cy="24" r="5" />
      <circle cx="62" cy="24" r="5" />
      <circle cx="20" cy="24" r="2" fill="#05070B" />
      <circle cx="62" cy="24" r="2" fill="#05070B" />
    </svg>
  ),

  // Utility — short cab + flat open cargo bed at the rear.
  utility: (p) => (
    <svg viewBox="0 0 80 32" {...p}>
      <path d="M2 21h76v-3c0-1-1-2-2-2H40v-4c0-2-1-3-3-3H22c-2 0-3 1-3 3v4h-7c-3 0-5 1-6 3l-3 2v0z M22 9h15v7H22V9z M40 16h36v3l-2 2H40v-5z" />
      <circle cx="20" cy="24" r="5" />
      <circle cx="60" cy="24" r="5" />
      <circle cx="20" cy="24" r="2" fill="#05070B" />
      <circle cx="60" cy="24" r="2" fill="#05070B" />
    </svg>
  ),
};

function Icon({ id, className = "" }) {
  const Cmp = ICONS[id];
  if (!Cmp) return null;
  return (
    <Cmp
      width="60"
      height="24"
      fill="currentColor"
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
