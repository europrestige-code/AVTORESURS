import React from "react";
import { fmtPrice } from "./VehicleCard";

const LINES = [
  ["vehicle_price_nzd", "Цена автомобиля"],
  ["commission_nzd", "Комиссия (20%)"],
  ["local_transport_nzd", "Местный транспорт"],
  ["forklift_nzd", "Погрузчик"],
  ["storage_nzd", "Хранение"],
  ["documentation_nzd", "Документы"],
  ["container_share_nzd", "Доля контейнера"],
];

export default function PriceBreakdown({ breakdown, label = "Расчёт стоимости" }) {
  if (!breakdown) return null;
  return (
    <div className="auto-card" data-testid="price-breakdown">
      <div style={{ fontWeight: 600, marginBottom: 10 }}>{label}</div>
      <table className="auto-table">
        <tbody>
          {LINES.map(([k, l]) => (
            <tr key={k}>
              <td className="auto-muted">{l}</td>
              <td style={{ textAlign: "right" }}>{fmtPrice(breakdown[k])}</td>
            </tr>
          ))}
          <tr>
            <td style={{ fontWeight: 700 }}>Итого</td>
            <td style={{ textAlign: "right", fontWeight: 700, fontSize: 18 }}>
              {fmtPrice(breakdown.total_nzd)}
            </td>
          </tr>
          {breakdown.total_rub != null && (
            <tr>
              <td className="auto-muted">≈ в рублях</td>
              <td style={{ textAlign: "right" }}>
                {Number(breakdown.total_rub).toLocaleString("ru-RU", { maximumFractionDigits: 0 })} ₽
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
