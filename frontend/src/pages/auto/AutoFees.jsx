import React, { useEffect, useState } from "react";
import autoApi from "../../services/autoApi";
import PriceBreakdown from "../../components/auto/PriceBreakdown";

export default function AutoFees() {
  const [price, setPrice] = useState(8000);
  const [storage, setStorage] = useState(0);
  const [breakdown, setBreakdown] = useState(null);

  useEffect(() => {
    autoApi
      .post("/price-breakdown", { vehicle_price_nzd: Number(price || 0), storage_days: Number(storage || 0) })
      .then((r) => setBreakdown(r.data));
  }, [price, storage]);

  return (
    <div className="auto-section">
      <h1 style={{ fontSize: 32, margin: 0 }}>Стоимость и комиссии</h1>
      <p className="auto-muted" style={{ marginTop: 8 }}>Все суммы в NZD. Курс в рубли уточняется в счёте.</p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18, marginTop: 16 }} className="fees-grid">
        <div className="auto-card">
          <div style={{ fontWeight: 600, marginBottom: 10 }}>Базовые тарифы</div>
          <ul style={{ paddingLeft: 18, margin: 0, lineHeight: 1.9 }} className="auto-muted">
            <li>Комиссия — <b style={{ color: "var(--auto-text)" }}>20%</b> от цены авто</li>
            <li>Местный транспорт — <b style={{ color: "var(--auto-text)" }}>NZ$500</b></li>
            <li>Документы — <b style={{ color: "var(--auto-text)" }}>NZ$250</b></li>
            <li>Хранение — <b style={{ color: "var(--auto-text)" }}>NZ$50 / день</b></li>
            <li>Доля контейнера — <b style={{ color: "var(--auto-text)" }}>NZ$3,333</b></li>
            <li>Погрузчик (форклифт) — <b style={{ color: "var(--auto-text)" }}>NZ$0</b> (если не требуется)</li>
          </ul>
        </div>
        <div className="auto-card">
          <div style={{ fontWeight: 600, marginBottom: 10 }}>Калькулятор</div>
          <label className="auto-muted" style={{ fontSize: 12 }}>Цена автомобиля, NZ$</label>
          <input className="auto-input" type="number" value={price} onChange={(e) => setPrice(e.target.value)} data-testid="fees-price" />
          <label className="auto-muted" style={{ fontSize: 12, marginTop: 10, display: "block" }}>Дней хранения</label>
          <input className="auto-input" type="number" value={storage} onChange={(e) => setStorage(e.target.value)} data-testid="fees-storage" />
        </div>
      </div>
      {breakdown && <div style={{ marginTop: 18 }}><PriceBreakdown breakdown={breakdown} /></div>}
      <style>{`@media (max-width: 800px) { .fees-grid { grid-template-columns: 1fr !important; } }`}</style>
    </div>
  );
}
