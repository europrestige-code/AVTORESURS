import React, { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import autoApi from "../../services/autoApi";
import { useAuth } from "../../contexts/AuthContext";
import DepositStatus from "../../components/auto/DepositStatus";
import LogisticsTimeline, { LOGISTICS_LABELS } from "../../components/auto/LogisticsTimeline";
import { getFxRate, formatRub } from "../../services/autoCurrency";

const BID_STATUS = {
  active: { cls: "auto-badge-success", text: "Лидируете" },
  outbid: { cls: "auto-badge-warning", text: "Перебита" },
  cancelled: { cls: "", text: "Отменена" },
  won: { cls: "auto-badge-primary", text: "Выиграна" },
  lost: { cls: "auto-badge-danger", text: "Проиграна" },
};

export default function AutoDashboard() {
  const { isAuthenticated, loading } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [searchParams, setSearchParams] = useSearchParams();

  const load = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const r = await autoApi.get("/my/dashboard");
      setData(r.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Не удалось загрузить кабинет.");
    }
  }, [isAuthenticated]);

  useEffect(() => {
    load();
    getFxRate();
  }, [load]);

  // Poll Stripe status when returning from checkout
  useEffect(() => {
    const sid = searchParams.get("stripe_session");
    if (!sid) return;
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts += 1;
      try {
        const r = await autoApi.get(`/deposit/stripe/status/${sid}`);
        if (r.data.payment_status === "paid" || attempts >= 6) {
          clearInterval(interval);
          searchParams.delete("stripe_session");
          setSearchParams(searchParams, { replace: true });
          load();
        }
      } catch {
        if (attempts >= 6) clearInterval(interval);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [searchParams, setSearchParams, load]);

  if (loading) return <div className="auto-section auto-card auto-muted">Загружаем…</div>;
  if (!isAuthenticated) {
    return (
      <div className="auto-section auto-card" data-testid="dashboard-login-required">
        <div style={{ fontWeight: 600, marginBottom: 8 }}>Требуется авторизация</div>
        <div className="auto-muted" style={{ marginBottom: 12 }}>
          Войдите в систему, чтобы открыть личный кабинет BuyAnywhere Auto.
        </div>
        <Link to="/" className="auto-btn">На главную BuyAnywhere</Link>
      </div>
    );
  }
  if (error) return <div className="auto-section auto-card auto-muted">{error}</div>;
  if (!data) return <div className="auto-section auto-card auto-muted">Загружаем…</div>;

  return (
    <div className="auto-section" style={{ display: "grid", gap: 18 }}>
      <h1 style={{ fontSize: 28, margin: 0 }}>Мой кабинет BuyAnywhere Auto</h1>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }} className="dash-grid">
        <DepositStatus deposit={data.deposit} onChange={load} />
        <div className="auto-card" data-testid="dash-summary">
          <div style={{ fontWeight: 600, marginBottom: 10 }}>Сводка</div>
          <Row label="Активные ставки" value={data.bids?.filter((b) => b.status === "active").length || 0} />
          <Row label="Перебитые" value={data.bids?.filter((b) => b.status === "outbid").length || 0} />
          <Row label="В избранном" value={data.watchlist?.length || 0} />
          <Row label="Счета" value={data.invoices?.length || 0} />
          <Row label="События логистики" value={data.logistics?.length || 0} />
        </div>
      </div>

      <Section title="Мои ставки" testid="dash-bids">
        {data.bids?.length ? (
          <table className="auto-table">
            <thead>
              <tr><th>Автомобиль</th><th>Ставка</th><th>Статус</th><th>Дата</th></tr>
            </thead>
            <tbody>
              {data.bids.map((b) => {
                const s = BID_STATUS[b.status] || { cls: "", text: b.status };
                return (
                  <tr key={b.id} data-testid={`bid-row-${b.id}`}>
                    <td>
                      {b.vehicle ? (
                        <Link to={`/auto/vehicle/${b.vehicle.id}`} style={{ color: "var(--auto-primary)" }}>
                          {b.vehicle.title_ru}
                        </Link>
                      ) : b.vehicle_id}
                    </td>
                    <td>{formatRub(b.max_bid_nzd)}</td>
                    <td><span className={`auto-badge ${s.cls}`}>{s.text}</span></td>
                    <td>{new Date(b.created_at).toLocaleString("ru-RU")}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : <Empty>Ставок пока нет.</Empty>}
      </Section>

      <Section title="Избранное" testid="dash-watchlist">
        {data.watchlist?.length ? (
          <div className="auto-grid">
            {data.watchlist.map((v) => (
              <div key={v.id} className="auto-card">
                <div style={{ fontWeight: 600 }}>{v.title_ru}</div>
                <div className="auto-muted" style={{ fontSize: 13, marginBottom: 8 }}>
                  {v.year} · {formatRub(v.current_price_nzd)}
                </div>
                <Link to={`/auto/vehicle/${v.id}`} className="auto-btn">Открыть</Link>
              </div>
            ))}
          </div>
        ) : <Empty>Список пуст.</Empty>}
      </Section>

      <Section title="Счета" testid="dash-invoices">
        {data.invoices?.length ? (
          <table className="auto-table">
            <thead><tr><th>ID</th><th>Авто</th><th>Сумма</th><th>Статус</th><th>Дата</th></tr></thead>
            <tbody>
              {data.invoices.map((i) => (
                <tr key={i.id} data-testid={`invoice-row-${i.id}`}>
                  <td>{i.id.slice(0, 8)}</td>
                  <td>{i.vehicle_id.slice(0, 8)}</td>
                  <td>{formatRub(i.total_nzd)}</td>
                  <td><span className="auto-badge">{i.status}</span></td>
                  <td>{new Date(i.created_at).toLocaleString("ru-RU")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <Empty>Счетов пока нет.</Empty>}
      </Section>

      <Section title="Логистика" testid="dash-logistics">
        <LogisticsTimeline events={data.logistics} />
      </Section>

      <Section title="Запросы (Австралия и inquiry-only)" testid="dash-inquiries">
        {data.inquiries?.length ? (
          <table className="auto-table">
            <thead><tr><th>Статус</th><th>Сообщение</th><th>Дата</th></tr></thead>
            <tbody>
              {data.inquiries.map((q) => (
                <tr key={q.id} data-testid={`inquiry-row-${q.id}`}>
                  <td><span className="auto-badge">{q.status}</span></td>
                  <td className="auto-muted">{q.message}</td>
                  <td>{new Date(q.created_at).toLocaleString("ru-RU")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <Empty>Запросов нет.</Empty>}
      </Section>

      <style>{`
        @media (max-width: 800px) { .dash-grid { grid-template-columns: 1fr !important; } }
      `}</style>
    </div>
  );
}

function Section({ title, children, testid }) {
  return (
    <div data-testid={testid}>
      <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 10 }}>{title}</div>
      {children}
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid var(--auto-border)" }}>
      <span className="auto-muted">{label}</span><span style={{ fontWeight: 600 }}>{value}</span>
    </div>
  );
}

function Empty({ children }) {
  return <div className="auto-card auto-muted">{children}</div>;
}
