import React, { useEffect, useState } from "react";
import autoApi from "../../services/autoApi";
import PriceBreakdown from "../../components/auto/PriceBreakdown";
import { getFxRate, formatRub } from "../../services/autoCurrency";

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
  const [price, setPrice] = useState(8000);          // NZD input (one of the few places customer thinks NZD)
  const [storage, setStorage] = useState(0);
  const [city, setCity] = useState("");
  const [nonRunner, setNonRunner] = useState(false);
  const [breakdown, setBreakdown] = useState(null);
  const [pricing, setPricing] = useState(null);
  const [fx, setFx] = useState(null);

  useEffect(() => { getFxRate().then(setFx); }, []);
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

  const rate = fx?.nzd_to_rub_display || 57.68;
  const rub = (nzd) => formatRub(nzd);

  return (
    <div className="auto-section">
      <h1 style={{ fontSize: 32, margin: 0 }}>Стоимость и комиссии</h1>
      <p className="auto-muted" style={{ marginTop: 8 }}>
        Все цены показаны в рублях по курсу Google + наша конвенциальная комиссия 3%.
        Текущий курс: <b style={{ color: "var(--auto-text)" }}>1 NZ$ ≈ {rate.toFixed(2)} ₽</b>.
        Если авто <b>не на ходу</b> — транспорт умножается ×2 (буксировка).
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18, marginTop: 16 }} className="fees-grid">
        <div className="auto-card">
          <div style={{ fontWeight: 600, marginBottom: 10 }}>Базовые тарифы (в ₽)</div>
          <ul style={{ paddingLeft: 18, margin: 0, lineHeight: 1.9 }} className="auto-muted">
            <li>Комиссия АвтоРесурс — <b style={{ color: "var(--auto-text)" }}>20%</b> от цены авто</li>
            <li>Премия аукциона — <b style={{ color: "var(--auto-text)" }}>10%</b> от выигрышной ставки</li>
            <li>Местный транспорт по НЗ — <b style={{ color: "var(--auto-text)" }}>от {rub(0)} до {rub(1700)}</b> (Окленд → Инверкаргилл)</li>
            <li>Не на ходу — <b style={{ color: "var(--auto-text)" }}>×2 транспорт</b> + форклифт обязателен</li>
            <li>Инспекция (опционально) — <b style={{ color: "var(--auto-text)" }}>{rub(200)}</b></li>
            <li>Форклифт — <b style={{ color: "var(--auto-text)" }}>{rub(200)}</b></li>
            <li>Демонтаж / распил — <b style={{ color: "var(--auto-text)" }}>{rub(800)}</b> (только схема «запчасти»)</li>
            <li>Документы экспорта — <b style={{ color: "var(--auto-text)" }}>{rub(250)}</b></li>
            <li>Хранение — <b style={{ color: "var(--auto-text)" }}>{rub(50)} / день</b></li>
            <li>Морской фрахт — <b style={{ color: "var(--auto-text)" }}>~{formatRub(5000 / (fx?.nzd_to_usd || 0.6))}</b> (1/2 контейнера, 2 авто × $5 000)</li>
            <li>Страховка — <b style={{ color: "var(--auto-text)" }}>1.5%</b> от CIF</li>
            <li>Растаможка РФ — индивидуально (открыть калькулятор «Под ключ» на странице авто)</li>
          </ul>
        </div>
        <div className="auto-card">
          <div style={{ fontWeight: 600, marginBottom: 10 }}>Калькулятор расходов в НЗ</div>
          <label className="auto-muted" style={{ fontSize: 12 }}>Цена автомобиля на аукционе, ₽</label>
          <input
            className="auto-input"
            type="number"
            value={Math.round(price * rate)}
            onChange={(e) => setPrice(Number(e.target.value) / rate)}
            data-testid="fees-price"
          />
          <label className="auto-muted" style={{ fontSize: 12, marginTop: 10, display: "block" }}>Город / филиал аукциона</label>
          <select className="auto-select" value={city} onChange={(e) => setCity(e.target.value)} data-testid="fees-city">
            {CITY_OPTIONS.map((c) => <option key={c || "default"} value={c}>{c || "Стандартный тариф"}</option>)}
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
          <summary style={{ cursor: "pointer", fontWeight: 600 }}>Тариф транспорта по городам Новой Зеландии</summary>
          <table className="auto-table" style={{ marginTop: 10 }}>
            <thead><tr><th>Город / филиал</th><th>На ходу, ₽</th><th>Не на ходу, ₽</th></tr></thead>
            <tbody>
              {Object.entries(pricing.runner_nzd_by_branch)
                .sort((a, b) => a[1] - b[1])
                .map(([city, val]) => (
                  <tr key={city}>
                    <td style={{ textTransform: "capitalize" }}>{city}</td>
                    <td>{rub(val)}</td>
                    <td style={{ color: "var(--auto-warning)" }}>{rub(val * 2)}</td>
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
