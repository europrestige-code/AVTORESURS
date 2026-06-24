import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import autoApi from "../../services/autoApi";
import VehicleCard from "../../components/auto/VehicleCard";

const HOW = [
  ["Выбираете автомобиль", "Каталог содержит аукционные и розничные авто из Новой Зеландии. Австралия — по запросу."],
  ["Вносите депозит", "Депозит NZ$1,000 разрешает участие в торгах. Возвращается, если не выкупили авто."],
  ["Делаете ставку", "Внутренняя система фиксирует вашу максимальную ставку. Менеджер выставляет её на реальном аукционе."],
  ["Выигрываете и оплачиваете", "Выставляем счёт: цена + комиссия + транспорт + хранение + документы + контейнер."],
  ["Доставка в Россию", "Отслеживаете статус: со склада → контейнер → отправка → прибытие → доставка."],
];

export default function AutoHome() {
  const [featured, setFeatured] = useState([]);

  useEffect(() => {
    autoApi
      .get("/vehicles", { params: { country: "NZ", limit: 6 } })
      .then((r) => setFeatured(r.data.items || []))
      .catch(() => setFeatured([]));
  }, []);

  return (
    <>
      <section className="auto-hero auto-section" style={{ borderRadius: 20 }}>
        <div style={{ maxWidth: 720 }}>
          <div className="auto-badge auto-badge-primary" style={{ marginBottom: 16 }}>BuyAnywhere · Auto</div>
          <h1 style={{ fontSize: 44, fontWeight: 800, lineHeight: 1.05, margin: 0, letterSpacing: "-0.02em" }}>
            Автомобили из Новой Зеландии под заказ
          </h1>
          <p className="auto-muted" style={{ fontSize: 18, marginTop: 14, maxWidth: 620 }}>
            Аукционные авто, повреждённые автомобили, доноры, коммерческий транспорт и запчасти
            с расчётом доставки, комиссии и логистики.
          </p>
          <div style={{ display: "flex", gap: 12, marginTop: 22, flexWrap: "wrap" }}>
            <Link to="/auto/catalog" className="auto-btn" data-testid="home-cta-catalog">Смотреть автомобили</Link>
            <Link to="/auto/how-it-works" className="auto-btn auto-btn-outline" data-testid="home-cta-how">Как это работает</Link>
          </div>
        </div>
      </section>

      <section className="auto-section">
        <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 16 }}>
          <h2 style={{ fontSize: 24, margin: 0 }}>Рекомендуемые автомобили</h2>
          <Link to="/auto/catalog" style={{ color: "var(--auto-primary)" }}>Весь каталог →</Link>
        </div>
        {featured.length === 0 ? (
          <div className="auto-card auto-muted" data-testid="home-empty">Загружаем автомобили…</div>
        ) : (
          <div className="auto-grid" data-testid="home-featured-grid">
            {featured.map((v) => (
              <VehicleCard key={v.id} vehicle={v} />
            ))}
          </div>
        )}
      </section>

      <section className="auto-section">
        <h2 style={{ fontSize: 24, marginBottom: 16 }}>Как это работает</h2>
        <div className="auto-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))" }}>
          {HOW.map(([t, d], i) => (
            <div key={i} className="auto-card">
              <div className="auto-badge auto-badge-primary" style={{ marginBottom: 10 }}>Шаг {i + 1}</div>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>{t}</div>
              <div className="auto-muted" style={{ fontSize: 13 }}>{d}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="auto-section">
        <div className="auto-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: 18 }}>Готовы начать?</div>
              <div className="auto-muted">Внесите депозит и сделайте первую ставку сегодня.</div>
            </div>
            <Link to="/auto/dashboard" className="auto-btn" data-testid="home-cta-dashboard">Внести депозит</Link>
          </div>
        </div>
      </section>
    </>
  );
}
