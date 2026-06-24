import React, { useEffect, useState } from "react";
import autoApi from "../../services/autoApi";
import PriceBreakdown from "../../components/auto/PriceBreakdown";

const CITY_OPTIONS = [
  "", "Auckland", "Otahuhu", "North Shore", "Westgate", "Botany", "Manukau", "Penrose",
  "Whangarei",
  "Hamilton", "Tauranga", "Rotorua",
  "Napier", "New Plymouth", "Palmerston North",
  "Porirua", "Wellington",
  "Nelson", "Blenheim",
  "Christchurch", "Hornby", "Moorhouse Ave", "Wairakei Rd",
  "Timaru", "Dunedin", "Invercargill",
];

export default function AutoFees() {
  const [price, setPrice] = useState(8000);
  const [storage, setStorage] = useState(0);
  const [city, setCity] = useState("");
  const [nonRunner, setNonRunner] = useState(false);
  const [breakdown, setBreakdown] = useState(null);
  const [pricing, setPricing] = useState(null);

  useEffect(() => {
    autoApi.get("/transport/pricing").then((r) => setPricing(r.data));
  }, []);

  useEffect(() => {
    const payload = {
      vehicle_price_nzd: Number(price || 0),
      storage_days: Number(storage || 0),
      is_non_runner: nonRunner,
    };
    if (city) payload.branch_or_city = city;
    autoApi.post("/price-breakdown", payload).then((r) => setBreakdown(r.data));
  }, [price, storage, city, nonRunner]);

  return (
    <div className="auto-section">
      <h1 style={{ fontSize: 32, margin: 0 }}>Стоимость и комиссии</h1>
      <p className="auto-muted" style={{ marginTop: 8 }}>
        Все суммы в NZD. Транспорт рассчитывается по городу аукциона (PTS-стиль).
        Не на ходу — транспорт ×2.
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18, marginTop: 16 }} className="fees-grid">
        <div className="auto-card">
          <div style={{ fontWeight: 600, marginBottom: 10 }}>Базовые тарифы</div>
          <ul style={{ paddingLeft: 18, margin: 0, lineHeight: 1.9 }} className="auto-muted">
            <li>Комиссия — <b style={{ color: "var(--auto-text)" }}>20%</b> от цены авто</li>
            <li>Местный транспорт — <b style={{ color: "var(--auto-text)" }}>от NZ$0 до NZ$1,950</b> (Auckland → Invercargill)</li>
            <li>Не на ходу — <b style={{ color: "var(--auto-text)" }}>×2 транспорт</b></li>
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
          <label className="auto-muted" style={{ fontSize: 12, marginTop: 10, display: "block" }}>Город / филиал аукциона</label>
          <select className="auto-select" value={city} onChange={(e) => setCity(e.target.value)} data-testid="fees-city">
            {CITY_OPTIONS.map((c) => <option key={c || "default"} value={c}>{c || "Стандартный тариф (NZ$500)"}</option>)}
          </select>
          <label className="auto-muted" style={{ fontSize: 12, marginTop: 10, display: "block" }}>Дней хранения</label>
          <input className="auto-input" type="number" value={storage} onChange={(e) => setStorage(e.target.value)} data-testid="fees-storage" />
          <label style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 14, cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={nonRunner}
              onChange={(e) => setNonRunner(e.target.checked)}
              data-testid="fees-non-runner"
            />
            <span>Автомобиль не на ходу (×2 к транспорту)</span>
          </label>
        </div>
      </div>
      {breakdown && <div style={{ marginTop: 18 }}><PriceBreakdown breakdown={breakdown} /></div>}

      {pricing?.runner_nzd_by_branch && (
        <details className="auto-card" style={{ marginTop: 18 }} data-testid="pricing-table">
          <summary style={{ cursor: "pointer", fontWeight: 600 }}>Тариф по городам Новой Зеландии</summary>
          <table className="auto-table" style={{ marginTop: 10 }}>
            <thead><tr><th>Город / филиал</th><th>На ходу, NZ$</th><th>Не на ходу, NZ$</th></tr></thead>
            <tbody>
              {Object.entries(pricing.runner_nzd_by_branch)
                .sort((a, b) => a[1] - b[1])
                .map(([city, val]) => (
                  <tr key={city}>
                    <td style={{ textTransform: "capitalize" }}>{city}</td>
                    <td>NZ${val}</td>
                    <td style={{ color: "var(--auto-warning)" }}>NZ${val * 2}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </details>
      )}
      <style>{`@media (max-width: 800px) { .fees-grid { grid-template-columns: 1fr !important; } }`}</style>
    </div>
  );
}
