import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import autoApi from "../../services/autoApi";
import { formatRub } from "../../services/autoCurrency";
import { fmtPrice } from "./VehicleCard";
import LeadModal from "./LeadModal";

/* Three-stage engagement panel — replaces the old BidPanel.
 *
 * Stage 1 (visitor)        → "Выразить интерес" + "Зарегистрироваться"
 * Stage 2 (auth, no deposit)→ "Предложить цену" + "Внести депозит"
 * Stage 3 (deposit verified)→ "Подать ставку" / "Повысить ставку"
 *
 * AU vehicles or listing_type=inquiry_only skip Stage 3 entirely — only the
 * soft engagement actions are available.
 */
export default function EngagementPanel({
  vehicle,
  isAuthenticated,
  depositVerified,
  onPlaced,
  user,
}) {
  const [leadOpen, setLeadOpen] = useState(false);
  const [offerOpen, setOfferOpen] = useState(false);
  const [bidOpen, setBidOpen] = useState(false);

  const isAU = vehicle.country === "AU";
  const inquiryOnly = vehicle.listing_type === "inquiry_only";
  const bidsDisabled = isAU || inquiryOnly;
  const currentMaxNzd = vehicle.current_price_nzd || 0;

  // ---- Stage 1 — visitor (no auth) ----
  if (!isAuthenticated) {
    return (
      <div
        className="rounded-2xl border border-white/10 bg-[var(--ar-card)] p-5"
        data-testid="engagement-panel-visitor"
      >
        <div className="text-base font-bold text-white">Получить расчёт и условия</div>
        <p className="mt-1 text-sm text-gray-400">
          Оставьте контакт — мы рассчитаем стоимость под ключ до Владивостока и ответим в течение часа.
        </p>
        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <button
            onClick={() => setLeadOpen(true)}
            className="flex-1 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-500"
            data-testid="cta-express-interest"
          >
            Выразить интерес
          </button>
          <Link
            to="/"
            className="flex-1 rounded-xl border border-white/10 bg-white/5 px-5 py-3 text-center text-sm font-medium hover:bg-white/10"
            data-testid="cta-register"
          >
            Зарегистрироваться
          </Link>
        </div>
        <button
          onClick={() => setLeadOpen(true)}
          className="mt-2 w-full rounded-xl border border-white/10 bg-transparent px-5 py-3 text-sm hover:bg-white/5"
          data-testid="cta-request-quote"
        >
          Запросить расчёт под ключ
        </button>
        <LeadModal
          open={leadOpen}
          onClose={() => setLeadOpen(false)}
          vehicle={vehicle}
          source="vehicle_page"
          title="Выразить интерес"
          subtitle="Оставьте контакты — расскажем условия и пришлём расчёт."
        />
      </div>
    );
  }

  // ---- Stage 2 — authed, no deposit ----
  if (!depositVerified) {
    return (
      <div
        className="rounded-2xl border border-white/10 bg-[var(--ar-card)] p-5"
        data-testid="engagement-panel-no-deposit"
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-base font-bold text-white">Хотите купить этот авто?</div>
            <p className="mt-1 text-sm text-gray-400">
              Без депозита можно предложить свою цену — это <b>не ставка</b>, а ваш ориентир. Менеджер
              свяжется с вами и согласует условия. {!bidsDisabled && "Для подачи официальной ставки потребуется депозит."}
            </p>
          </div>
        </div>

        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <button
            onClick={() => setOfferOpen(true)}
            className="flex-1 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-500"
            data-testid="cta-make-offer"
          >
            Предложить цену
          </button>
          {!bidsDisabled && (
            <Link
              to="/auto/dashboard"
              className="flex-1 rounded-xl border border-blue-500/40 bg-blue-500/10 px-5 py-3 text-center text-sm font-semibold text-white hover:bg-blue-500/20"
              data-testid="cta-deposit"
            >
              Внести депозит NZ$1,000
            </Link>
          )}
        </div>

        {!bidsDisabled && (
          <div className="mt-3 rounded-lg bg-white/[0.03] px-3 py-2 text-[12px] text-gray-400">
            <b className="text-gray-300">Депозит NZ$1,000</b> — возвратный или зачётный. Засчитывается
            в покупку или остаётся на балансе для будущих ставок.
          </div>
        )}

        <OfferModal
          open={offerOpen}
          onClose={() => setOfferOpen(false)}
          vehicle={vehicle}
        />
      </div>
    );
  }

  // ---- Stage 3 — deposit verified, AU-restricted check ----
  if (bidsDisabled) {
    return (
      <div className="rounded-2xl border border-white/10 bg-[var(--ar-card)] p-5" data-testid="engagement-panel-au-inquiry">
        <div className="text-base font-bold text-white">Сделать предложение</div>
        <p className="mt-1 text-sm text-gray-400">
          {isAU
            ? "Автомобили из Австралии продаются по заявке: наш менеджер согласует цену и срок поставки."
            : "Этот лот доступен только по предложению — обычная ставка не применима."}
        </p>
        <button
          onClick={() => setOfferOpen(true)}
          className="mt-4 w-full rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-500"
          data-testid="cta-make-offer-au"
        >
          Предложить цену
        </button>
        <OfferModal open={offerOpen} onClose={() => setOfferOpen(false)} vehicle={vehicle} />
      </div>
    );
  }

  // ---- Stage 3 — verified, NZ auction ----
  return (
    <div className="rounded-2xl border border-white/10 bg-[var(--ar-card)] p-5" data-testid="engagement-panel-verified">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-base font-bold text-white">Подать ставку</div>
          <p className="mt-1 text-sm text-gray-400">
            Текущая максимальная ставка:{" "}
            <b className="text-white">{fmtPrice(currentMaxNzd)}</b>
            {" · "}
            <span className="text-gray-500">{formatRub(currentMaxNzd)} (ориентир)</span>
          </p>
        </div>
        <span className="rounded-full bg-[var(--ar-success)]/15 px-2.5 py-1 text-[11px] font-bold text-[var(--ar-success)]">
          Депозит ✓
        </span>
      </div>

      <button
        onClick={() => setBidOpen(true)}
        className="mt-4 w-full rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-500"
        data-testid="cta-submit-bid"
      >
        {currentMaxNzd > 0 ? "Повысить ставку" : "Подать ставку"}
      </button>

      <BidModal
        open={bidOpen}
        onClose={() => setBidOpen(false)}
        vehicle={vehicle}
        currentMaxNzd={currentMaxNzd}
        onPlaced={onPlaced}
      />
    </div>
  );
}

/* ---------- Offer modal (Предложение цены) ---------- */
function OfferModal({ open, onClose, vehicle }) {
  const [price, setPrice] = useState("");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!open) {
      setPrice("");
      setMsg("");
      setError(null);
      setDone(false);
    }
  }, [open]);

  if (!open) return null;

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    const v = parseFloat(price);
    if (!Number.isFinite(v) || v <= 0) {
      setError("Введите положительную сумму в NZ$.");
      return;
    }
    try {
      setBusy(true);
      await autoApi.post("/offers", {
        vehicle_id: vehicle.id,
        offer_price_nzd: v,
        message: msg.trim() || null,
      });
      setDone(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Не удалось отправить предложение.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm" onClick={onClose}>
      <div className="relative w-full max-w-md rounded-2xl border border-white/10 bg-[var(--ar-card)] p-6" onClick={(e) => e.stopPropagation()} data-testid="offer-modal">
        <button onClick={onClose} className="absolute right-3 top-3 rounded-lg p-2 text-gray-400 hover:bg-white/5">×</button>
        {done ? (
          <div className="py-6 text-center">
            <div className="mb-3 inline-flex h-14 w-14 items-center justify-center rounded-full bg-[var(--ar-success)]/20 text-3xl">✓</div>
            <h3 className="text-xl font-bold text-white">Предложение отправлено</h3>
            <p className="mt-2 text-sm text-gray-400">Менеджер свяжется с вами для согласования.</p>
            <button onClick={onClose} className="mt-5 rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white">Хорошо</button>
          </div>
        ) : (
          <form onSubmit={submit} className="space-y-4">
            <div>
              <h3 className="text-xl font-bold text-white">Предложение цены</h3>
              <p className="mt-1 text-sm text-gray-400">
                Это <b className="text-white">не ставка</b> — это ваше ориентировочное предложение. Менеджер
                свяжется в течение часа.
              </p>
            </div>
            <label className="block">
              <span className="mb-1 block text-xs uppercase tracking-wide text-gray-400">Ваше предложение, NZ$</span>
              <input
                className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-3 text-base text-white"
                required
                type="number"
                min="1"
                step="50"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="Например, 6500"
                data-testid="offer-price-input"
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-xs uppercase tracking-wide text-gray-400">Сообщение (необязательно)</span>
              <textarea
                rows={3}
                className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white"
                value={msg}
                onChange={(e) => setMsg(e.target.value)}
                placeholder="Срок, условия, дополнительные пожелания…"
                data-testid="offer-message-input"
              />
            </label>
            {error && <div className="rounded-lg bg-[var(--ar-danger)]/15 px-3 py-2 text-sm text-[#FF7A6F]" data-testid="offer-error">{error}</div>}
            <button type="submit" disabled={busy} className="w-full rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-60" data-testid="offer-submit-btn">
              {busy ? "Отправка…" : "Отправить предложение"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

/* ---------- Bid modal (Ставка — only deposit-verified) ---------- */
function BidModal({ open, onClose, vehicle, currentMaxNzd, onPlaced }) {
  const [amount, setAmount] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    if (!open) {
      setAmount("");
      setError(null);
      setSuccess(null);
    }
  }, [open]);

  if (!open) return null;

  const minSuggested = currentMaxNzd + 100;

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    const v = parseFloat(amount);
    if (!Number.isFinite(v) || v <= 0) {
      setError("Введите положительную сумму.");
      return;
    }
    try {
      setBusy(true);
      const res = await autoApi.post(`/vehicles/${vehicle.id}/bid`, { max_bid_nzd: v });
      setSuccess(`Ставка ${fmtPrice(v)} принята. Максимальная сейчас: ${fmtPrice(res.data.highest_bid_nzd)}.`);
      onPlaced?.(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Не удалось разместить ставку.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm" onClick={onClose}>
      <div className="relative w-full max-w-md rounded-2xl border border-white/10 bg-[var(--ar-card)] p-6" onClick={(e) => e.stopPropagation()} data-testid="bid-modal">
        <button onClick={onClose} className="absolute right-3 top-3 rounded-lg p-2 text-gray-400 hover:bg-white/5">×</button>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <h3 className="text-xl font-bold text-white">Подать ставку</h3>
            <p className="mt-1 text-sm text-gray-400">
              Это <b className="text-white">официальная ставка</b>. После принятия торгов она исполняется автоматически
              в пределах указанной максимальной суммы.
            </p>
          </div>
          <div className="rounded-lg bg-white/[0.03] p-3 text-sm text-gray-400">
            Текущая макс. ставка: <b className="text-white">{fmtPrice(currentMaxNzd)}</b>
            <br />
            Минимальный шаг: NZ$100 ⇒ от <b className="text-white">{fmtPrice(minSuggested)}</b>
          </div>
          <label className="block">
            <span className="mb-1 block text-xs uppercase tracking-wide text-gray-400">Ваш максимум, NZ$</span>
            <input
              className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-3 text-base text-white"
              required
              type="number"
              min={minSuggested}
              step="50"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              data-testid="bid-amount-input"
            />
          </label>
          {error && <div className="rounded-lg bg-[var(--ar-danger)]/15 px-3 py-2 text-sm text-[#FF7A6F]" data-testid="bid-error">{error}</div>}
          {success && <div className="rounded-lg bg-[var(--ar-success)]/15 px-3 py-2 text-sm text-[#7BE7A4]" data-testid="bid-success">{success}</div>}
          <button type="submit" disabled={busy} className="w-full rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-60" data-testid="bid-submit-btn">
            {busy ? "Отправка…" : "Подтвердить ставку"}
          </button>
        </form>
      </div>
    </div>
  );
}
