import React, { useState, useEffect } from "react";
import { getFxRate } from "../../services/autoCurrency";

/**
 * VehicleFilters — customer-facing filter form.
 *
 * Price filters accept input in ROUBLES (consistent with the rest of the
 * customer-facing UI). We convert ₽ → NZD using the cached display rate
 * before calling onApply, since the backend still expects NZD.
 */
export default function VehicleFilters({ value, onChange, onApply }) {
  const [local, setLocal] = useState(value || {});
  const [fx, setFx] = useState(null);

  useEffect(() => setLocal(value || {}), [value]);
  useEffect(() => { getFxRate().then(setFx); }, []);

  const rate = fx?.nzd_to_rub_display || 57.68;

  const update = (k, v) => {
    const next = { ...local, [k]: v === "" ? undefined : v };
    setLocal(next);
    onChange?.(next);
  };

  const submit = (e) => {
    e?.preventDefault?.();
    // Convert RUB → NZD for the backend
    const out = { ...local };
    if (local.price_from_rub) out.price_from = Math.round(Number(local.price_from_rub) / rate);
    if (local.price_to_rub)   out.price_to   = Math.round(Number(local.price_to_rub) / rate);
    delete out.price_from_rub;
    delete out.price_to_rub;
    onApply?.(out);
  };

  return (
    <form
      className="auto-card"
      onSubmit={submit}
      data-testid="vehicle-filters"
      style={{ display: "grid", gap: 10 }}
    >
      <div style={{ fontWeight: 600 }}>Фильтры</div>
      <input
        className="auto-input"
        placeholder="Поиск: марка, модель, артикул…"
        value={local.search || ""}
        onChange={(e) => update("search", e.target.value)}
        data-testid="filter-search"
      />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        <select className="auto-select" value={local.country || ""} onChange={(e) => update("country", e.target.value)} data-testid="filter-country">
          <option value="">Страна (все)</option>
          <option value="NZ">Новая Зеландия</option>
          <option value="AU">Австралия</option>
        </select>
        <select className="auto-select" value={local.listing_type || ""} onChange={(e) => update("listing_type", e.target.value)} data-testid="filter-listing-type">
          <option value="">Тип (все)</option>
          <option value="auction">Аукцион</option>
          <option value="fixed_price">Фикс. цена</option>
          <option value="inquiry_only">По запросу</option>
        </select>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        <input className="auto-input" placeholder="Марка" value={local.make || ""} onChange={(e) => update("make", e.target.value)} data-testid="filter-make" />
        <input className="auto-input" placeholder="Модель" value={local.model || ""} onChange={(e) => update("model", e.target.value)} data-testid="filter-model" />
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        <input className="auto-input" placeholder="Год от" type="number" value={local.year_from || ""} onChange={(e) => update("year_from", e.target.value)} data-testid="filter-year-from" />
        <input className="auto-input" placeholder="Год до" type="number" value={local.year_to || ""} onChange={(e) => update("year_to", e.target.value)} data-testid="filter-year-to" />
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        <input className="auto-input" placeholder="Цена от ₽" type="number" value={local.price_from_rub || ""} onChange={(e) => update("price_from_rub", e.target.value)} data-testid="filter-price-from" />
        <input className="auto-input" placeholder="Цена до ₽" type="number" value={local.price_to_rub || ""} onChange={(e) => update("price_to_rub", e.target.value)} data-testid="filter-price-to" />
      </div>
      <button type="submit" className="auto-btn" data-testid="filter-apply-btn">Применить</button>
      <button
        type="button"
        className="auto-btn auto-btn-outline"
        onClick={() => {
          setLocal({});
          onChange?.({});
          onApply?.({});
        }}
        data-testid="filter-reset-btn"
      >
        Сбросить
      </button>
    </form>
  );
}
