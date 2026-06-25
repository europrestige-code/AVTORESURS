import React, { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import autoApi from "../../services/autoApi";
import { useAuth } from "../../contexts/AuthContext";
import EngagementPanel from "../../components/auto/EngagementPanel";
import UrgencyWidget from "../../components/auto/UrgencyWidget";
import PriceGuidance from "../../components/auto/PriceGuidance";
import PriceBreakdown from "../../components/auto/PriceBreakdown";
import CountdownTimer from "../../components/auto/CountdownTimer";
import SimilarLots from "../../components/auto/SimilarLots";
import { fmtPrice, fmtKm, fmtDate, LISTING_LABEL } from "../../components/auto/VehicleCard";
import { getFxRate, formatRub } from "../../services/autoCurrency";

export default function AutoVehicleDetail() {
  const { id } = useParams();
  const { isAuthenticated, user } = useAuth();
  const [vehicle, setVehicle] = useState(null);
  const [error, setError] = useState(null);
  const [activeImage, setActiveImage] = useState(0);
  const [depositVerified, setDepositVerified] = useState(false);
  useEffect(() => { getFxRate(); }, []);
  const [inquiry, setInquiry] = useState({ message: "", phone: "", telegram: "" });
  const [inquiryStatus, setInquiryStatus] = useState(null);
  const [watching, setWatching] = useState(false);

  const load = useCallback(async () => {
    try {
      const r = await autoApi.get(`/vehicles/${id}`);
      setVehicle(r.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Не удалось загрузить.");
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  // Live poll of the highest bid every 8s, so the visible amount and bid
  // count update without a page refresh.
  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    const tick = async () => {
      try {
        const r = await autoApi.get(`/vehicles/${id}/highest-bid`);
        if (cancelled) return;
        setVehicle((prev) =>
          prev
            ? {
                ...prev,
                highest_bid_nzd: r.data.highest_bid_nzd,
                bid_count: r.data.bid_count,
                current_price_nzd: r.data.highest_bid_nzd > (prev.current_price_nzd || 0)
                  ? r.data.highest_bid_nzd
                  : prev.current_price_nzd,
              }
            : prev,
        );
      } catch { /* ignore polling errors */ }
    };
    const t = setInterval(tick, 8000);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, [id]);

  useEffect(() => {
    if (!isAuthenticated) return;
    autoApi.get("/my/deposit").then((r) => setDepositVerified(!!r.data.verified)).catch(() => {});
  }, [isAuthenticated]);

  const submitInquiry = async (e) => {
    e.preventDefault();
    if (!inquiry.message.trim()) return;
    try {
      await autoApi.post(`/vehicles/${id}/inquiry`, inquiry);
      setInquiryStatus("Заявка отправлена. Мы свяжемся с вами.");
      setInquiry({ message: "", phone: "", telegram: "" });
    } catch (err) {
      setInquiryStatus(err.response?.data?.detail || "Ошибка при отправке.");
    }
  };

  const toggleWatch = async () => {
    if (!isAuthenticated) return;
    try {
      const r = await autoApi.post(`/vehicles/${id}/watchlist`);
      setWatching(r.data.watching);
    } catch {}
  };

  if (error) return <div className="auto-section auto-card auto-muted" data-testid="vehicle-error">{error}</div>;
  if (!vehicle) return <div className="auto-section auto-card auto-muted" data-testid="vehicle-loading">Загружаем…</div>;

  const isAU = vehicle.country === "AU";
  const isInquiryOnly = isAU || vehicle.listing_type === "inquiry_only";
  const cover = vehicle.images?.[activeImage] || vehicle.images?.[0];

  return (
    <div className="auto-section">
      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 22 }} className="vehicle-grid">
        <div>
          <div className="auto-card" style={{ padding: 0, overflow: "hidden" }}>
            {cover ? (
              <img src={cover} alt={vehicle.title_ru} className="auto-image" style={{ aspectRatio: "16/10", borderRadius: 0 }} />
            ) : (
              <div className="auto-placeholder" style={{ aspectRatio: "16/10", borderRadius: 0 }}>Нет изображения</div>
            )}
            {vehicle.images && vehicle.images.length > 1 && (
              <div style={{ display: "flex", gap: 8, padding: 10, overflowX: "auto" }}>
                {vehicle.images.map((src, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => setActiveImage(i)}
                    style={{
                      border: i === activeImage ? "2px solid var(--auto-primary)" : "1px solid var(--auto-border)",
                      borderRadius: 8, padding: 0, overflow: "hidden", background: "#0a0a0a",
                    }}
                    data-testid={`vehicle-thumb-${i}`}
                  >
                    <img src={src} alt="" style={{ width: 80, height: 60, objectFit: "cover", display: "block" }} />
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="auto-card" style={{ marginTop: 18 }}>
            <h1 style={{ fontSize: 24, margin: 0 }} data-testid="vehicle-title">{vehicle.title_ru}</h1>
            <div className="auto-muted" style={{ marginTop: 4 }}>
              {vehicle.country} · {LISTING_LABEL[vehicle.listing_type] || vehicle.listing_type} · {vehicle.source}
              {vehicle.source_reference ? ` · ${vehicle.source_reference}` : ""}
            </div>

            <div className="auto-divider" />
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
              <Spec label="Год" value={vehicle.year || "—"} />
              <Spec label="Пробег" value={fmtKm(vehicle.mileage_km)} />
              <Spec label="Двигатель" value={vehicle.engine || "—"} />
              <Spec label="Топливо" value={vehicle.fuel || "—"} />
              <Spec label="КПП" value={vehicle.transmission || "—"} />
              <Spec label="Кузов" value={vehicle.body_type || "—"} />
              <Spec label="Локация" value={vehicle.location || "—"} />
              <Spec label="Состояние" value={vehicle.condition || "—"} />
              <Spec label="Повреждения" value={vehicle.damage_type || "—"} />
            </div>

            {vehicle.description_ru && (
              <>
                <div className="auto-divider" />
                <div style={{ fontWeight: 600, marginBottom: 6 }}>Описание</div>
                <div className="auto-muted" style={{ whiteSpace: "pre-wrap" }}>{vehicle.description_ru}</div>
              </>
            )}
            {vehicle.ai_summary_ru && (
              <>
                <div className="auto-divider" />
                <div style={{ fontWeight: 600, marginBottom: 6 }}>AI-резюме</div>
                <div className="auto-muted">{vehicle.ai_summary_ru}</div>
              </>
            )}
            {vehicle.ai_risk_summary_ru && (
              <>
                <div className="auto-divider" />
                <div style={{ fontWeight: 600, marginBottom: 6 }}>Оценка рисков</div>
                <div className="auto-muted">{vehicle.ai_risk_summary_ru}</div>
              </>
            )}
          </div>
        </div>

        <div style={{ display: "grid", gap: 18, alignContent: "start" }}>
          <div className="auto-card">
            <div className="auto-muted" style={{ fontSize: 12 }}>Цена · с аукциона</div>
            <div style={{ fontSize: 28, fontWeight: 800 }} data-testid="vehicle-price">
              {formatRub(vehicle.current_price_nzd)}
            </div>
            {vehicle.buy_now_price_nzd && (
              <div className="auto-muted" style={{ marginTop: 6 }}>Купить сразу: {formatRub(vehicle.buy_now_price_nzd)}</div>
            )}
            <div className="auto-muted" style={{ fontSize: 13, marginTop: 6 }}>
              Внутр. макс. ставка: <b style={{ color: "var(--auto-text)" }}>{formatRub(vehicle.highest_bid_nzd || 0)}</b>
              {" · "}ставок: {vehicle.bid_count || 0}
            </div>
            {vehicle.auction_end_time && (
              <div style={{ marginTop: 10 }}>
                <CountdownTimer target={vehicle.auction_end_time} testid="vehicle-detail-countdown" />
                <div className="auto-muted" style={{ fontSize: 12, marginTop: 4 }}>
                  Закрытие: {fmtDate(vehicle.auction_end_time)}
                </div>
              </div>
            )}
            <button
              type="button"
              onClick={toggleWatch}
              className="auto-btn auto-btn-outline"
              style={{ marginTop: 12, width: "100%" }}
              data-testid="watchlist-btn"
            >
              {watching ? "★ В избранном" : "☆ В избранное"}
            </button>
          </div>

          <UrgencyWidget vehicle={vehicle} />
          <PriceGuidance vehicle={vehicle} />

          <EngagementPanel
            vehicle={vehicle}
            depositVerified={depositVerified}
            isAuthenticated={isAuthenticated}
            user={user}
            onPlaced={() => load()}
          />

          {/* Legacy inquiry textarea retained only for the rare custom-message flow */}
          {isInquiryOnly && (
            <div className="auto-card" data-testid="inquiry-panel">
              <div style={{ fontWeight: 600, marginBottom: 8 }}>
                {isAU ? "Автомобиль из Австралии — только по запросу" : "Этот автомобиль доступен по запросу"}
              </div>
              <form onSubmit={submitInquiry} style={{ display: "grid", gap: 8 }}>
                <textarea
                  className="auto-textarea"
                  rows={4}
                  placeholder="Опишите интерес: цена, условия, похожие авто из НЗ…"
                  value={inquiry.message}
                  onChange={(e) => setInquiry({ ...inquiry, message: e.target.value })}
                  data-testid="inquiry-message"
                  required
                />
                <input
                  className="auto-input"
                  placeholder="Телефон (опционально)"
                  value={inquiry.phone}
                  onChange={(e) => setInquiry({ ...inquiry, phone: e.target.value })}
                  data-testid="inquiry-phone"
                />
                <input
                  className="auto-input"
                  placeholder="Telegram (опционально)"
                  value={inquiry.telegram}
                  onChange={(e) => setInquiry({ ...inquiry, telegram: e.target.value })}
                  data-testid="inquiry-telegram"
                />
                <button type="submit" className="auto-btn" data-testid="inquiry-submit">Запросить цену</button>
                {isAU && (
                  <Link to="/auto/catalog?country=NZ" className="auto-btn auto-btn-outline" data-testid="inquiry-nz-link">
                    Найти похожий в Новой Зеландии
                  </Link>
                )}
                {inquiryStatus && <div className="auto-badge auto-badge-primary" data-testid="inquiry-status">{inquiryStatus}</div>}
              </form>
            </div>
          )}

          {vehicle.price_breakdown && (
            <PriceBreakdown breakdown={vehicle.price_breakdown} />
          )}
        </div>
      </div>

      <SimilarLots vehicleId={id} />
      <style>{`
        @media (max-width: 900px) {
          .vehicle-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  );
}

function Spec({ label, value }) {
  return (
    <div>
      <div className="auto-muted" style={{ fontSize: 12 }}>{label}</div>
      <div style={{ fontWeight: 600 }}>{value}</div>
    </div>
  );
}
