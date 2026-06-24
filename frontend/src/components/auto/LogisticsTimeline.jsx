import React from "react";

const LABELS = {
  won: "Выигран на аукционе",
  invoice_issued: "Счёт выставлен",
  paid: "Оплачен",
  collected: "Забран со склада",
  stored: "На складе",
  container_assigned: "Контейнер назначен",
  loaded: "Загружен",
  shipped: "Отправлен",
  arrived: "Прибыл в порт",
  delivered: "Доставлен",
};

export default function LogisticsTimeline({ events }) {
  if (!events || events.length === 0) {
    return (
      <div className="auto-card auto-muted" data-testid="logistics-empty">
        Пока нет событий по логистике.
      </div>
    );
  }
  return (
    <div className="auto-card" data-testid="logistics-timeline">
      <div style={{ fontWeight: 600, marginBottom: 12 }}>Логистика</div>
      <ol style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 10 }}>
        {events.map((e) => (
          <li key={e.id} style={{ display: "flex", gap: 12, alignItems: "start" }}>
            <span
              style={{
                width: 10, height: 10, borderRadius: "50%",
                background: "var(--auto-primary)", marginTop: 6,
              }}
            />
            <div>
              <div style={{ fontWeight: 600 }}>{LABELS[e.status] || e.status}</div>
              <div className="auto-muted" style={{ fontSize: 13 }}>
                {new Date(e.created_at).toLocaleString("ru-RU")}
                {e.note_ru ? ` · ${e.note_ru}` : ""}
              </div>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

export { LABELS as LOGISTICS_LABELS };
