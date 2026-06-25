import React, { useCallback, useEffect, useState } from "react";
import { Bell, BellOff, Trash2, Send, Mail, RefreshCw, QrCode } from "lucide-react";
import autoApi from "../../services/autoApi";
import { useAuth } from "../../contexts/AuthContext";

/** «Мои подписки» — list of saved searches + Telegram-binding controls. */
export default function MySearches() {
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tgStatus, setTgStatus] = useState(null);
  const [tgLink, setTgLink] = useState(null);

  const load = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    try {
      const [r, s] = await Promise.all([
        autoApi.get("/saved-searches"),
        autoApi.get("/telegram/binding-status"),
      ]);
      setItems(r.data?.items || []);
      setTgStatus(s.data);
    } catch {
      // best-effort
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => { load(); }, [load]);

  const toggle = async (id, enabled) => {
    await autoApi.patch(`/saved-searches/${id}/toggle`, { enabled });
    load();
  };
  const remove = async (id) => {
    if (!window.confirm("Удалить подписку?")) return;
    await autoApi.delete(`/saved-searches/${id}`);
    load();
  };

  const requestTelegramBinding = async () => {
    const r = await autoApi.post("/telegram/start-binding");
    setTgLink(r.data);
  };

  const unbindTelegram = async () => {
    if (!window.confirm("Отвязать Telegram?")) return;
    await autoApi.post("/telegram/unbind");
    setTgLink(null);
    load();
  };

  if (authLoading) return <div className="auto-section auto-muted">Загружаем…</div>;
  if (!isAuthenticated) {
    return (
      <div className="auto-section auto-card" data-testid="my-searches-need-login">
        <div style={{ fontWeight: 600 }}>Войдите в аккаунт</div>
        <div className="auto-muted">Раздел «Мои подписки» доступен после входа.</div>
      </div>
    );
  }

  return (
    <div className="auto-section my-searches" data-testid="my-searches">
      <h1 style={{ fontSize: 28, marginTop: 0 }}>Мои подписки</h1>
      <div className="auto-muted" style={{ marginBottom: 16, maxWidth: 700 }}>
        Сохранённые поиски — мы каждые 15 минут проверяем новые поступления и
        пришлём уведомление по email и/или в Telegram, как только появится
        подходящее авто.
      </div>

      <div className="my-searches__tg auto-card" data-testid="my-searches-tg">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
          <div>
            <div style={{ fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
              <Send size={16} className="text-blue-400" /> Уведомления в Telegram
            </div>
            <div className="auto-muted" style={{ fontSize: 12, marginTop: 4 }}>
              {tgStatus?.bound
                ? "Бот привязан — будем присылать новые лоты прямо в чат."
                : "Привяжите бота, чтобы получать push-уведомления вместе с email."}
            </div>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {tgStatus?.bound ? (
              <button
                type="button"
                className="auto-btn auto-btn--ghost"
                onClick={unbindTelegram}
                data-testid="my-searches-tg-unbind"
              >
                Отвязать
              </button>
            ) : (
              <button
                type="button"
                className="auto-btn"
                onClick={requestTelegramBinding}
                data-testid="my-searches-tg-bind"
              >
                <QrCode size={14} style={{ marginRight: 6 }} />
                Привязать Telegram
              </button>
            )}
          </div>
        </div>
        {tgLink && !tgStatus?.bound && (
          <div className="my-searches__tg-link" data-testid="my-searches-tg-link">
            <div className="auto-muted" style={{ fontSize: 12, marginBottom: 6 }}>
              Откройте ссылку в Telegram и нажмите «Start» — мы автоматически
              привяжем чат к вашему аккаунту:
            </div>
            <a
              href={tgLink.deep_link}
              target="_blank"
              rel="noopener noreferrer"
              className="auto-btn"
              data-testid="my-searches-tg-open"
            >
              Открыть {tgLink.bot_username}
            </a>
            <button
              type="button"
              className="auto-btn auto-btn--ghost"
              onClick={load}
              style={{ marginLeft: 8 }}
              data-testid="my-searches-tg-recheck"
            >
              <RefreshCw size={14} style={{ marginRight: 6 }} /> Проверить
            </button>
          </div>
        )}
      </div>

      <div style={{ marginTop: 20 }}>
        {loading ? (
          <div className="auto-card auto-muted">Загружаем подписки…</div>
        ) : items.length === 0 ? (
          <div className="auto-card auto-muted" data-testid="my-searches-empty">
            Пока нет ни одной подписки. Откройте каталог, настройте фильтры и
            нажмите «Сохранить поиск».
          </div>
        ) : (
          <div className="my-searches__list">
            {items.map((s) => (
              <div
                key={s.id}
                className="my-searches__item auto-card"
                data-testid={`my-searches-item-${s.id}`}
              >
                <div className="my-searches__head">
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 16 }}>{s.name}</div>
                    <div className="auto-muted" style={{ fontSize: 12 }}>
                      Создана {s.created_at ? new Date(s.created_at).toLocaleDateString("ru-RU") : "—"}
                      {" · "}
                      Совпадений отправлено: {s.notify_count || 0}
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                    {s.channels?.email && (
                      <span className="auto-badge" title="Email включён"><Mail size={11} style={{ marginRight: 4 }} />Email</span>
                    )}
                    {s.channels?.telegram && (
                      <span className="auto-badge auto-badge-primary" title="Telegram включён"><Send size={11} style={{ marginRight: 4 }} />TG</span>
                    )}
                    <button
                      type="button"
                      className="auto-btn auto-btn--ghost"
                      onClick={() => toggle(s.id, !s.enabled)}
                      data-testid={`my-searches-toggle-${s.id}`}
                      title={s.enabled ? "Поставить на паузу" : "Включить"}
                    >
                      {s.enabled ? <Bell size={14} /> : <BellOff size={14} />}
                    </button>
                    <button
                      type="button"
                      className="auto-btn auto-btn--ghost"
                      onClick={() => remove(s.id)}
                      data-testid={`my-searches-delete-${s.id}`}
                      title="Удалить"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
                <div className="my-searches__filters">
                  {renderFilters(s.filters)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function renderFilters(f) {
  if (!f) return null;
  const tags = [];
  if (f.country) tags.push({ k: "Страна", v: f.country });
  if (f.body_type) tags.push({ k: "Кузов", v: f.body_type });
  if (f.make) tags.push({ k: "Марка", v: f.make });
  if (f.model) tags.push({ k: "Модель", v: f.model });
  if (f.year_from || f.year_to) tags.push({ k: "Год", v: `${f.year_from || "…"}–${f.year_to || "…"}` });
  if (f.price_from_nzd || f.price_to_nzd)
    tags.push({ k: "NZ$", v: `${f.price_from_nzd || "…"}–${f.price_to_nzd || "…"}` });
  if (f.price_from_rub || f.price_to_rub)
    tags.push({ k: "₽", v: `${f.price_from_rub || "…"}–${f.price_to_rub || "…"}` });
  if (f.mileage_to_km) tags.push({ k: "Пробег ≤", v: `${f.mileage_to_km} км` });
  if (f.fuel) tags.push({ k: "Топливо", v: f.fuel });
  if (f.damage_only) tags.push({ k: "Повреждённые", v: "да" });
  if (f.keywords) tags.push({ k: "Ключевые слова", v: f.keywords });
  if (tags.length === 0) return <span className="auto-muted">Без фильтров — будут все новые лоты.</span>;
  return tags.map((t, i) => (
    <span key={i} className="auto-badge">
      <span className="auto-muted" style={{ marginRight: 4 }}>{t.k}:</span>
      {t.v}
    </span>
  ));
}
