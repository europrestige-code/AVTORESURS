import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, MapPin, Hash, Calendar, ExternalLink, Sparkles } from "lucide-react";
import autoApi from "../../services/autoApi";
import VehicleCard from "../../components/auto/VehicleCard";

function CityTag({ name }) {
  if (!name) return null;
  return (
    <span className="auto-badge" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
      <MapPin size={11} style={{ color: "var(--ar-blue)" }} />
      {name}
    </span>
  );
}

/**
 * Mirror page for a single auction event. We never bounce visitors to
 * Turners or Manheim — they stay on АвтоРесурс and either inspect the
 * vehicles we already have synced from this auction, or leave a soft lead
 * with «Уведомить когда стартует».
 */
export default function AutoAuctionEvent() {
  const { eventId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    autoApi
      .get(`/auctions/events/${encodeURIComponent(eventId)}`)
      .then((r) => { if (!cancelled) setData(r.data); })
      .catch((e) => { if (!cancelled) setError(e.response?.status === 404 ? "Аукцион не найден или уже закрыт." : "Не удалось загрузить аукцион."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [eventId]);

  const event = data?.event;
  const vehicles = data?.vehicles || [];
  const dt = useMemo(() => (event?.starts_at ? new Date(event.starts_at) : null), [event]);

  if (loading) {
    return (
      <div className="auto-section auto-muted" data-testid="auction-event-loading">
        Загружаем аукцион…
      </div>
    );
  }
  if (error || !event) {
    return (
      <div className="auto-section" data-testid="auction-event-error">
        <Link to="/auto/auctions" className="auto-btn auto-btn--ghost">
          <ArrowLeft size={14} style={{ marginRight: 6 }} />
          К календарю
        </Link>
        <div className="auto-card" style={{ marginTop: 16 }}>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Аукцион недоступен</div>
          <div className="auto-muted">{error || "Событие пропало из календаря."}</div>
        </div>
      </div>
    );
  }

  const SOURCE_LABEL = { turners: "Turners NZ", manheim: "Manheim NZ", pickles: "Pickles" };
  const CATEGORY_LABEL = { cars: "Легковые", damaged: "Повреждённые", trucks: "Грузовики и техника" };

  return (
    <div className="auto-section auction-event" data-testid="auction-event">
      <Link to="/auto/auctions" className="auto-btn auto-btn--ghost" data-testid="auction-back">
        <ArrowLeft size={14} style={{ marginRight: 6 }} />
        К календарю
      </Link>

      <div className="auction-event__hero auto-card" style={{ marginTop: 16 }}>
        <div className="auction-event__title-row">
          <div>
            <div className="auto-muted" style={{ fontSize: 12, marginBottom: 6 }}>
              {SOURCE_LABEL[event.source] || event.source} · {CATEGORY_LABEL[event.category] || event.category}
            </div>
            <h1 style={{ fontSize: 26, margin: 0, lineHeight: 1.2 }} data-testid="auction-title">
              {event.title}
            </h1>
            <div className="auction-event__meta" style={{ marginTop: 10 }}>
              {dt && (
                <span className="auto-badge" data-testid="auction-when">
                  <Calendar size={11} style={{ marginRight: 4 }} />
                  {dt.toLocaleDateString("ru-RU")} · {dt.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}
                </span>
              )}
              {event.branch && (
                <span data-testid="auction-branch">
                  <CityTag name={event.branch} />
                </span>
              )}
              {event.city && event.city !== event.branch && (
                <span className="auto-badge">
                  <MapPin size={11} style={{ marginRight: 4 }} /> {event.city}
                </span>
              )}
              {!!event.lots && (
                <span className="auto-badge auto-badge-primary" data-testid="auction-lots">
                  <Hash size={11} style={{ marginRight: 4 }} /> {event.lots} лотов
                </span>
              )}
            </div>
          </div>
          <div className="auction-event__ctas">
            <Link
              to={`/auto/catalog?source=${encodeURIComponent(event.source || "")}`}
              className="auto-btn auto-btn--ghost"
              data-testid="auction-browse-source"
            >
              Все лоты от {SOURCE_LABEL[event.source] || event.source}
            </Link>
          </div>
        </div>
      </div>

      <div className="auction-event__cards-head" style={{ marginTop: 22 }}>
        <h2 style={{ margin: 0, fontSize: 18 }}>
          Лоты этого аукциона в нашем каталоге
        </h2>
        <div className="auto-muted" data-testid="auction-vehicles-count">
          {vehicles.length > 0 ? `Найдено: ${vehicles.length}` : "Лоты ещё не появились"}
        </div>
      </div>

      {vehicles.length > 0 ? (
        <div className="vehicle-grid" data-testid="auction-vehicles-grid">
          {vehicles.map((v) => (
            <VehicleCard key={v.id} vehicle={v} />
          ))}
        </div>
      ) : (
        <div className="auction-event__empty auto-card" data-testid="auction-vehicles-empty">
          <div style={{ fontWeight: 600, marginBottom: 6, display: "flex", alignItems: "center", gap: 6 }}>
            <Sparkles size={15} className="text-blue-400" /> Лоты появятся ближе к началу аукциона
          </div>
          <div className="auto-muted" style={{ marginBottom: 16, lineHeight: 1.5 }}>
            Полный каталог этого аукциона импортёр обычно публикует за 24–48 часов до старта.
            Подпишитесь — пришлём подборку по выбранным параметрам, как только лоты появятся.
          </div>
          <Link
            to="/auto/my/searches"
            className="auto-btn"
            data-testid="auction-empty-subscribe"
          >
            Создать подписку
          </Link>
          {event.auction_url && (
            <a
              href={event.auction_url}
              target="_blank"
              rel="noopener noreferrer"
              className="auto-btn auto-btn--ghost"
              style={{ marginLeft: 8 }}
              data-testid="auction-source-link"
            >
              <ExternalLink size={13} style={{ marginRight: 6 }} />
              Источник
            </a>
          )}
        </div>
      )}
    </div>
  );
}
