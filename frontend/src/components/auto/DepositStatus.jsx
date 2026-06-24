import React, { useState } from "react";
import autoApi from "../../services/autoApi";

const STATUS = {
  pending: { cls: "auto-badge-warning", text: "Ожидает подтверждения" },
  verified: { cls: "auto-badge-success", text: "Депозит подтверждён" },
  rejected: { cls: "auto-badge-danger", text: "Отклонён" },
};

export default function DepositStatus({ deposit, onChange }) {
  const [method, setMethod] = useState("bank_transfer");
  const [note, setNote] = useState("");
  const [file, setFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [stripeSubmitting, setStripeSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const submitProof = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    try {
      setSubmitting(true);
      const form = new FormData();
      form.append("amount", "1000");
      form.append("currency", "NZD");
      form.append("method", method);
      if (note) form.append("payment_proof_note", note);
      if (file) form.append("payment_proof_file", file);
      await autoApi.post("/deposit/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setSuccess("Подтверждение отправлено. Ожидайте проверки.");
      setNote("");
      setFile(null);
      onChange?.();
    } catch (err) {
      setError(err.response?.data?.detail || "Не удалось отправить.");
    } finally {
      setSubmitting(false);
    }
  };

  const payWithStripe = async () => {
    setError(null);
    try {
      setStripeSubmitting(true);
      const origin_url = window.location.origin;
      const res = await autoApi.post("/deposit/stripe/session", { origin_url });
      window.location.href = res.data.url;
    } catch (err) {
      setError(err.response?.data?.detail || "Не удалось создать сессию оплаты.");
      setStripeSubmitting(false);
    }
  };

  const s = deposit?.status ? STATUS[deposit.status] : null;

  return (
    <div className="auto-card" data-testid="deposit-card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ fontWeight: 600 }}>Депозит NZ$1,000</div>
          <div className="auto-muted" style={{ fontSize: 13 }}>
            Депозит требуется для участия в торгах. Один депозит — для всех ставок.
          </div>
        </div>
        {s && <span className={`auto-badge ${s.cls}`} data-testid="deposit-status-badge">{s.text}</span>}
      </div>

      {deposit?.status === "verified" ? (
        <div className="auto-muted" style={{ marginTop: 12, fontSize: 13 }}>
          Депозит подтверждён {deposit.updated_at ? new Date(deposit.updated_at).toLocaleString("ru-RU") : ""}.
        </div>
      ) : (
        <>
          <div className="auto-divider" />
          <div style={{ fontWeight: 600, marginBottom: 8 }}>Оплатить картой (Stripe)</div>
          <button
            type="button"
            className="auto-btn auto-btn-success"
            onClick={payWithStripe}
            disabled={stripeSubmitting}
            data-testid="deposit-stripe-btn"
          >
            {stripeSubmitting ? "Готовим сессию…" : "Оплатить NZ$1,000 онлайн"}
          </button>

          <div className="auto-divider" />
          <form onSubmit={submitProof} style={{ display: "grid", gap: 8 }} data-testid="deposit-upload-form">
            <div style={{ fontWeight: 600 }}>Загрузить подтверждение оплаты</div>
            <select className="auto-select" value={method} onChange={(e) => setMethod(e.target.value)} data-testid="deposit-method">
              <option value="bank_transfer">Банковский перевод</option>
              <option value="rub_transfer">Перевод в рублях</option>
              <option value="crypto">Крипто</option>
              <option value="manual">Иное</option>
            </select>
            <textarea
              className="auto-textarea"
              rows={3}
              placeholder="Комментарий: дата перевода, отправитель, банк и т.п."
              value={note}
              onChange={(e) => setNote(e.target.value)}
              data-testid="deposit-note"
            />
            <input
              type="file"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              data-testid="deposit-file"
              style={{ color: "var(--auto-muted)" }}
            />
            <button type="submit" className="auto-btn" disabled={submitting} data-testid="deposit-submit-btn">
              {submitting ? "Отправка…" : "Отправить на проверку"}
            </button>
            {success && <div className="auto-badge auto-badge-success" data-testid="deposit-success">{success}</div>}
            {error && <div className="auto-badge auto-badge-danger" data-testid="deposit-error">{error}</div>}
          </form>
        </>
      )}
      {deposit?.admin_note && (
        <div className="auto-muted" style={{ marginTop: 10, fontSize: 13 }} data-testid="deposit-admin-note">
          Комментарий администратора: {deposit.admin_note}
        </div>
      )}
    </div>
  );
}
