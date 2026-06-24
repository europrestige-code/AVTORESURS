import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import autoApi from "../../services/autoApi";

const BODY_TYPE_LABEL = {
  Кабриолет: "Кабриолет",
  Универсал: "Универсал",
  Пикап: "Пикап",
  Купе: "Купе",
  Хэтчбек: "Хэтчбек",
  Фургон: "Фургон",
  Седан: "Седан",
  Кроссовер: "Кроссовер",
  Внедорожник: "Внедорожник",
};

const CATEGORIES = [
  { key: "auction", label: "Аукционы", filter: { listing_type: "auction" }, icon: "🏁" },
  { key: "trucks", label: "Грузовики и техника", filter: { body_type: "Грузовик" }, icon: "🚚", soon: true },
  { key: "damaged", label: "Повреждённые / EOL", filter: { damage_type: "Затопление" }, icon: "🛠️" },
  { key: "boats", label: "Лодки и катера", filter: { body_type: "Лодка" }, icon: "⛵", soon: true },
  { key: "moto", label: "Мотоциклы", filter: { body_type: "Мотоцикл" }, icon: "🏍️", soon: true },
  { key: "general", label: "Общая техника", filter: { body_type: "Общая" }, icon: "📦", soon: true },
  { key: "vans", label: "Автобусы и автодома", filter: { body_type: "Фургон" }, icon: "🚐" },
];

const CURRENT_YEAR = new Date().getFullYear();
const YEAR_OPTIONS = Array.from({ length: 35 }, (_, i) => CURRENT_YEAR - i);

export default function SearchHero({ variant = "home" }) {
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [make, setMake] = useState("");
  const [model, setModel] = useState("");
  const [yearFrom, setYearFrom] = useState("");
  const [yearTo, setYearTo] = useState("");

  useEffect(() => {
    autoApi.get("/catalog-summary").then((r) => setSummary(r.data)).catch(() => setSummary(null));
  }, []);

  const total = summary?.total ?? 0;
  const bodyTypes = useMemo(() => summary?.body_types || [], [summary]);
  const makes = useMemo(() => summary?.makes || [], [summary]);
  const modelsForMake = useMemo(() => {
    if (!make || !summary) return [];
    return summary.models_by_make?.[make] || [];
  }, [make, summary]);

  const goWith = (extra) => {
    const params = new URLSearchParams();
    if (make) params.set("make", make);
    if (model) params.set("model", model);
    if (yearFrom) params.set("year_from", yearFrom);
    if (yearTo) params.set("year_to", yearTo);
    if (extra) Object.entries(extra).forEach(([k, v]) => v && params.set(k, v));
    navigate(`/auto/catalog?${params.toString()}`);
  };

  return (
    <section className={`auto-card auto-search-hero ${variant === "catalog" ? "compact" : ""}`} data-testid="search-hero">
      <div className="auto-search-hero__title">
        <h2 style={{ fontSize: variant === "home" ? 28 : 22, margin: 0, fontWeight: 800, letterSpacing: "-0.01em" }}>
          Найдите авто среди{" "}
          <span style={{ color: "var(--auto-primary)" }} data-testid="search-hero-total">
            {total.toLocaleString("ru-RU")}
          </span>{" "}
          в наличии
        </h2>
        <p className="auto-muted" style={{ marginTop: 6 }}>
          Помощник <b style={{ color: "var(--auto-text)" }}>Тина</b> подберёт автомобиль из Turners, Manheim и Pickles.
        </p>
      </div>

      {/* Body-type chips */}
      <div className="auto-search-hero__chips" data-testid="search-body-chips">
        {bodyTypes.length === 0 ? (
          <span className="auto-muted" style={{ fontSize: 13 }}>Загружаем категории…</span>
        ) : (
          bodyTypes.map((b) => (
            <button
              key={b.value}
              type="button"
              className="auto-badge auto-badge-primary auto-chip"
              onClick={() => goWith({ body_type: b.value })}
              data-testid={`search-chip-${b.value}`}
            >
              {BODY_TYPE_LABEL[b.value] || b.value} <span style={{ opacity: 0.7 }}>({b.count})</span>
            </button>
          ))
        )}
      </div>

      {/* Make / Model / Year selectors */}
      <div className="auto-search-hero__row">
        <select
          className="auto-select"
          value={make}
          onChange={(e) => { setMake(e.target.value); setModel(""); }}
          data-testid="search-make"
        >
          <option value="">Марка (все)</option>
          {makes.map((m) => (
            <option key={m.value} value={m.value}>
              {m.value} ({m.count})
            </option>
          ))}
        </select>
        <select
          className="auto-select"
          value={model}
          onChange={(e) => setModel(e.target.value)}
          disabled={!make}
          data-testid="search-model"
        >
          <option value="">Модель</option>
          {modelsForMake.map((m) => (
            <option key={m.value} value={m.value}>
              {m.value} ({m.count})
            </option>
          ))}
        </select>
        <select className="auto-select" value={yearFrom} onChange={(e) => setYearFrom(e.target.value)} data-testid="search-year-from">
          <option value="">Год от</option>
          {YEAR_OPTIONS.map((y) => <option key={y} value={y}>{y}</option>)}
        </select>
        <select className="auto-select" value={yearTo} onChange={(e) => setYearTo(e.target.value)} data-testid="search-year-to">
          <option value="">Год до</option>
          {YEAR_OPTIONS.map((y) => <option key={y} value={y}>{y}</option>)}
        </select>
        <button type="button" onClick={() => goWith()} className="auto-btn" data-testid="search-submit">
          Найти
        </button>
      </div>

      {/* Category tiles */}
      <div className="auto-search-hero__cats" data-testid="search-categories">
        {CATEGORIES.map((c) => (
          <button
            key={c.key}
            type="button"
            onClick={() => !c.soon && goWith(c.filter)}
            className="auto-cat-tile"
            disabled={c.soon}
            data-testid={`search-cat-${c.key}`}
          >
            <span className="auto-cat-tile__icon" aria-hidden>{c.icon}</span>
            <span className="auto-cat-tile__label">{c.label}</span>
            {c.soon && <span className="auto-badge">скоро</span>}
          </button>
        ))}
      </div>
    </section>
  );
}
