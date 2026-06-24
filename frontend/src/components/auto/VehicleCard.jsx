import React from "react";
import { Link } from "react-router-dom";

const STATUS_BADGE = {
  available: { cls: "auto-badge-success", text: "Доступен" },
  sold: { cls: "auto-badge-danger", text: "Продан" },
  expired: { cls: "auto-badge-warning", text: "Истёк" },
  won: { cls: "auto-badge-primary", text: "Куплен" },
  hidden: { cls: "", text: "Скрыт" },
};

const LISTING_LABEL = {
  auction: "Аукцион",
  fixed_price: "Фикс. цена",
  inquiry_only: "По запросу",
};

function fmtPrice(v) {
  if (v == null) return "—";
  return `NZ$${Number(v).toLocaleString("en-NZ", { maximumFractionDigits: 0 })}`;
}

function fmtKm(v) {
  if (v == null) return "—";
  return `${Number(v).toLocaleString("ru-RU")} км`;
}

function fmtDate(v) {
  if (!v) return null;
  try {
    return new Date(v).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
  } catch {
    return null;
  }
}

export default function VehicleCard({ vehicle }) {
  const status = STATUS_BADGE[vehicle.status] || { cls: "", text: vehicle.status };
  const cover = (vehicle.images && vehicle.images[0]) || null;
  return (
    <div className="auto-card" data-testid={`vehicle-card-${vehicle.id}`}>
      <div style={{ position: "relative" }}>
        {cover ? (
          <img src={cover} alt={vehicle.title_ru} className="auto-image" />
        ) : (
          <div className="auto-placeholder">Нет изображения</div>
        )}
        <div style={{ position: "absolute", top: 10, left: 10, display: "flex", gap: 6 }}>
          <span className={`auto-badge ${status.cls}`}>{status.text}</span>
          <span className="auto-badge">{vehicle.country}</span>
          <span className="auto-badge">{LISTING_LABEL[vehicle.listing_type] || vehicle.listing_type}</span>
        </div>
      </div>
      <div style={{ marginTop: 14 }}>
        <div style={{ fontSize: 16, fontWeight: 600, lineHeight: 1.3 }}>{vehicle.title_ru}</div>
        <div className="auto-muted" style={{ fontSize: 13, marginTop: 4 }}>
          {vehicle.year ? `${vehicle.year} · ` : ""}
          {fmtKm(vehicle.mileage_km)}
          {vehicle.location ? ` · ${vehicle.location}` : ""}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "end", marginTop: 12 }}>
          <div>
            <div className="auto-muted" style={{ fontSize: 12 }}>Текущая цена</div>
            <div style={{ fontSize: 18, fontWeight: 700 }}>{fmtPrice(vehicle.current_price_nzd)}</div>
          </div>
          {vehicle.auction_end_time && (
            <div style={{ textAlign: "right" }}>
              <div className="auto-muted" style={{ fontSize: 12 }}>Окончание</div>
              <div style={{ fontSize: 13 }}>{fmtDate(vehicle.auction_end_time)}</div>
            </div>
          )}
        </div>
        <Link
          to={`/auto/vehicle/${vehicle.id}`}
          className="auto-btn"
          style={{ width: "100%", marginTop: 14 }}
          data-testid={`vehicle-detail-link-${vehicle.id}`}
        >
          Подробнее
        </Link>
      </div>
    </div>
  );
}

export { fmtPrice, fmtKm, fmtDate, LISTING_LABEL };
