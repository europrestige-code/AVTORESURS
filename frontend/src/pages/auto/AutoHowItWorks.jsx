import React from "react";

const STEPS = [
  ["Выбор автомобиля", "Просматриваете каталог: аукционные авто, фикс. цена, авто на запчасти. Австралия — по запросу."],
  ["Депозит NZ$1,000", "Депозит подтверждает серьёзность намерений и открывает доступ к торгам. Возвращается, если не выкупили."],
  ["Внутренняя ставка", "Вы указываете максимальную цену. Менеджер делает реальные ставки на аукционе от вашего имени, не превышая вашу."],
  ["Выигрыш и счёт", "После выигрыша получаете счёт: цена + комиссия + транспорт + хранение + документы + контейнер."],
  ["Логистика", "Авто едет со склада в порт, в контейнер, в Россию. Статус отображается в кабинете."],
  ["Получение", "Получаете автомобиль или запчасти в РФ. Полное сопровождение."],
];

export default function AutoHowItWorks() {
  return (
    <div className="auto-section">
      <h1 style={{ fontSize: 32, margin: 0 }}>Как это работает</h1>
      <p className="auto-muted" style={{ marginTop: 8, marginBottom: 22 }}>
        Полный цикл покупки авто из Новой Зеландии — от выбора до доставки.
      </p>
      <div style={{ display: "grid", gap: 14 }}>
        {STEPS.map(([t, d], i) => (
          <div key={i} className="auto-card" style={{ display: "flex", gap: 14, alignItems: "start" }}>
            <div style={{
              minWidth: 36, height: 36, borderRadius: "50%",
              background: "rgba(0,102,255,0.15)", color: "var(--auto-primary)",
              display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700,
            }}>{i + 1}</div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 18 }}>{t}</div>
              <div className="auto-muted" style={{ marginTop: 4 }}>{d}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
