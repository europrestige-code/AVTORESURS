import React, { useCallback, useEffect, useMemo, useState } from "react";
import autoApi from "../../services/autoApi";
import { useAuth } from "../../contexts/AuthContext";
import { MapPin } from "lucide-react";

const DAY_RU = ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"];

function CityTag({ name, testid }) {
  if (!name || name === "—") {
    return <span className="auto-muted">—</span>;
  }
  return (
    <span
      data-testid={testid}
      className="inline-flex items-center gap-1 whitespace-nowrap"
      title="Место проведения аукциона (Новая Зеландия)"
    >
      <MapPin size={13} style={{ color: "var(--ar-blue, var(--ar-blue))", flexShrink: 0 }} />
      <span>{name}</span>
    </span>
  );
}

function parseISO(s) {
  if (!s) return null;
  const t = new Date(s);
  return Number.isNaN(t.getTime()) ? null : t;
}

export default function AutoAuctionsCalendar() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [data, setData] = useState(null);
  const [city, setCity] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const params = { days_ahead: 21 };
      if (city) params.city = city;
      const r = await autoApi.get("/auctions/calendar", { params });
      setData(r.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Не удалось загрузить календарь.");
    }
  }, [city]);

  useEffect(() => { load(); }, [load]);

  const refresh = async () => {
    setRefreshing(true);
    try {
      await autoApi.post("/admin/auctions/refresh", { categories: ["cars"] });
      await load();
    } catch (e) {
      alert(e.response?.data?.detail || "Не удалось обновить.");
    } finally {
      setRefreshing(false);
    }
  };

  const cities = useMemo(() => {
    if (!data?.events) return [];
    const set = new Set();
    data.events.forEach((e) => e.city && set.add(e.city));
    return ["", ...Array.from(set).sort()];
  }, [data]);

  const grid = useMemo(() => {
    if (!data?.by_day) return [];
    // Build a 21-day strip starting from today
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const days = [];
    const byDate = new Map(data.by_day.map((d) => [d.date, d]));
    for (let i = 0; i < 21; i++) {
      const d = new Date(today.getTime() + i * 86400000);
      const key = d.toISOString().slice(0, 10);
      const stats = byDate.get(key);
      days.push({ date: key, jsDate: d, stats });
    }
    return days;
  }, [data]);

  const totalLots = useMemo(
    () => (data?.events || []).reduce((sum, e) => sum + (e.lots || 0), 0),
    [data]
  );

  return (
    <div className="auto-section">
      <header style={{ display: "flex", gap: 16, alignItems: "flex-end", flexWrap: "wrap", marginBottom: 18 }}>
        <div style={{ flex: 1, minWidth: 280 }}>
          <div className="auto-badge auto-badge-primary" style={{ marginBottom: 10 }}>Аукционы · Turners NZ</div>
          <h1 style={{ fontSize: 28, margin: 0 }}>Календарь аукционов на 3 недели</h1>
          <p className="auto-muted" style={{ marginTop: 6 }} data-testid="auctions-summary">
            {data ? `${data.count} аукционов · ${totalLots.toLocaleString("ru-RU")} лотов` : "Загружаем…"}
          </p>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <select
            className="auto-select"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            data-testid="auctions-city-filter"
            style={{ minWidth: 180 }}
          >
            {cities.map((c) => (
              <option key={c || "all"} value={c}>{c || "Все города"}</option>
            ))}
          </select>
          {isAdmin && (
            <button
              type="button"
              onClick={refresh}
              disabled={refreshing}
              className="auto-btn"
              data-testid="auctions-refresh-btn"
            >
              {refreshing ? "Обновляем…" : "Обновить из Turners"}
            </button>
          )}
        </div>
      </header>

      {error && <div className="auto-card auto-muted">{error}</div>}

      {/* Calendar strip */}
      <section className="auctions-calendar" data-testid="auctions-calendar-grid">
        {grid.map((d) => {
          const heat = Math.min(1, (d.stats?.lots || 0) / 400);
          const bg = d.stats
            ? `rgba(0,102,255,${0.12 + heat * 0.6})`
            : "transparent";
          return (
            <div
              key={d.date}
              className={`auctions-day ${d.stats ? "auctions-day--active" : ""}`}
              style={{ background: bg }}
              data-testid={`auctions-day-${d.date}`}
            >
              <div className="auctions-day__head">
                <span className="auto-muted" style={{ fontSize: 12 }}>{DAY_RU[d.jsDate.getDay()]}</span>
                <span style={{ fontSize: 20, fontWeight: 800, lineHeight: 1 }}>
                  {d.jsDate.getDate()}
                </span>
                <span className="auto-muted" style={{ fontSize: 11 }}>
                  {d.jsDate.toLocaleDateString("ru-RU", { month: "short" })}
                </span>
              </div>
              {d.stats ? (
                <div className="auctions-day__stats">
                  <div className="auctions-day__big">{d.stats.lots}</div>
                  <div className="auto-muted" style={{ fontSize: 11 }}>лотов · {d.stats.events} ауц.</div>
                  <div className="flex flex-wrap items-center gap-x-1 gap-y-0.5" style={{ fontSize: 11, marginTop: 4 }}>
                    {d.stats.cities.slice(0, 2).map((c, i) => (
                      <CityTag key={c} name={c} testid={`day-city-${d.date}-${i}`} />
                    ))}
                    {d.stats.cities.length > 2 && (
                      <span className="auto-muted">+{d.stats.cities.length - 2}</span>
                    )}
                  </div>
                </div>
              ) : (
                <div className="auto-muted" style={{ fontSize: 11 }}>—</div>
              )}
            </div>
          );
        })}
      </section>

      {/* Detailed list */}
      <section style={{ marginTop: 24 }}>
        <h2 style={{ fontSize: 20, marginBottom: 12 }}>События</h2>
        {!data?.events?.length ? (
          <div className="auto-card auto-muted" data-testid="auctions-empty">
            На ближайшие 3 недели аукционов не найдено. Попробуйте обновить список.
          </div>
        ) : (
          <table className="auto-table" data-testid="auctions-table">
            <thead>
              <tr>
                <th>Дата</th>
                <th>Время</th>
                <th>Аукцион</th>
                <th>Город</th>
                <th>Лотов</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.events.map((e) => {
                const dt = parseISO(e.starts_at);
                return (
                  <tr key={e.key} data-testid={`auction-row-${e.key}`}>
                    <td>{dt ? dt.toLocaleDateString("ru-RU") : "—"}</td>
                    <td>{dt ? dt.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" }) : "—"}</td>
                    <td style={{ maxWidth: 380 }}>
                      <div style={{ fontWeight: 600 }}>{e.title}</div>
                      <div className="auto-muted" style={{ fontSize: 12 }}>
                        <CityTag name={e.branch} testid={`event-branch-${e.key}`} />
                      </div>
                    </td>
                    <td><CityTag name={e.city || "—"} testid={`event-city-${e.key}`} /></td>
                    <td style={{ fontWeight: 700 }}>{e.lots}</td>
                    <td>
                      {e.auction_url && (
                        <a
                          href={e.auction_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="auto-btn auto-btn-outline"
                          data-testid={`auction-link-${e.key}`}
                        >
                          Открыть
                        </a>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
