import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Calculator } from "lucide-react";
import CountdownTimer from "./CountdownTimer";
import LandedPriceModal from "./LandedPriceModal";
import { getFxRate, formatRub } from "../../services/autoCurrency";

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

function fmtKm(v) {
  if (v == null) return "—";
  return `${Number(v).toLocaleString("ru-RU")} км`;
}

// Internal/admin-only formatter (kept for staff-facing pages where NZD is needed).
function fmtPrice(v) {
  if (v == null) return "—";
  return `NZ$${Number(v).toLocaleString("en-NZ", { maximumFractionDigits: 0 })}`;
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
  const [landedOpen, setLandedOpen] = useState(false);
  const [, setFx] = useState(null);
  useEffect(() => { getFxRate().then(setFx); }, []);
  const status = STATUS_BADGE[vehicle.status] || { cls: "", text: vehicle.status };
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
            <div className="auto-muted vehicle-card__price-label">Цена · с аукциона</div>
            <div className="vehicle-card__price">{formatRub(vehicle.current_price_nzd)}</div>
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

        <div className="vehicle-card__actions">
          <Link
            to={`/auto/vehicle/${vehicle.id}`}
            className="auto-btn vehicle-card__cta"
            data-testid={`vehicle-detail-link-${vehicle.id}`}
          >
            Подробнее
          </Link>
          {vehicle.current_price_nzd > 0 && (
            <button
              type="button"
              className="auto-btn auto-btn--ghost vehicle-card__landed"
              onClick={(e) => { e.preventDefault(); setLandedOpen(true); }}
              data-testid={`vehicle-landed-btn-${vehicle.id}`}
              title="Рассчитать ориентировочную цену под ключ во Владивостоке"
            >
              <Calculator size={14} style={{ marginRight: 6, verticalAlign: "text-bottom" }} />
              Под ключ в РФ
            </button>
          )}
        </div>
      </div>

      <LandedPriceModal
        open={landedOpen}
        onClose={() => setLandedOpen(false)}
        vehicleId={vehicle.id}
        fallbackFobNzd={vehicle.current_price_nzd || vehicle.buy_now_price_nzd}
      />
    </article>
  );
}

export { fmtPrice, fmtKm, fmtDate, LISTING_LABEL };
