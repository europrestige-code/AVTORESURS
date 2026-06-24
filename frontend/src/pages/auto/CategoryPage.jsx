import React, { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import autoApi from "../../services/autoApi";
import VehicleCard from "../../components/auto/VehicleCard";
import VehicleFilters from "../../components/auto/VehicleFilters";

const LIMIT = 12;

/**
 * Generic category landing page. Driven by an `apiFilters` object the parent
 * passes in. All sources (Turners, Manheim, Pickles) are aggregated since the
 * underlying collection is unified.
 */
export default function CategoryPage({ category }) {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [extra, setExtra] = useState({});
  const [loading, setLoading] = useState(true);
  const [searchParams] = useSearchParams();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = { ...category.apiFilters, ...extra, limit: LIMIT, offset };
      // Allow URL overrides (e.g. ?country=NZ)
      ["country", "source", "make", "model", "year_from", "year_to"].forEach((k) => {
        const v = searchParams.get(k);
        if (v) params[k] = v;
      });
      Object.keys(params).forEach((k) => {
        if (params[k] === "" || params[k] == null) delete params[k];
      });
      const res = await autoApi.get("/vehicles", { params });
      setItems(res.data.items || []);
      setTotal(res.data.total || 0);
    } finally {
      setLoading(false);
    }
  }, [category, extra, offset, searchParams]);

  useEffect(() => { load(); }, [load]);

  const totalPages = Math.max(1, Math.ceil(total / LIMIT));
  const page = Math.floor(offset / LIMIT) + 1;

  return (
    <div className="auto-section">
      <header className={`category-hero category-hero--${category.key}`} data-testid={`category-hero-${category.key}`}>
        <div className="category-hero__icon" aria-hidden>{category.icon}</div>
        <div className="category-hero__text">
          <h1 className="category-hero__title">{category.title}</h1>
          <p className="auto-muted category-hero__subtitle">{category.subtitle}</p>
          <div className="category-hero__sources">
            <span>Источники:</span>
            <span className="auto-badge">Turners NZ</span>
            <span className="auto-badge">Manheim NZ</span>
            <span className="auto-badge">Pickles AU</span>
            <span className="auto-badge">Дилерские стоки</span>
          </div>
        </div>
        <div className="category-hero__count">
          <div className="auto-muted" style={{ fontSize: 12 }}>В наличии</div>
          <div className="category-hero__count-value" data-testid={`category-count-${category.key}`}>
            {total.toLocaleString("ru-RU")}
          </div>
        </div>
      </header>

      <div className="category-grid" style={{ marginTop: 18 }}>
        <aside>
          <VehicleFilters
            value={extra}
            onChange={() => {}}
            onApply={(next) => {
              setOffset(0);
              setExtra(next);
            }}
          />
          {category.tips && (
            <div className="auto-card" style={{ marginTop: 14 }}>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>Что важно знать</div>
              <ul className="auto-muted" style={{ paddingLeft: 18, margin: 0, lineHeight: 1.7, fontSize: 13 }}>
                {category.tips.map((t, i) => <li key={i}>{t}</li>)}
              </ul>
            </div>
          )}
          <div className="auto-card" style={{ marginTop: 14 }}>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>Покупка через АвтоРесурс</div>
            <p className="auto-muted" style={{ fontSize: 13, margin: 0 }}>
              Вы оформляете сделку с АвтоРесурс. Мы выкупаем автомобиль на аукционе от вашего имени.
            </p>
            <Link to="/auto/terms" className="auto-btn auto-btn-outline" style={{ marginTop: 10, width: "100%" }} data-testid={`category-${category.key}-terms-link`}>
              Условия
            </Link>
          </div>
        </aside>

        <div>
          {loading ? (
            <div className="auto-card auto-muted" data-testid={`category-${category.key}-loading`}>Загружаем…</div>
          ) : items.length === 0 ? (
            <div className="auto-card auto-muted" data-testid={`category-${category.key}-empty`}>
              В этой категории пока ничего нет. Попробуйте смежные категории или {" "}
              <Link to="/auto/catalog" style={{ color: "var(--auto-primary)" }}>полный каталог</Link>.
            </div>
          ) : (
            <div className="auto-grid" data-testid={`category-${category.key}-grid`}>
              {items.map((v) => <VehicleCard key={v.id} vehicle={v} />)}
            </div>
          )}
          {totalPages > 1 && (
            <div style={{ display: "flex", justifyContent: "center", gap: 8, marginTop: 18 }}>
              <button
                className="auto-btn auto-btn-outline"
                disabled={page === 1}
                onClick={() => setOffset(Math.max(0, offset - LIMIT))}
              >Назад</button>
              <div className="auto-badge">{page} / {totalPages}</div>
              <button
                className="auto-btn auto-btn-outline"
                disabled={page >= totalPages}
                onClick={() => setOffset(offset + LIMIT)}
              >Вперёд</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Category configuration shared with the SearchHero tiles.
export const CATEGORY_DEFS = {
  auctions: {
    key: "auctions",
    title: "Аукционы",
    subtitle: "Авто на торгах из Turners, Manheim, Pickles. Требуется внутренний депозит NZ$1,000.",
    icon: "🏁",
    apiFilters: { listing_type: "auction" },
    tips: [
      "Цена растёт по мере поступления ставок.",
      "Депозит даёт право участия и возвращается при отказе от покупки.",
      "Реальную ставку выставляет менеджер АвтоРесурс, не превышая вашу максимальную.",
    ],
  },
  buynow: {
    key: "buynow",
    title: "Купить сейчас",
    subtitle: "Зафиксированная цена. Без торгов, без ожидания. Дороже аукционных, но быстро.",
    icon: "💳",
    apiFilters: { listing_type: "fixed_price" },
    tips: [
      "Цена окончательная.",
      "Депозит не требуется для оформления.",
      "Подходит, если важна скорость и нет желания ждать аукциона.",
    ],
  },
  damaged: {
    key: "damaged",
    title: "Повреждённые",
    subtitle: "Авто после ДТП, града, технических поломок. Дешевле, но требуют восстановления.",
    icon: "🛠️",
    apiFilters: { condition: "Повреждённое" },
    tips: [
      "Проверьте тип повреждения: фронтальный удар, удар сзади, град.",
      "Подушки безопасности могли сработать — каркас требует диагностики.",
      "Хорошо подходят опытным восстановителям и СТО.",
    ],
  },
  eol: {
    key: "eol",
    title: "End of Life · Доноры",
    subtitle: "Автомобили на запчасти. Сильные повреждения, не восстанавливаются — но кузов и узлы ещё рабочие.",
    icon: "♻️",
    apiFilters: { condition: "На запчасти" },
    tips: [
      "Используйте как источник запчастей: двигатели, КПП, кузовные детали, электроника.",
      "Документы могут отсутствовать или ограничены.",
      "Лучшая стратегия — разбор и розничная продажа компонентов.",
    ],
  },
  parts: {
    key: "parts",
    title: "Запчасти и комплектующие",
    subtitle: "Каталог разобранных авто и запчастей. Скоро.",
    icon: "🔧",
    apiFilters: { body_type: "Запчасть" },
    tips: ["Раздел в разработке."],
  },
};
