import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import autoApi from "../../services/autoApi";

/* Professional car body icons from Material Design Icons (Pictogrammers,
 * Apache-2.0). These are real-world, consistent automotive silhouettes
 * (sedan, hatchback, wagon, SUV, ute, sports coupe, convertible, van) —
 * the same family used on Toyota / Mazda / NRMA configurators. Embedded
 * inline so we don't pull a runtime CDN. */
const ICONS = {
  sedan: (
    <path fill="currentColor" d="M3 6h13l3 4h2c1.11 0 2 .89 2 2v3h-2a3 3 0 0 1-3 3 3 3 0 0 1-3-3H9a3 3 0 0 1-3 3 3 3 0 0 1-3-3H1V8c0-1.11.89-2 2-2m-.5 1.5V10h8V7.5zm9.5 0V10h5.14l-1.89-2.5zm-6 6A1.5 1.5 0 0 0 4.5 15 1.5 1.5 0 0 0 6 16.5 1.5 1.5 0 0 0 7.5 15 1.5 1.5 0 0 0 6 13.5m12 0a1.5 1.5 0 0 0-1.5 1.5 1.5 1.5 0 0 0 1.5 1.5 1.5 1.5 0 0 0 1.5-1.5 1.5 1.5 0 0 0-1.5-1.5"/>
  ),
  hatchback: (
    <path fill="currentColor" d="M16 6H6l-5 6v3h2a3 3 0 0 0 3 3 3 3 0 0 0 3-3h6a3 3 0 0 0 3 3 3 3 0 0 0 3-3h2v-3c0-1.11-.89-2-2-2h-2zM6.5 7.5h4V10h-6zm5.5 0h3.5l1.96 2.5H12zm-6 6A1.5 1.5 0 0 1 7.5 15 1.5 1.5 0 0 1 6 16.5 1.5 1.5 0 0 1 4.5 15 1.5 1.5 0 0 1 6 13.5m12 0a1.5 1.5 0 0 1 1.5 1.5 1.5 1.5 0 0 1-1.5 1.5 1.5 1.5 0 0 1-1.5-1.5 1.5 1.5 0 0 1 1.5-1.5"/>
  ),
  wagon: (
    <path fill="currentColor" d="M3 6h17v4h1c1.11 0 2 .89 2 2v3h-2a3 3 0 0 1-3 3 3 3 0 0 1-3-3H9a3 3 0 0 1-3 3 3 3 0 0 1-3-3H1V8c0-1.11.89-2 2-2m-.5 1.5V10h8V7.5zm9.5 0V10h6V7.5zm-6 6A1.5 1.5 0 0 0 4.5 15 1.5 1.5 0 0 0 6 16.5 1.5 1.5 0 0 0 7.5 15 1.5 1.5 0 0 0 6 13.5m12 0a1.5 1.5 0 0 0-1.5 1.5 1.5 1.5 0 0 0 1.5 1.5 1.5 1.5 0 0 0 1.5-1.5 1.5 1.5 0 0 0-1.5-1.5"/>
  ),
  utility: (
    <path fill="currentColor" d="M16 6h-5.5v4H1v5h2a3 3 0 0 0 3 3 3 3 0 0 0 3-3h6a3 3 0 0 0 3 3 3 3 0 0 0 3-3h2v-3c0-1.11-.89-2-2-2h-2zm-4 1.5h3.5l1.96 2.5H12zm-6 6A1.5 1.5 0 0 1 7.5 15 1.5 1.5 0 0 1 6 16.5 1.5 1.5 0 0 1 4.5 15 1.5 1.5 0 0 1 6 13.5m12 0a1.5 1.5 0 0 1 1.5 1.5 1.5 1.5 0 0 1-1.5 1.5 1.5 1.5 0 0 1-1.5-1.5 1.5 1.5 0 0 1 1.5-1.5"/>
  ),
  coupe: (
    <path fill="currentColor" d="M12 8.5H7L4 11H3c-1.11 0-2 .89-2 2v3h2.17c.43 1.2 1.56 2 2.83 2s2.4-.8 2.82-2h6.35c.43 1.2 1.56 2 2.83 2s2.4-.8 2.82-2H23v-1c0-1.11-1.03-1.47-2-2zM5.25 12l2.25-2h4l4 2zM6 13.5A1.5 1.5 0 0 1 7.5 15 1.5 1.5 0 0 1 6 16.5 1.5 1.5 0 0 1 4.5 15 1.5 1.5 0 0 1 6 13.5m12 0a1.5 1.5 0 0 1 1.5 1.5 1.5 1.5 0 0 1-1.5 1.5 1.5 1.5 0 0 1-1.5-1.5 1.5 1.5 0 0 1 1.5-1.5"/>
  ),
  convertible: (
    <path fill="currentColor" d="m16 6l-1 .75L17.5 10h-4V8.5H12V10H3c-1.11 0-2 .89-2 2v3h2a3 3 0 0 0 3 3 3 3 0 0 0 3-3h6a3 3 0 0 0 3 3 3 3 0 0 0 3-3h2v-3c0-1.11-.89-2-2-2h-2zM6 13.5A1.5 1.5 0 0 1 7.5 15 1.5 1.5 0 0 1 6 16.5 1.5 1.5 0 0 1 4.5 15 1.5 1.5 0 0 1 6 13.5m12 0a1.5 1.5 0 0 1 1.5 1.5 1.5 1.5 0 0 1-1.5 1.5 1.5 1.5 0 0 1-1.5-1.5 1.5 1.5 0 0 1 1.5-1.5"/>
  ),
  van: (
    <path fill="currentColor" d="M3 7c-1.11 0-2 .89-2 2v8h2a3 3 0 0 0 3 3 3 3 0 0 0 3-3h6a3 3 0 0 0 3 3 3 3 0 0 0 3-3h2v-4c0-1.11-.89-2-2-2l-3-4zm12 1.5h2.5l1.96 2.5H15zm-9 7A1.5 1.5 0 0 1 7.5 17 1.5 1.5 0 0 1 6 18.5 1.5 1.5 0 0 1 4.5 17 1.5 1.5 0 0 1 6 15.5m12 0a1.5 1.5 0 0 1 1.5 1.5 1.5 1.5 0 0 1-1.5 1.5 1.5 1.5 0 0 1-1.5-1.5 1.5 1.5 0 0 1 1.5-1.5"/>
  ),
  suv: (
    <path fill="currentColor" d="M5 4c-1.11 0-2 .89-2 2v2H1v5h2a3 3 0 0 0 3 3 3 3 0 0 0 3-3h6a3 3 0 0 0 3 3 3 3 0 0 0 3-3h2v-3c0-1.11-.89-2-2-2h-3l-2-4zm.5 1.5h6V8h-6zm7.5 0h4l1.25 2.5H13zM6 12a1.5 1.5 0 0 1 1.5 1.5A1.5 1.5 0 0 1 6 15a1.5 1.5 0 0 1-1.5-1.5A1.5 1.5 0 0 1 6 12m12 0a1.5 1.5 0 0 1 1.5 1.5A1.5 1.5 0 0 1 18 15a1.5 1.5 0 0 1-1.5-1.5A1.5 1.5 0 0 1 18 12"/>
  ),
  motorcycle: (
    <path fill="currentColor" d="M19 7.82V6.69l-2-.66V5a1 1 0 0 0-1-1h-2v2h1v2.31L12.16 12H8.07A3 3 0 1 0 8 14h6.91l1.5-3.45A2.99 2.99 0 0 0 19 15a3 3 0 0 0 0-6c-.21 0-.4 0-.6.07L19 7.82M5 15a1 1 0 1 1 1-1a1 1 0 0 1-1 1m14-2a1 1 0 1 1-1-1a1 1 0 0 1 1 1"/>
  ),
  truck: (
    <path fill="currentColor" d="M20 8h-3V4H3c-1.11 0-2 .89-2 2v11h2a3 3 0 0 0 6 0h6a3 3 0 0 0 6 0h2v-5l-3-4M6 18.5A1.5 1.5 0 0 1 4.5 17A1.5 1.5 0 0 1 6 15.5A1.5 1.5 0 0 1 7.5 17A1.5 1.5 0 0 1 6 18.5m13.5-9l1.96 2.5H17V9.5h2.5M18 18.5a1.5 1.5 0 0 1-1.5-1.5a1.5 1.5 0 0 1 1.5-1.5a1.5 1.5 0 0 1 1.5 1.5a1.5 1.5 0 0 1-1.5 1.5z"/>
  ),
  machinery: (
    <path fill="currentColor" d="M20 15.27V12h-1V8h-2v4h-2V8h-1l-3 5v2H8.6c-.6-.6-1.6-1-2.6-1c-2.2 0-4 1.8-4 4s1.8 4 4 4c1 0 2-.4 2.6-1H22v-3l-2-1.73M6 19c-1.1 0-2-.9-2-2s.9-2 2-2s2 .9 2 2s-.9 2-2 2m11-1c-.6-.6-1.6-1-2.6-1H10v-2h1.13L13 12h2v4h5v1l-3 1z"/>
  ),
};

function Icon({ id, className = "" }) {
  const path = ICONS[id];
  if (!path) return null;
  return (
    <svg
      width="40"
      height="40"
      viewBox="0 0 24 24"
      className={className}
      aria-hidden
    >
      {path}
    </svg>
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
                : "border-white/10 bg-[var(--ar-card)] text-gray-300 hover:border-blue-500/40 hover:bg-white/[0.05] hover:text-white",
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
