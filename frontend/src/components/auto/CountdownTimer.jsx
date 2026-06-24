import React, { useEffect, useState } from "react";

/**
 * Live countdown to a target ISO timestamp. Updates every second.
 * Shows "Окончен" once the target has passed.
 */
export default function CountdownTimer({ target, compact = false, testid = "countdown" }) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (!target) return;
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [target]);

  if (!target) return null;
  const end = new Date(target).getTime();
  const ms = end - now;

  if (ms <= 0) {
    return (
      <span className="auto-badge auto-badge-danger" data-testid={`${testid}-ended`}>
        Аукцион окончен
      </span>
    );
  }

  const totalSec = Math.floor(ms / 1000);
  const d = Math.floor(totalSec / 86400);
  const h = Math.floor((totalSec % 86400) / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;

  const urgent = ms < 1000 * 60 * 60; // < 1 hour
  const cls = urgent ? "auto-badge-danger" : ms < 1000 * 60 * 60 * 24 ? "auto-badge-warning" : "auto-badge-primary";

  if (compact) {
    return (
      <span className={`auto-badge ${cls}`} data-testid={testid}>
        {d > 0 ? `${d}д ` : ""}{String(h).padStart(2, "0")}:{String(m).padStart(2, "0")}:{String(s).padStart(2, "0")}
      </span>
    );
  }

  return (
    <div data-testid={testid} style={{ display: "flex", gap: 8, alignItems: "center" }}>
      <span className={`auto-badge ${cls}`}>До конца аукциона:</span>
      <span style={{ fontVariantNumeric: "tabular-nums", fontWeight: 700, fontSize: 16 }}>
        {d > 0 ? `${d}д ` : ""}{String(h).padStart(2, "0")}:{String(m).padStart(2, "0")}:{String(s).padStart(2, "0")}
      </span>
    </div>
  );
}
