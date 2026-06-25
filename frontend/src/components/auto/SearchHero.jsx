import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import autoApi from "../../services/autoApi";
import { Car, CreditCard, Wrench, Recycle, CalendarDays, Cog, Bike, Truck, Tractor } from "lucide-react";
import BodyTypeStrip from "./BodyTypeStrip";

const CATEGORIES = [
  { key: "auctions", label: "Аукционы",      route: "/auto/auctions-list", Icon: Car },
  { key: "buynow",   label: "Купить сейчас", route: "/auto/buynow",        Icon: CreditCard },
  { key: "damaged",  label: "Повреждённые",  route: "/auto/damaged",       Icon: Wrench },
  { key: "eol",      label: "End of Life",   route: "/auto/end-of-life",   Icon: Recycle },
  { key: "calendar", label: "Календарь",     route: "/auto/auctions",      Icon: CalendarDays },
  { key: "moto",     label: "Мотоциклы",     route: "/auto/motorcycles",   Icon: Bike },
  { key: "trucks",   label: "Грузовики",     route: "/auto/trucks",        Icon: Truck },
  { key: "machinery",label: "Спецтехника",   route: "/auto/machinery",     Icon: Tractor },
  { key: "parts",    label: "Запчасти",      route: "/auto/parts",         Icon: Cog,  soon: true },
];

const CURRENT_YEAR = new Date().getFullYear();
const YEAR_OPTIONS = Array.from({ length: 35 }, (_, i) => CURRENT_YEAR - i);

export default function SearchHero({ variant = "home", activeBodyType = null }) {
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [make, setMake] = useState("");
  const [model, setModel] = useState("");
  const [yearFrom, setYearFrom] = useState("");
  const [yearTo, setYearTo] = useState("");

  useEffect(() => {
    autoApi.get("/catalog-summary").then((r) => setSummary(r.data)).catch(() => setSummary(null));
  }, []);

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
      {/* Body-type filter strip — single source of truth. Replaces the
       *  previous in-hero chips (was duplicated with BodyTypeStrip). */}
      <BodyTypeStrip
        activeKey={activeBodyType}
        onSelect={(key) => goWith({ body_type: key })}
        className="mb-4"
      />

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
        {CATEGORIES.map((c) => {
          const Icon = c.Icon;
          return (
            <button
              key={c.key}
              type="button"
              onClick={() => {
                if (c.soon) return;
                if (c.route) navigate(c.route);
                else if (c.filter) goWith(c.filter);
              }}
              className="auto-cat-tile"
              disabled={c.soon}
              data-testid={`search-cat-${c.key}`}
            >
              <span className="auto-cat-tile__icon" aria-hidden>
                <Icon size={28} strokeWidth={1.7} />
              </span>
              <span className="auto-cat-tile__label">{c.label}</span>
              {c.soon && <span className="auto-badge">скоро</span>}
            </button>
          );
        })}
      </div>
    </section>
  );
}
