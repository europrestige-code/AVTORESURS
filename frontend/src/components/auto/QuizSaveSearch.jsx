import React, { useState } from "react";
import { Bell, Mail, Send } from "lucide-react";
import autoApi from "../../services/autoApi";
import { useAuth } from "../../contexts/AuthContext";

/**
 * Inline «Сохранить поиск» CTA shown at the end of the AI quiz.
 *
 * Converts the answered quiz form + lead (budget_nzd_max, body_types[0],
 * country, repair) into a SavedSearch and lets the user choose Email /
 * Telegram channels. Visually aligned with the rest of the quiz —
 * no flashy icons, just the existing `auto-btn` + a small panel.
 */
export default function QuizSaveSearch({ form, lead }) {
  const { user, isAuthenticated } = useAuth();
  const [open, setOpen] = useState(false);
  const [channels, setChannels] = useState({ email: true, telegram: false });
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState(null);

  const guessName = () => {
    const bits = [];
    if (form.body_types?.length) bits.push(form.body_types[0]);
    if (form.country) bits.push(form.country);
    if (lead?.budget_rub_max) {
      bits.push(`до ${Math.round(lead.budget_rub_max / 1_000_000)} млн ₽`);
    }
    return bits.join(" · ") || `Подписка ${new Date().toLocaleDateString("ru-RU")}`;
  };

  const buildFilters = () => ({
    country: form.country || null,
    body_type: form.body_types?.[0] || null,
    make: null,
    model: null,
    year_from: null,
    year_to: null,
    price_from_nzd: null,
    price_to_nzd: lead?.budget_nzd_max ? Math.round(lead.budget_nzd_max) : null,
    mileage_to_km: null,
    damage_only: form.repair === "any" ? true : null,
    keywords: form.notes || null,
  });

  const subscribe = async () => {
    if (!isAuthenticated) {
      setError("Войдите в аккаунт, чтобы получать уведомления.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await autoApi.post("/saved-searches", {
        name: guessName().slice(0, 80),
        filters: buildFilters(),
        channels,
      });
      setDone(true);
    } catch (e) {
      setError(
        e.response?.data?.detail ||
          "Не удалось сохранить. Попробуйте через минуту."
      );
    } finally {
      setBusy(false);
    }
  };

  if (done) {
    return (
      <div className="quiz-save quiz-save--done" data-testid="quiz-save-done">
        Подписка сохранена. Мы пришлём уведомление, как только появится лот по
        вашим параметрам.
      </div>
    );
  }

  if (!open) {
    return (
      <div className="quiz-save" data-testid="quiz-save">
        <div className="quiz-save__head">
          <div className="quiz-save__title">
            Получать уведомления о новых подходящих лотах?
          </div>
          <div className="quiz-save__sub auto-muted">
            Мы сохраним эти параметры и пришлём первое же совпадение —
            на email или в Telegram. Никакого спама.
          </div>
        </div>
        <div className="quiz-save__cta">
          <button
            type="button"
            className="auto-btn"
            onClick={() => setOpen(true)}
            data-testid="quiz-save-open"
          >
            <Bell size={14} style={{ marginRight: 6 }} />
            Подписаться на новые лоты
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="quiz-save quiz-save--open" data-testid="quiz-save-form">
      <div className="quiz-save__head">
        <div className="quiz-save__title">Каналы уведомлений</div>
        <div className="quiz-save__sub auto-muted">
          Подписка «{guessName()}»
        </div>
      </div>

      {!isAuthenticated && (
        <div className="quiz-save__warn" data-testid="quiz-save-need-login">
          Чтобы сохранить подписку, войдите в аккаунт — это займёт минуту.
        </div>
      )}

      <div className="quiz-save__channels">
        <label className="quiz-save__channel">
          <input
            type="checkbox"
            checked={channels.email}
            onChange={(e) => setChannels((c) => ({ ...c, email: e.target.checked }))}
            data-testid="quiz-save-email"
          />
          <Mail size={14} />
          <span>Email</span>
          {user?.email && <span className="auto-muted">{user.email}</span>}
        </label>
        <label className="quiz-save__channel">
          <input
            type="checkbox"
            checked={channels.telegram}
            onChange={(e) => setChannels((c) => ({ ...c, telegram: e.target.checked }))}
            data-testid="quiz-save-telegram"
          />
          <Send size={14} />
          <span>Telegram</span>
          <span className="auto-muted">привяжите бот в «Мои подписки»</span>
        </label>
      </div>

      {error && (
        <div className="quiz-step__error" data-testid="quiz-save-error">
          {error}
        </div>
      )}

      <div className="quiz-save__actions">
        <button
          type="button"
          className="auto-btn"
          onClick={subscribe}
          disabled={busy || !isAuthenticated}
          data-testid="quiz-save-submit"
        >
          {busy ? "Сохраняем…" : "Подписаться"}
        </button>
        <button
          type="button"
          className="auto-btn auto-btn--ghost"
          onClick={() => setOpen(false)}
          data-testid="quiz-save-cancel"
        >
          Не сейчас
        </button>
      </div>
    </div>
  );
}
