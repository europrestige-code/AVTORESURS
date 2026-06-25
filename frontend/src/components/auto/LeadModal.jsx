import React, { useState, useEffect } from "react";
import autoApi from "../../services/autoApi";

/* Lead-capture modal — minimal friction.
 * Used by:
 *   - public visitor clicking "Выразить интерес" / "Запросить расчёт"
 *   - "Хотите расчёт под ключ?" CTAs
 * Captures: name + phone (required) + city + budget + message.
 * Posts to POST /api/auto/interests — works without auth.
 */
export default function LeadModal({
  open,
  onClose,
  vehicle = null,
  source = "lead_modal",
  title = "Расчёт под ключ",
  subtitle = "Оставьте контакты — Татьяна свяжется с вами в течение часа.",
}) {
  const [form, setForm] = useState({
    name: "",
    phone: "",
    email: "",
    city: "",
    budget_nzd: "",
    message: "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!open) {
      setError(null);
      setDone(false);
      setBusy(false);
    }
  }, [open]);

  if (!open) return null;

  const update = (k) => (e) => setForm((p) => ({ ...p, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!form.name.trim() || !form.phone.trim()) {
      setError("Укажите имя и телефон.");
      return;
    }
    try {
      setBusy(true);
      await autoApi.post("/interests", {
        vehicle_id: vehicle?.id,
        name: form.name.trim(),
        phone: form.phone.trim(),
        email: form.email.trim() || null,
        city: form.city.trim() || null,
        budget_nzd: form.budget_nzd ? Number(form.budget_nzd) : null,
        message: form.message.trim() || null,
        source,
      });
      setDone(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Не удалось отправить. Попробуйте ещё раз.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-[80] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
      onClick={onClose}
      data-testid="lead-modal-backdrop"
    >
      <div
        className="relative w-full max-w-lg rounded-2xl border border-white/10 bg-[#0D111A] p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
        data-testid="lead-modal"
      >
        <button
          onClick={onClose}
          className="absolute right-3 top-3 rounded-lg p-2 text-gray-400 hover:bg-white/5 hover:text-white"
          aria-label="Закрыть"
          data-testid="lead-modal-close"
        >
          ×
        </button>
        {done ? (
          <div className="py-6 text-center" data-testid="lead-modal-success">
            <div className="mb-3 inline-flex h-14 w-14 items-center justify-center rounded-full bg-[#00C853]/20 text-3xl">
              ✓
            </div>
            <h3 className="text-xl font-bold text-white">Заявка отправлена</h3>
            <p className="mt-2 text-sm text-gray-400">
              Татьяна свяжется с вами в течение часа в рабочее время.
            </p>
            <button
              className="mt-5 rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white hover:bg-blue-500"
              onClick={onClose}
            >
              Хорошо
            </button>
          </div>
        ) : (
          <form onSubmit={submit} className="space-y-4">
            <div>
              <h3 className="text-xl font-bold text-white">{title}</h3>
              <p className="mt-1 text-sm text-gray-400">{subtitle}</p>
            </div>

            {vehicle && (
              <div className="rounded-lg border border-white/10 bg-white/[0.03] p-3 text-sm">
                <div className="text-gray-400">Интересует:</div>
                <div className="font-semibold text-white">
                  {vehicle.title_ru ||
                    `${vehicle.year || ""} ${vehicle.make || ""} ${vehicle.model || ""}`.trim()}
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <Field label="Имя*" testid="lead-name">
                <input className="input" required value={form.name} onChange={update("name")} data-testid="lead-name-input" />
              </Field>
              <Field label="Телефон / WhatsApp*" testid="lead-phone">
                <input
                  className="input"
                  required
                  type="tel"
                  placeholder="+7…"
                  value={form.phone}
                  onChange={update("phone")}
                  data-testid="lead-phone-input"
                />
              </Field>
              <Field label="Email">
                <input
                  className="input"
                  type="email"
                  value={form.email}
                  onChange={update("email")}
                  data-testid="lead-email-input"
                />
              </Field>
              <Field label="Город">
                <input
                  className="input"
                  value={form.city}
                  onChange={update("city")}
                  data-testid="lead-city-input"
                />
              </Field>
              <Field label="Бюджет NZ$">
                <input
                  className="input"
                  type="number"
                  min="0"
                  step="500"
                  value={form.budget_nzd}
                  onChange={update("budget_nzd")}
                  data-testid="lead-budget-input"
                />
              </Field>
            </div>

            <Field label="Сообщение">
              <textarea
                className="input min-h-[72px]"
                rows={3}
                value={form.message}
                onChange={update("message")}
                placeholder="Например: интересует целый кроссовер до ₽1.5 млн под ключ"
                data-testid="lead-message-input"
              />
            </Field>

            {error && (
              <div className="rounded-lg bg-[#FF3B30]/15 px-3 py-2 text-sm text-[#FF7A6F]" data-testid="lead-error">
                {error}
              </div>
            )}

            <div className="flex flex-wrap gap-2">
              <button
                type="submit"
                disabled={busy}
                className="flex-1 rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-60"
                data-testid="lead-submit-btn"
              >
                {busy ? "Отправка…" : "Отправить заявку"}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="rounded-xl border border-white/10 bg-white/5 px-5 py-3 text-sm hover:bg-white/10"
              >
                Отмена
              </button>
            </div>

            <p className="text-[11px] text-gray-500">
              Нажимая «Отправить», вы соглашаетесь на обработку персональных данных.
            </p>
          </form>
        )}
        <style>{`
          .input {
            width: 100%;
            border-radius: 10px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.1);
            padding: 10px 12px;
            font-size: 14px;
            color: #fff;
          }
          .input:focus { outline: none; border-color: #0066ff; box-shadow: 0 0 0 2px rgba(0,102,255,0.2); }
        `}</style>
      </div>
    </div>
  );
}

function Field({ label, children, testid }) {
  return (
    <label className="block" data-testid={testid}>
      <span className="mb-1 block text-xs uppercase tracking-wide text-gray-400">{label}</span>
      {children}
    </label>
  );
}
