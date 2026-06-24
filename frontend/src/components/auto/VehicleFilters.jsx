import React, { useState, useEffect } from "react";

export default function VehicleFilters({ value, onChange, onApply }) {
  const [local, setLocal] = useState(value || {});

  useEffect(() => setLocal(value || {}), [value]);

  const update = (k, v) => {
    const next = { ...local, [k]: v === "" ? undefined : v };
    setLocal(next);
    onChange?.(next);
  };

  return (
    <form
      className="auto-card"
      onSubmit={(e) => {
        e.preventDefault();
        onApply?.(local);
      }}
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
        <input className="auto-input" placeholder="Цена от NZ$" type="number" value={local.price_from || ""} onChange={(e) => update("price_from", e.target.value)} data-testid="filter-price-from" />
        <input className="auto-input" placeholder="Цена до NZ$" type="number" value={local.price_to || ""} onChange={(e) => update("price_to", e.target.value)} data-testid="filter-price-to" />
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
