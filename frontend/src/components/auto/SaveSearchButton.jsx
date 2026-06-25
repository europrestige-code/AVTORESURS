import React, { useState } from "react";
import { Bell, BellRing, Mail, Send } from "lucide-react";
import autoApi from "../../services/autoApi";
import { useAuth } from "../../contexts/AuthContext";

/**
 * Floating «Сохранить поиск» CTA — opens a tiny modal that lets a logged-in
 * user save the current catalog filters and choose notification channels.
 *
 * Unauthenticated visitors see a prompt to log in instead.
 */
export default function SaveSearchButton({ filters, total }) {
  const { user, isAuthenticated } = useAuth();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [channels, setChannels] = useState({ email: true, telegram: false });
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState(null);

  const toApiFilters = () => {
    // Translate the catalog UI filter keys → SavedSearchFilters fields.
    const f = filters || {};
    return {
      country: f.country || null,
      body_type: f.body_type || null,
      make: f.make || null,
      model: f.model || null,
      year_from: f.year_from ? Number(f.year_from) : null,
      year_to: f.year_to ? Number(f.year_to) : null,
      price_from_nzd: f.price_from ? Number(f.price_from) : null,
      price_to_nzd: f.price_to ? Number(f.price_to) : null,
      mileage_to_km: f.mileage_to ? Number(f.mileage_to) : null,
      damage_only: f.damage_type ? true : null,
      keywords: f.search || null,
    };
  };

  const guessName = () => {
    const parts = [];
    if (filters?.make) parts.push(filters.make);
    if (filters?.model) parts.push(filters.model);
    if (filters?.body_type) parts.push(filters.body_type);
    if (filters?.country) parts.push(filters.country);
    if (filters?.price_to) parts.push(`до NZ$${filters.price_to}`);
    return parts.join(" · ") || `Подписка ${new Date().toLocaleDateString("ru-RU")}`;
  };

  const submit = async () => {
    if (!isAuthenticated) {
      setError("Войдите в аккаунт, чтобы сохранить поиск.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await autoApi.post("/saved-searches", {
        name: (name || guessName()).slice(0, 80),
        filters: toApiFilters(),
        channels,
      });
      setDone(true);
    } catch (e) {
      setError(
        e.response?.data?.detail ||
          "Не удалось сохранить. Попробуйте ещё раз через минуту."
      );
    } finally {
      setBusy(false);
    }
  };

  const close = () => {
    setOpen(false);
    setDone(false);
    setName("");
    setError(null);
  };

  return (
    <>
      <button
        type="button"
        className="auto-btn auto-btn--ghost save-search-btn"
        onClick={() => setOpen(true)}
        data-testid="save-search-btn"
        title="Получать уведомления о новых авто по этим параметрам"
      >
        <Bell size={14} style={{ marginRight: 6 }} />
        Сохранить поиск
      </button>
      {open && (
        <div className="save-search-modal" data-testid="save-search-modal">
          <div className="save-search-modal__panel">
            <div className="save-search-modal__head">
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <BellRing size={18} className="text-blue-400" />
                <div style={{ fontWeight: 700 }}>Сохранить поиск</div>
              </div>
              <button
                type="button"
                className="auto-btn auto-btn--ghost"
                onClick={close}
                data-testid="save-search-close"
              >
                ×
              </button>
            </div>
            {!done ? (
              <>
                <div className="auto-muted" style={{ fontSize: 13, marginBottom: 14 }}>
                  Подпишитесь — и мы пришлём уведомление, как только появится
                  авто, подходящее под эти параметры (
                  {typeof total === "number" ? `сейчас ${total} совпадений` : "обновляется автоматически"}).
                </div>
                {!isAuthenticated && (
                  <div className="save-search-modal__warn" data-testid="save-search-need-login">
                    Чтобы сохранить поиск, войдите в аккаунт.
                  </div>
                )}
                <label className="quiz-field">
                  <span>Название</span>
                  <input
                    className="auto-input"
                    placeholder={guessName()}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    data-testid="save-search-name"
                  />
                </label>
                <div className="quiz-group-label">Каналы уведомлений</div>
                <div className="save-search-channels">
                  <label className="save-search-channel">
                    <input
                      type="checkbox"
                      checked={channels.email}
                      onChange={(e) => setChannels((c) => ({ ...c, email: e.target.checked }))}
                      data-testid="save-search-email"
                    />
                    <Mail size={14} /> Email
                    <span className="auto-muted">{user?.email}</span>
                  </label>
                  <label className="save-search-channel">
                    <input
                      type="checkbox"
                      checked={channels.telegram}
                      onChange={(e) => setChannels((c) => ({ ...c, telegram: e.target.checked }))}
                      data-testid="save-search-telegram"
                    />
                    <Send size={14} /> Telegram
                    <span className="auto-muted">привяжите бот в «Мои подписки»</span>
                  </label>
                </div>
                {error && (
                  <div className="quiz-step__error" data-testid="save-search-error">
                    {error}
                  </div>
                )}
                <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
                  <button
                    type="button"
                    className="auto-btn"
                    onClick={submit}
                    disabled={busy || !isAuthenticated}
                    data-testid="save-search-submit"
                  >
                    {busy ? "Сохраняем…" : "Подписаться"}
                  </button>
                  <button
                    type="button"
                    className="auto-btn auto-btn--ghost"
                    onClick={close}
                  >
                    Отмена
                  </button>
                </div>
              </>
            ) : (
              <div data-testid="save-search-done">
                <div style={{ fontWeight: 700, marginBottom: 8 }}>
                  ✅ Подписка сохранена
                </div>
                <div className="auto-muted" style={{ fontSize: 13, marginBottom: 14 }}>
                  Мы пришлём уведомление при первом новом совпадении. Все
                  подписки доступны в разделе «Мои подписки».
                </div>
                <button type="button" className="auto-btn" onClick={close}>
                  Готово
                </button>
              </div>
            )}
          </div>
          <div className="save-search-modal__backdrop" onClick={close} />
        </div>
      )}
    </>
  );
}
