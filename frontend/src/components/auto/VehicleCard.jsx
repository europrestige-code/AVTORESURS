import React from "react";
import { Link } from "react-router-dom";
import CountdownTimer from "./CountdownTimer";

const STATUS_BADGE = {
  available: { cls: "auto-badge-success", text: "Доступен" },
  sold: { cls: "auto-badge-danger", text: "Продан" },
  expired: { cls: "auto-badge-warning", text: "Истёк" },
  won: { cls: "auto-badge-primary", text: "Куплен" },
  hidden: { cls: "", text: "Скрыт" },
  import_error: { cls: "auto-badge-warning", text: "Импорт" },
};

const LISTING_LABEL = {
  auction: "Аукцион",
  fixed_price: "Купить сейчас",
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
  // Prefer local (АвтоРесурс-branded) images over source previews
  const localImages = vehicle.local_images || [];
  const sourceImages = vehicle.images || vehicle.source_images || [];
  const cover = (localImages[0] || sourceImages[0]) || null;
  const isBranded = !!localImages[0];

  return (
    <article className="auto-card vehicle-card" data-testid={`vehicle-card-${vehicle.id}`}>
      <div className="vehicle-card__media">
        {cover ? (
          <img src={cover} alt={vehicle.title_ru} className="vehicle-card__img" loading="lazy" />
        ) : (
          <div className="vehicle-card__placeholder">Нет изображения</div>
        )}
        <div className="vehicle-card__badges">
          <span className={`auto-badge ${status.cls}`}>{status.text}</span>
          <span className="auto-badge">{vehicle.country}</span>
          <span className="auto-badge">{LISTING_LABEL[vehicle.listing_type] || vehicle.listing_type}</span>
          {!isBranded && sourceImages[0] && (
            <span className="auto-badge" title="Превью из источника">Источник</span>
          )}
        </div>
      </div>

      <div className="vehicle-card__body">
        <h3 className="vehicle-card__title">{vehicle.title_ru}</h3>
        <div className="vehicle-card__meta auto-muted">
          {vehicle.year ? `${vehicle.year} · ` : ""}
          {fmtKm(vehicle.mileage_km)}
          {vehicle.location ? ` · ${vehicle.location}` : ""}
        </div>

        <div className="vehicle-card__price-row">
          <div>
            <div className="auto-muted vehicle-card__price-label">Текущая цена</div>
            <div className="vehicle-card__price">{fmtPrice(vehicle.current_price_nzd)}</div>
          </div>
          {vehicle.auction_end_time ? (
            <div className="vehicle-card__countdown">
              <div className="auto-muted vehicle-card__price-label">До окончания</div>
              <CountdownTimer
                target={vehicle.auction_end_time}
                compact
                testid={`vehicle-countdown-${vehicle.id}`}
              />
            </div>
          ) : (
            <div className="vehicle-card__countdown vehicle-card__countdown--empty" aria-hidden />
          )}
        </div>

        <Link
          to={`/auto/vehicle/${vehicle.id}`}
          className="auto-btn vehicle-card__cta"
          data-testid={`vehicle-detail-link-${vehicle.id}`}
        >
          Подробнее
        </Link>
      </div>
    </article>
  );
}

export { fmtPrice, fmtKm, fmtDate, LISTING_LABEL };
