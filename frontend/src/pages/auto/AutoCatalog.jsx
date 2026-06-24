import React, { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import autoApi from "../../services/autoApi";
import VehicleCard from "../../components/auto/VehicleCard";
import VehicleFilters from "../../components/auto/VehicleFilters";
import SearchHero from "../../components/auto/SearchHero";

const LIMIT = 12;

const FILTER_KEYS = [
  "country", "source", "make", "model", "year_from", "year_to",
  "price_from", "price_to", "mileage_from", "mileage_to",
  "condition", "damage_type", "listing_type", "status", "search", "body_type",
];

export default function AutoCatalog() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [searchParams, setSearchParams] = useSearchParams();
  const [filters, setFilters] = useState(() => {
    const init = {};
    FILTER_KEYS.forEach((k) => {
      const v = searchParams.get(k);
      if (v) init[k] = v;
    });
    return init;
  });
  const [loading, setLoading] = useState(true);

  // Re-sync filters when the URL changes (e.g. via SearchHero navigation)
  useEffect(() => {
    const next = {};
    FILTER_KEYS.forEach((k) => {
      const v = searchParams.get(k);
      if (v) next[k] = v;
    });
    setFilters(next);
    setOffset(0);
  }, [searchParams]);

  const load = useCallback(async (currentFilters, currentOffset) => {
    setLoading(true);
    try {
      const params = { ...currentFilters, limit: LIMIT, offset: currentOffset };
      Object.keys(params).forEach((k) => {
        if (params[k] === "" || params[k] == null) delete params[k];
      });
      const res = await autoApi.get("/vehicles", { params });
      setItems(res.data.items || []);
      setTotal(res.data.total || 0);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(filters, offset);
  }, [load, filters, offset]);

  const totalPages = Math.max(1, Math.ceil(total / LIMIT));
  const page = Math.floor(offset / LIMIT) + 1;

  return (
    <div className="auto-section">
      <SearchHero variant="catalog" />
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "end", margin: "18px 0 12px" }}>
        <div>
          <h1 style={{ fontSize: 28, margin: 0 }}>Каталог автомобилей</h1>
          <div className="auto-muted" data-testid="catalog-count">Найдено: {total}</div>
        </div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 18 }} className="catalog-grid">
        <aside>
          <VehicleFilters
            value={filters}
            onChange={() => {}}
            onApply={(next) => {
              setOffset(0);
              setFilters(next);
            }}
          />
        </aside>
        <div>
          {loading ? (
            <div className="auto-card auto-muted" data-testid="catalog-loading">Загружаем…</div>
          ) : items.length === 0 ? (
            <div className="auto-card auto-muted" data-testid="catalog-empty">
              По вашему запросу ничего не найдено. Попробуйте изменить фильтры.
            </div>
          ) : (
            <div className="auto-grid" data-testid="catalog-grid">
              {items.map((v) => (
                <VehicleCard key={v.id} vehicle={v} />
              ))}
            </div>
          )}
          {totalPages > 1 && (
            <div style={{ display: "flex", justifyContent: "center", gap: 8, marginTop: 18 }}>
              <button
                className="auto-btn auto-btn-outline"
                disabled={page === 1}
                onClick={() => setOffset(Math.max(0, offset - LIMIT))}
                data-testid="page-prev"
              >
                Назад
              </button>
              <div className="auto-badge" data-testid="page-indicator">
                {page} / {totalPages}
              </div>
              <button
                className="auto-btn auto-btn-outline"
                disabled={page >= totalPages}
                onClick={() => setOffset(offset + LIMIT)}
                data-testid="page-next"
              >
                Вперёд
              </button>
            </div>
          )}
        </div>
      </div>
      <style>{`
        @media (max-width: 800px) {
          .catalog-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  );
}
