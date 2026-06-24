import React, { useState } from "react";
import autoApi from "../../services/autoApi";
import { fmtPrice } from "./VehicleCard";

export default function BidPanel({ vehicle, depositVerified, isAuthenticated, onPlaced }) {
  const [amount, setAmount] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Australia or inquiry-only: hide bidding
  if (vehicle.country === "AU" || vehicle.listing_type === "inquiry_only") {
    return null;
  }

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    const max = parseFloat(amount);
    if (!Number.isFinite(max) || max <= 0) {
      setError("Введите положительную сумму.");
      return;
    }
    try {
      setSubmitting(true);
      const res = await autoApi.post(`/vehicles/${vehicle.id}/bid`, { max_bid_nzd: max });
      setSuccess(`Ставка ${fmtPrice(max)} принята. Текущая макс. ставка: ${fmtPrice(res.data.highest_bid_nzd)}`);
      setAmount("");
      onPlaced?.(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Не удалось разместить ставку.");
    } finally {
      setSubmitting(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="auto-card" data-testid="bid-panel-login-required">
        <div style={{ fontWeight: 600, marginBottom: 8 }}>Сделать ставку</div>
        <div className="auto-muted" style={{ marginBottom: 12 }}>
          Войдите в систему, чтобы участвовать в торгах.
        </div>
        <a href="/" className="auto-btn">Войти</a>
      </div>
    );
  }

  if (!depositVerified) {
    return (
      <div className="auto-card" data-testid="bid-panel-deposit-required">
        <div style={{ fontWeight: 600, marginBottom: 8 }}>Депозит не подтверждён</div>
        <div className="auto-muted" style={{ marginBottom: 12 }}>
          Для участия в торгах требуется подтверждённый депозит NZ$1,000.
        </div>
        <a href="/auto/dashboard" className="auto-btn">Внести депозит</a>
      </div>
    );
  }

  const min = (vehicle.current_price_nzd || 0) + 100;
  return (
    <form className="auto-card" onSubmit={submit} data-testid="bid-panel">
      <div style={{ fontWeight: 600, marginBottom: 8 }}>Сделать ставку</div>
      <div className="auto-muted" style={{ fontSize: 13, marginBottom: 10 }}>
        Текущая макс. ставка: {fmtPrice(vehicle.current_price_nzd || 0)}. Минимально допустимая: {fmtPrice(min)}.
      </div>
      <input
        type="number"
        min="1"
        step="50"
        className="auto-input"
        placeholder="NZ$"
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
        data-testid="bid-amount-input"
      />
      <button type="submit" disabled={submitting} className="auto-btn" style={{ marginTop: 10, width: "100%" }} data-testid="bid-submit-btn">
        {submitting ? "Отправка…" : "Отправить ставку"}
      </button>
      {error && <div className="auto-badge auto-badge-danger" style={{ marginTop: 10 }} data-testid="bid-error">{error}</div>}
      {success && <div className="auto-badge auto-badge-success" style={{ marginTop: 10 }} data-testid="bid-success">{success}</div>}
    </form>
  );
}
