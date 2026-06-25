import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Sparkles } from "lucide-react";
import autoApi from "../../services/autoApi";
import { formatRub } from "../../services/autoCurrency";

/**
 * AI-подборщик — multi-step quiz rendered inline inside the chat panel.
 *
 * Flow:
 *   1. Цель покупки
 *   2. Тип кузова (multi)
 *   3. Бюджет под ключ (RUB bucket)
 *   4. Страна и срочность
 *   5. Контакты + город
 *   → POST /api/auto/quiz/submit → render matches as cards inside the chat
 */
export default function QuizFlow({ onClose, onSubmitted }) {
  const [meta, setMeta] = useState(null);
  const [step, setStep] = useState(0);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [form, setForm] = useState({
    purpose: null,
    body_types: [],
    budget_key: null,
    country: null,
    urgency: null,
    name: "",
    contact: "",
    city: "",
    notes: "",
  });
  const liveRef = useRef(null);

  useEffect(() => {
    autoApi
      .get("/quiz/meta")
      .then((r) => setMeta(r.data))
      .catch(() => setError("Не удалось загрузить параметры подбора."));
  }, []);

  useEffect(() => {
    if (liveRef.current) liveRef.current.scrollIntoView({ behavior: "smooth" });
  }, [step, result]);

  const BODY_OPTS = [
    { key: "sedan",       label: "Седан" },
    { key: "suv",         label: "Внедорожник" },
    { key: "utility",     label: "Пикап" },
    { key: "wagon",       label: "Универсал" },
    { key: "hatchback",   label: "Хэтчбек" },
    { key: "van",         label: "Фургон" },
    { key: "coupe",       label: "Купе" },
    { key: "convertible", label: "Кабриолет" },
  ];

  const update = (patch) => setForm((f) => ({ ...f, ...patch }));
  const next = () => setStep((s) => Math.min(s + 1, 4));
  const back = () => setStep((s) => Math.max(s - 1, 0));

  const submit = async () => {
    if (!form.name.trim() || !form.contact.trim()) {
      setError("Заполните имя и контакт (телефон, Telegram или email).");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const r = await autoApi.post("/quiz/submit", { ...form, limit: 6 });
      setResult(r.data);
      onSubmitted?.(r.data);
    } catch (e) {
      setError(
        e.response?.data?.detail ||
          "Не удалось отправить заявку. Напишите нам в WhatsApp +64 21 425 233."
      );
    } finally {
      setBusy(false);
    }
  };

  if (error && !meta) {
    return (
      <div className="quiz-flow" data-testid="quiz-flow">
        <div className="quiz-flow__error">{error}</div>
      </div>
    );
  }
  if (!meta) {
    return (
      <div className="quiz-flow" data-testid="quiz-flow">
        <div className="quiz-flow__loading">Готовлю АИ-подборщик…</div>
      </div>
    );
  }

  if (result) {
    return (
      <div className="quiz-flow quiz-flow--result" data-testid="quiz-result">
        <div className="quiz-flow__title">
          Спасибо, {form.name.split(" ")[0] || "друг"}! Подобрал{" "}
          {result.match_count} вариант{result.match_count === 1 ? "" : "а"}.
        </div>
        <div className="quiz-flow__sub auto-muted">
          Менеджер свяжется в течение часа. Ниже — лучшие совпадения по вашим
          параметрам:
        </div>
        <div className="quiz-flow__matches">
          {result.matches.length === 0 && (
            <div className="quiz-flow__empty auto-muted">
              Точных совпадений сейчас нет — мы пришлём подборку, как только
              появятся подходящие лоты.
            </div>
          )}
          {result.matches.map((v) => (
            <Link
              key={v.id}
              to={`/auto/vehicle/${v.id}`}
              className="quiz-match"
              data-testid={`quiz-match-${v.id}`}
              onClick={onClose}
            >
              <div className="quiz-match__media">
                {v.image ? (
                  <img src={v.image} alt={v.title_ru} loading="lazy" />
                ) : (
                  <div className="quiz-match__placeholder">Нет фото</div>
                )}
              </div>
              <div className="quiz-match__body">
                <div className="quiz-match__title">{v.title_ru}</div>
                <div className="quiz-match__meta auto-muted">
                  {v.year} · {v.country}
                  {v.mileage_km ? ` · ${Math.round(v.mileage_km / 1000)} тыс. км` : ""}
                </div>
                <div className="quiz-match__price">
                  {v.current_price_nzd
                    ? formatRub(v.current_price_nzd)
                    : v.ai_estimate?.recommended_max_bid_nzd
                      ? `до ${formatRub(v.ai_estimate.recommended_max_bid_nzd)}`
                      : "Уточняем"}
                </div>
              </div>
            </Link>
          ))}
        </div>
        <button
          type="button"
          className="auto-btn auto-btn--ghost quiz-flow__close"
          onClick={onClose}
          data-testid="quiz-close-btn"
        >
          Закрыть подборщик
        </button>
        <span ref={liveRef} />
      </div>
    );
  }

  const toggleBody = (key) => {
    setForm((f) => {
      const has = f.body_types.includes(key);
      return {
        ...f,
        body_types: has
          ? f.body_types.filter((k) => k !== key)
          : [...f.body_types, key],
      };
    });
  };

  return (
    <div className="quiz-flow" data-testid="quiz-flow">
      <div className="quiz-flow__header">
        <Sparkles size={14} /> АИ-подборщик · шаг {step + 1} из 5
      </div>

      {step === 0 && (
        <QuizStep
          step={step} busy={busy} error={error}
          onBack={back} onNext={next} onSubmit={submit}
          canSubmit={form.name.trim() && form.contact.trim()}
          title="Для каких задач выбираете авто?"
          hint="Подскажу варианты, которые подходят под цель."
          canNext={!!form.purpose}
        >
          <div className="quiz-pills">
            {meta.purposes.map((p) => (
              <button
                key={p.key}
                type="button"
                className={`quiz-pill ${form.purpose === p.key ? "is-active" : ""}`}
                onClick={() => update({ purpose: p.key })}
                data-testid={`quiz-purpose-${p.key}`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </QuizStep>
      )}

      {step === 1 && (
        <QuizStep
          step={step} busy={busy} error={error}
          onBack={back} onNext={next} onSubmit={submit}
          canSubmit={form.name.trim() && form.contact.trim()}
          title="Какой кузов предпочтительнее?"
          hint="Можно выбрать несколько. Если без разницы — пропустите."
          canNext={true}
        >
          <div className="quiz-pills">
            {BODY_OPTS.map((b) => (
              <button
                key={b.key}
                type="button"
                className={`quiz-pill ${form.body_types.includes(b.key) ? "is-active" : ""}`}
                onClick={() => toggleBody(b.key)}
                data-testid={`quiz-body-${b.key}`}
              >
                {b.label}
              </button>
            ))}
          </div>
        </QuizStep>
      )}

      {step === 2 && (
        <QuizStep
          step={step} busy={busy} error={error}
          onBack={back} onNext={next} onSubmit={submit}
          canSubmit={form.name.trim() && form.contact.trim()}
          title="Какой бюджет «под ключ» в РФ?"
          hint="Учитываем аукционную цену, доставку и таможню."
          canNext={!!form.budget_key}
        >
          <div className="quiz-pills">
            {meta.budgets.map((b) => (
              <button
                key={b.key}
                type="button"
                className={`quiz-pill ${form.budget_key === b.key ? "is-active" : ""}`}
                onClick={() => update({ budget_key: b.key })}
                data-testid={`quiz-budget-${b.key}`}
              >
                {b.label}
              </button>
            ))}
          </div>
        </QuizStep>
      )}

      {step === 3 && (
        <QuizStep
          step={step} busy={busy} error={error}
          onBack={back} onNext={next} onSubmit={submit}
          canSubmit={form.name.trim() && form.contact.trim()}
          title="Откуда удобнее везти и насколько срочно?"
          canNext={!!form.urgency}
        >
          <div className="quiz-group-label">Страна аукциона</div>
          <div className="quiz-pills">
            {meta.countries.map((c) => (
              <button
                key={String(c.key)}
                type="button"
                className={`quiz-pill ${form.country === c.key ? "is-active" : ""}`}
                onClick={() => update({ country: c.key })}
                data-testid={`quiz-country-${c.key || "any"}`}
              >
                {c.label}
              </button>
            ))}
          </div>
          <div className="quiz-group-label">Срочность</div>
          <div className="quiz-pills">
            {meta.urgencies.map((u) => (
              <button
                key={u.key}
                type="button"
                className={`quiz-pill ${form.urgency === u.key ? "is-active" : ""}`}
                onClick={() => update({ urgency: u.key })}
                data-testid={`quiz-urgency-${u.key}`}
              >
                {u.label}
              </button>
            ))}
          </div>
        </QuizStep>
      )}

      {step === 4 && (
        <QuizStep
          step={step} busy={busy} error={error}
          onBack={back} onNext={next} onSubmit={submit}
          canSubmit={form.name.trim() && form.contact.trim()}
          title="Куда отправить подборку?"
          hint="Запишем заявку и подберём авто под параметры. Никакого спама."
          canNext={!!form.name && !!form.contact}
        >
          <div className="quiz-fields">
            <label className="quiz-field">
              <span>Имя</span>
              <input
                className="auto-input"
                value={form.name}
                onChange={(e) => update({ name: e.target.value })}
                placeholder="Как к вам обращаться?"
                data-testid="quiz-name-input"
              />
            </label>
            <label className="quiz-field">
              <span>Контакт</span>
              <input
                className="auto-input"
                value={form.contact}
                onChange={(e) => update({ contact: e.target.value })}
                placeholder="Телефон, Telegram или email"
                data-testid="quiz-contact-input"
              />
            </label>
            <label className="quiz-field">
              <span>Город доставки в РФ</span>
              <input
                className="auto-input"
                value={form.city}
                onChange={(e) => update({ city: e.target.value })}
                placeholder="Например, Владивосток"
                data-testid="quiz-city-input"
              />
            </label>
            <label className="quiz-field">
              <span>Комментарий <span className="auto-muted">(необязательно)</span></span>
              <textarea
                className="auto-input"
                rows={2}
                value={form.notes}
                onChange={(e) => update({ notes: e.target.value })}
                placeholder="Особые пожелания: марка, цвет, год…"
                data-testid="quiz-notes-input"
              />
            </label>
          </div>
        </QuizStep>
      )}
      <span ref={liveRef} />
    </div>
  );
}

function QuizStep({
  step, title, hint, children, canNext, busy, error,
  onBack, onNext, onSubmit, canSubmit,
}) {
  return (
    <div className="quiz-step" data-testid={`quiz-step-${step}`}>
      <div className="quiz-step__title">{title}</div>
      {hint && <div className="quiz-step__hint auto-muted">{hint}</div>}
      <div className="quiz-step__body">{children}</div>
      {error && (
        <div className="quiz-step__error" data-testid="quiz-step-error">
          {error}
        </div>
      )}
      <div className="quiz-step__nav">
        {step > 0 && (
          <button
            type="button"
            className="auto-btn auto-btn--ghost"
            onClick={onBack}
            disabled={busy}
            data-testid="quiz-back-btn"
          >
            Назад
          </button>
        )}
        {step < 4 && (
          <button
            type="button"
            className="auto-btn"
            onClick={onNext}
            disabled={!canNext || busy}
            data-testid="quiz-next-btn"
          >
            Далее
          </button>
        )}
        {step === 4 && (
          <button
            type="button"
            className="auto-btn"
            onClick={onSubmit}
            disabled={busy || !canSubmit}
            data-testid="quiz-submit-btn"
          >
            {busy ? "Подбираю…" : "Подобрать авто"}
          </button>
        )}
      </div>
    </div>
  );
}
