import React, { useCallback, useEffect, useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import autoApi from "../../services/autoApi";
import { fmtPrice } from "../../components/auto/VehicleCard";

const TABS = ["vehicles", "bids", "deposits", "sources", "import", "branding", "auctions", "invoices", "logistics", "crm", "clients"];
const TAB_LABEL = {
  vehicles: "Автомобили",
  bids: "Ставки",
  deposits: "Депозиты",
  sources: "Источники",
  import: "Импорт",
  branding: "Брендирование",
  auctions: "Календарь",
  invoices: "Счета",
  logistics: "Логистика",
  crm: "CRM сделки",
  clients: "Клиенты",
};

export default function AutoAdmin() {
  const { user, isAuthenticated, loading } = useAuth();
  const [tab, setTab] = useState("vehicles");

  if (loading) return <div className="auto-section auto-card auto-muted">Загружаем…</div>;
  if (!isAuthenticated || user?.role !== "admin") {
    return (
      <div className="auto-section auto-card" data-testid="admin-access-denied">
        <div style={{ fontWeight: 600 }}>Доступ запрещён</div>
        <div className="auto-muted">Требуются права администратора.</div>
      </div>
    );
  }

  return (
    <div className="auto-section">
      <h1 style={{ fontSize: 28, marginTop: 0 }}>Админ-панель</h1>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`auto-btn ${tab === t ? "" : "auto-btn-outline"}`}
            data-testid={`admin-tab-${t}`}
          >
            {TAB_LABEL[t]}
          </button>
        ))}
      </div>
      {tab === "vehicles" && <VehiclesTab />}
      {tab === "bids" && <BidsTab />}
      {tab === "deposits" && <DepositsTab />}
      {tab === "sources" && <SourcesTab />}
      {tab === "import" && <ImportTab />}
      {tab === "branding" && <BrandingTab />}
      {tab === "auctions" && <AuctionsTab />}
      {tab === "invoices" && <InvoicesTab />}
      {tab === "logistics" && <LogisticsTab />}
      {tab === "crm" && <CrmTab />}
      {tab === "clients" && <ClientsTab />}
    </div>
  );
}

function VehiclesTab() {
  const [items, setItems] = useState([]);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState(initialVehicleForm());
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const r = await autoApi.get("/vehicles", { params: { limit: 100 } });
    setItems(r.data.items || []);
  }, []);
  useEffect(() => { load(); }, [load]);

  const save = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await autoApi.post("/admin/vehicles", parseVehicleForm(form));
      setCreating(false);
      setForm(initialVehicleForm());
      await load();
    } catch (err) {
      alert(err.response?.data?.detail || "Ошибка создания.");
    } finally { setBusy(false); }
  };

  const aiTranslate = async (id) => {
    try {
      await autoApi.post(`/admin/vehicles/${id}/ai-translate`);
      await load();
    } catch (e) { alert(e.response?.data?.detail || "Ошибка."); }
  };
  const aiSummary = async (id) => {
    try {
      await autoApi.post(`/admin/vehicles/${id}/ai-summary`);
      await load();
    } catch (e) { alert(e.response?.data?.detail || "Ошибка."); }
  };
  const remove = async (id) => {
    if (!confirm("Скрыть автомобиль?")) return;
    await autoApi.delete(`/admin/vehicles/${id}`);
    await load();
  };
  const markWon = async (id) => {
    if (!confirm("Отметить автомобиль как 'Выигран'? Будет создана CRM-сделка.")) return;
    try {
      const r = await autoApi.post(`/admin/vehicles/${id}/mark-won`);
      alert(r.data.crm_order
        ? `Создана CRM-сделка ${r.data.crm_order.order_id}`
        : "Статус обновлён. CRM-сделка не создана (нет ставок).");
      await load();
    } catch (e) {
      alert(e.response?.data?.detail || "Ошибка.");
    }
  };

  return (
    <div>
      <button className="auto-btn" onClick={() => setCreating(!creating)} data-testid="admin-create-vehicle-btn">
        {creating ? "Отменить" : "Добавить автомобиль"}
      </button>
      {creating && (
        <form onSubmit={save} className="auto-card" style={{ marginTop: 12, display: "grid", gap: 8 }} data-testid="admin-vehicle-form">
          <VehicleFormFields form={form} setForm={setForm} />
          <button type="submit" className="auto-btn" disabled={busy} data-testid="admin-vehicle-submit">
            {busy ? "Сохраняем…" : "Создать"}
          </button>
        </form>
      )}
      <div style={{ marginTop: 18 }}>
        <table className="auto-table">
          <thead>
            <tr><th>Авто</th><th>Страна / Тип</th><th>Цена</th><th>Статус</th><th>AI</th><th></th></tr>
          </thead>
          <tbody>
            {items.map((v) => (
              <tr key={v.id} data-testid={`admin-vehicle-row-${v.id}`}>
                <td>
                  <div style={{ fontWeight: 600 }}>{v.title_ru}</div>
                  <div className="auto-muted" style={{ fontSize: 12 }}>{v.id.slice(0, 8)}</div>
                </td>
                <td>{v.country} · {v.listing_type}</td>
                <td>{fmtPrice(v.current_price_nzd)}</td>
                <td><span className="auto-badge">{v.status}</span></td>
                <td style={{ display: "flex", gap: 6 }}>
                  <button className="auto-btn auto-btn-outline" onClick={() => aiTranslate(v.id)} data-testid={`admin-translate-${v.id}`}>Перевод</button>
                  <button className="auto-btn auto-btn-outline" onClick={() => aiSummary(v.id)} data-testid={`admin-summary-${v.id}`}>Резюме</button>
                </td>
                <td style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  <button className="auto-btn auto-btn-success" onClick={() => markWon(v.id)} data-testid={`admin-mark-won-${v.id}`}>Выигран</button>
                  <button className="auto-btn auto-btn-danger" onClick={() => remove(v.id)} data-testid={`admin-hide-${v.id}`}>Скрыть</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function VehicleFormFields({ form, setForm }) {
  const upd = (k, v) => setForm({ ...form, [k]: v });
  return (
    <>
      <input className="auto-input" placeholder="Название (рус)" value={form.title_ru} onChange={(e) => upd("title_ru", e.target.value)} required data-testid="form-title-ru" />
      <input className="auto-input" placeholder="Title (orig)" value={form.title_original} onChange={(e) => upd("title_original", e.target.value)} />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        <select className="auto-select" value={form.country} onChange={(e) => upd("country", e.target.value)} data-testid="form-country">
          <option value="NZ">NZ</option><option value="AU">AU</option>
        </select>
        <select className="auto-select" value={form.listing_type} onChange={(e) => upd("listing_type", e.target.value)} data-testid="form-listing-type">
          <option value="auction">auction</option>
          <option value="fixed_price">fixed_price</option>
          <option value="inquiry_only">inquiry_only</option>
        </select>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        <input className="auto-input" placeholder="Make" value={form.make} onChange={(e) => upd("make", e.target.value)} />
        <input className="auto-input" placeholder="Model" value={form.model} onChange={(e) => upd("model", e.target.value)} />
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
        <input className="auto-input" placeholder="Year" type="number" value={form.year} onChange={(e) => upd("year", e.target.value)} />
        <input className="auto-input" placeholder="Mileage km" type="number" value={form.mileage_km} onChange={(e) => upd("mileage_km", e.target.value)} />
        <input className="auto-input" placeholder="Price NZ$" type="number" value={form.current_price_nzd} onChange={(e) => upd("current_price_nzd", e.target.value)} data-testid="form-price" />
      </div>
      <input className="auto-input" placeholder="Source (eg ManheimNZ)" value={form.source} onChange={(e) => upd("source", e.target.value)} />
      <input className="auto-input" placeholder="Images (URL через запятую)" value={form.images} onChange={(e) => upd("images", e.target.value)} />
      <textarea className="auto-textarea" rows={3} placeholder="Описание (рус)" value={form.description_ru} onChange={(e) => upd("description_ru", e.target.value)} />
    </>
  );
}
function initialVehicleForm() {
  return {
    title_ru: "", title_original: "", country: "NZ", listing_type: "auction",
    make: "", model: "", year: "", mileage_km: "", current_price_nzd: "",
    source: "manual", images: "", description_ru: "",
  };
}
function parseVehicleForm(f) {
  return {
    title_ru: f.title_ru,
    title_original: f.title_original || null,
    country: f.country,
    listing_type: f.listing_type,
    make: f.make || null,
    model: f.model || null,
    year: f.year ? Number(f.year) : null,
    mileage_km: f.mileage_km ? Number(f.mileage_km) : null,
    current_price_nzd: f.current_price_nzd ? Number(f.current_price_nzd) : null,
    source: f.source || "manual",
    images: f.images ? f.images.split(",").map((s) => s.trim()).filter(Boolean) : [],
    description_ru: f.description_ru || null,
  };
}

function BidsTab() {
  const [bids, setBids] = useState([]);
  useEffect(() => { autoApi.get("/admin/bids").then((r) => setBids(r.data)); }, []);
  return (
    <table className="auto-table" data-testid="admin-bids-table">
      <thead><tr><th>Авто</th><th>Клиент</th><th>Ставка</th><th>Статус</th><th>Дата</th></tr></thead>
      <tbody>
        {bids.map((b) => (
          <tr key={b.id} data-testid={`admin-bid-row-${b.id}`}>
            <td>{b.vehicle_title_ru || b.vehicle_id.slice(0, 8)}</td>
            <td>{b.user_email || b.user_id.slice(0, 8)}</td>
            <td>{fmtPrice(b.max_bid_nzd)}</td>
            <td><span className="auto-badge">{b.status}</span></td>
            <td>{new Date(b.created_at).toLocaleString("ru-RU")}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function DepositsTab() {
  const [deposits, setDeposits] = useState([]);
  const load = useCallback(() => autoApi.get("/admin/deposits").then((r) => setDeposits(r.data)), []);
  useEffect(() => { load(); }, [load]);
  const verify = async (id) => {
    const note = prompt("Комментарий (опционально):") || "";
    await autoApi.put(`/admin/deposits/${id}/verify`, { note });
    await load();
  };
  const reject = async (id) => {
    const note = prompt("Причина отклонения:") || "Отклонено администратором.";
    await autoApi.put(`/admin/deposits/${id}/reject`, { note });
    await load();
  };
  return (
    <table className="auto-table" data-testid="admin-deposits-table">
      <thead><tr><th>Клиент</th><th>Сумма</th><th>Метод</th><th>Статус</th><th>Файл</th><th></th></tr></thead>
      <tbody>
        {deposits.map((d) => (
          <tr key={d.id} data-testid={`admin-deposit-row-${d.id}`}>
            <td>{d.user_email || d.user_id.slice(0, 8)}</td>
            <td>NZ${d.amount}</td>
            <td>{d.method}</td>
            <td><span className="auto-badge">{d.status}</span></td>
            <td className="auto-muted">
              {d.payment_proof_file ? (
                <a
                  href={`${process.env.REACT_APP_BACKEND_URL}/api/auto/deposit/${d.id}/proof`}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => {
                    e.preventDefault();
                    const token = localStorage.getItem("access_token");
                    fetch(e.currentTarget.href, { headers: { Authorization: `Bearer ${token}` } })
                      .then((r) => r.blob())
                      .then((b) => window.open(URL.createObjectURL(b), "_blank"));
                  }}
                  style={{ color: "var(--auto-primary)" }}
                  data-testid={`deposit-proof-link-${d.id}`}
                >
                  Открыть файл
                </a>
              ) : d.payment_proof_note || "—"}
            </td>
            <td style={{ display: "flex", gap: 6 }}>
              <button className="auto-btn auto-btn-success" onClick={() => verify(d.id)} data-testid={`admin-verify-${d.id}`}>Одобрить</button>
              <button className="auto-btn auto-btn-danger" onClick={() => reject(d.id)} data-testid={`admin-reject-${d.id}`}>Отклонить</button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function ImportTab() {
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  const importText = async (save) => {
    setBusy(true); setResult(null);
    try {
      const r = await autoApi.post(`/admin/import/from-text?save=${save ? "true" : "false"}`, { text });
      setResult(r.data);
    } catch (e) {
      setResult({ ok: false, error: e.response?.data?.detail || "Ошибка." });
    } finally { setBusy(false); }
  };
  const importUrl = async (save) => {
    setBusy(true); setResult(null);
    try {
      const r = await autoApi.post(`/admin/import/from-url?save=${save ? "true" : "false"}`, { url });
      setResult(r.data);
    } catch (e) {
      setResult({ ok: false, error: e.response?.data?.detail || "Ошибка." });
    } finally { setBusy(false); }
  };

  return (
    <div style={{ display: "grid", gap: 14 }} data-testid="admin-import">
      <div className="auto-card">
        <div style={{ fontWeight: 600, marginBottom: 8 }}>Импорт из текста</div>
        <textarea className="auto-textarea" rows={6} value={text} onChange={(e) => setText(e.target.value)} placeholder="Вставьте текст объявления…" data-testid="import-text" />
        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <button className="auto-btn auto-btn-outline" onClick={() => importText(false)} disabled={busy || !text} data-testid="import-text-preview">Предпросмотр</button>
          <button className="auto-btn" onClick={() => importText(true)} disabled={busy || !text} data-testid="import-text-save">Сохранить</button>
        </div>
      </div>
      <div className="auto-card">
        <div style={{ fontWeight: 600, marginBottom: 8 }}>Импорт по URL</div>
        <input className="auto-input" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://…" data-testid="import-url" />
        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <button className="auto-btn auto-btn-outline" onClick={() => importUrl(false)} disabled={busy || !url} data-testid="import-url-preview">Предпросмотр</button>
          <button className="auto-btn" onClick={() => importUrl(true)} disabled={busy || !url} data-testid="import-url-save">Сохранить</button>
        </div>
      </div>
      {result && (
        <pre className="auto-card" style={{ overflowX: "auto", fontSize: 12 }} data-testid="import-result">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}

function InvoicesTab() {
  const [items, setItems] = useState([]);
  const load = useCallback(() => autoApi.get("/admin/invoices").then((r) => setItems(r.data)), []);
  useEffect(() => { load(); }, [load]);

  const [form, setForm] = useState({ user_id: "", vehicle_id: "", vehicle_price_nzd: "", storage_days: 0 });
  const create = async () => {
    try {
      await autoApi.post("/admin/invoices", {
        user_id: form.user_id, vehicle_id: form.vehicle_id,
        vehicle_price_nzd: Number(form.vehicle_price_nzd || 0),
        storage_days: Number(form.storage_days || 0),
      });
      setForm({ user_id: "", vehicle_id: "", vehicle_price_nzd: "", storage_days: 0 });
      await load();
    } catch (e) { alert(e.response?.data?.detail || "Ошибка."); }
  };

  return (
    <div style={{ display: "grid", gap: 14 }} data-testid="admin-invoices">
      <div className="auto-card" style={{ display: "grid", gap: 8 }}>
        <div style={{ fontWeight: 600 }}>Создать счёт</div>
        <input className="auto-input" placeholder="user_id" value={form.user_id} onChange={(e) => setForm({ ...form, user_id: e.target.value })} data-testid="invoice-user-id" />
        <input className="auto-input" placeholder="vehicle_id" value={form.vehicle_id} onChange={(e) => setForm({ ...form, vehicle_id: e.target.value })} data-testid="invoice-vehicle-id" />
        <input className="auto-input" placeholder="Цена авто NZ$" type="number" value={form.vehicle_price_nzd} onChange={(e) => setForm({ ...form, vehicle_price_nzd: e.target.value })} data-testid="invoice-price" />
        <input className="auto-input" placeholder="Дней хранения" type="number" value={form.storage_days} onChange={(e) => setForm({ ...form, storage_days: e.target.value })} />
        <button className="auto-btn" onClick={create} data-testid="invoice-create-btn">Создать</button>
      </div>
      <table className="auto-table">
        <thead><tr><th>ID</th><th>User</th><th>Авто</th><th>Сумма</th><th>Статус</th><th>Дата</th></tr></thead>
        <tbody>
          {items.map((i) => (
            <tr key={i.id}>
              <td>{i.id.slice(0, 8)}</td>
              <td>{i.user_id.slice(0, 8)}</td>
              <td>{i.vehicle_id.slice(0, 8)}</td>
              <td>{fmtPrice(i.total_nzd)}</td>
              <td><span className="auto-badge">{i.status}</span></td>
              <td>{new Date(i.created_at).toLocaleString("ru-RU")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function LogisticsTab() {
  const [events, setEvents] = useState([]);
  const load = useCallback(() => autoApi.get("/admin/logistics").then((r) => setEvents(r.data)), []);
  useEffect(() => { load(); }, [load]);
  const [form, setForm] = useState({ vehicle_id: "", user_id: "", status: "won", note_ru: "" });
  const add = async () => {
    try {
      await autoApi.put(`/admin/logistics/${form.vehicle_id}`, {
        user_id: form.user_id, status: form.status, note_ru: form.note_ru,
      });
      setForm({ vehicle_id: "", user_id: "", status: "won", note_ru: "" });
      await load();
    } catch (e) { alert(e.response?.data?.detail || "Ошибка."); }
  };
  return (
    <div style={{ display: "grid", gap: 14 }} data-testid="admin-logistics">
      <div className="auto-card" style={{ display: "grid", gap: 8 }}>
        <div style={{ fontWeight: 600 }}>Добавить событие</div>
        <input className="auto-input" placeholder="vehicle_id" value={form.vehicle_id} onChange={(e) => setForm({ ...form, vehicle_id: e.target.value })} />
        <input className="auto-input" placeholder="user_id" value={form.user_id} onChange={(e) => setForm({ ...form, user_id: e.target.value })} />
        <select className="auto-select" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
          {["won","invoice_issued","paid","collected","stored","container_assigned","loaded","shipped","arrived","delivered"].map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <input className="auto-input" placeholder="Комментарий" value={form.note_ru} onChange={(e) => setForm({ ...form, note_ru: e.target.value })} />
        <button className="auto-btn" onClick={add} data-testid="logistics-add-btn">Добавить</button>
      </div>
      <table className="auto-table">
        <thead><tr><th>Авто</th><th>Клиент</th><th>Статус</th><th>Заметка</th><th>Дата</th></tr></thead>
        <tbody>
          {events.map((e) => (
            <tr key={e.id}>
              <td>{e.vehicle_id.slice(0, 8)}</td>
              <td>{e.user_id.slice(0, 8)}</td>
              <td><span className="auto-badge">{e.status}</span></td>
              <td className="auto-muted">{e.note_ru || "—"}</td>
              <td>{new Date(e.created_at).toLocaleString("ru-RU")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CrmTab() {
  const [items, setItems] = useState([]);
  useEffect(() => { autoApi.get("/admin/crm-orders").then((r) => setItems(r.data)); }, []);
  return (
    <table className="auto-table" data-testid="admin-crm-table">
      <thead>
        <tr><th>Order ID</th><th>Клиент</th><th>Авто</th><th>Сумма</th><th>Статус</th><th>Дата</th></tr>
      </thead>
      <tbody>
        {items.length === 0 && (
          <tr><td colSpan={6} className="auto-muted">CRM-сделок пока нет. Они создаются автоматически при отметке авто как «Выигран».</td></tr>
        )}
        {items.map((o) => (
          <tr key={o.id} data-testid={`admin-crm-row-${o.id}`}>
            <td style={{ fontWeight: 600 }}>{o.order_id}</td>
            <td>{o.customer_name}<div className="auto-muted" style={{ fontSize: 12 }}>{o.customer_email}</div></td>
            <td>{o.product_name}</td>
            <td>{fmtPrice(o.customer_paid_amount)}</td>
            <td><span className="auto-badge">{o.status}</span></td>
            <td>{o.created_at ? new Date(o.created_at).toLocaleString("ru-RU") : "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function ClientsTab() {
  const [items, setItems] = useState([]);
  useEffect(() => { autoApi.get("/admin/clients").then((r) => setItems(r.data)); }, []);
  return (
    <table className="auto-table" data-testid="admin-clients-table">
      <thead><tr><th>Email</th><th>Телефон</th><th>Депозит</th><th>Зарегистрирован</th></tr></thead>
      <tbody>
        {items.map((u) => (
          <tr key={u.id}>
            <td>{u.email}</td>
            <td>{u.phone}</td>
            <td>{u.latest_deposit_status ? <span className="auto-badge">{u.latest_deposit_status}</span> : <span className="auto-muted">—</span>}</td>
            <td>{u.created_at ? new Date(u.created_at).toLocaleString("ru-RU") : "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function SourcesTab() {
  const [source, setSource] = useState("turners");
  const [limit, setLimit] = useState(20);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [selected, setSelected] = useState({});
  const [runs, setRuns] = useState([]);

  const loadRuns = useCallback(async () => {
    try {
      const r = await autoApi.get("/admin/sources/runs", { params: { limit: 10 } });
      setRuns(r.data);
    } catch {}
  }, []);
  useEffect(() => { loadRuns(); }, [loadRuns]);

  const scan = async () => {
    setBusy(true); setResult(null); setSelected({});
    try {
      const r = await autoApi.post("/admin/sources/scan", { source, limit: Number(limit || 20) });
      setResult(r.data);
      // pre-select only new (non-duplicate) items
      const next = {};
      (r.data.items || []).forEach((it) => {
        const ref = it?.vehicle?.source_reference;
        if (ref && it.is_new) next[ref] = true;
      });
      setSelected(next);
    } catch (e) {
      setResult({ ok: false, error: e.response?.data?.detail || String(e) });
    } finally { setBusy(false); }
  };

  const importSelected = async () => {
    if (!result) return;
    const ids = Object.keys(selected).filter((k) => selected[k]);
    if (!ids.length) { alert("Не выбрано ни одной строки."); return; }
    setBusy(true);
    try {
      const r = await autoApi.post("/admin/sources/import", {
        source, limit: 100, ids, skip_duplicates: true,
      });
      alert(`Создано: ${r.data.created} · Обновлено: ${r.data.updated} · Пропущено: ${r.data.skipped} · Ошибок: ${r.data.failed}`);
      await loadRuns();
    } catch (e) {
      alert(e.response?.data?.detail || "Ошибка импорта.");
    } finally { setBusy(false); }
  };

  return (
    <div style={{ display: "grid", gap: 14 }} data-testid="admin-sources">
      <div className="auto-card" style={{ display: "grid", gap: 10 }}>
        <div style={{ fontWeight: 600 }}>Поиск автомобилей от источников</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 120px auto", gap: 8 }}>
          <select className="auto-select" value={source} onChange={(e) => setSource(e.target.value)} data-testid="sources-source">
            <option value="turners">Turners NZ</option>
            <option value="manheim">Manheim NZ</option>
            <option value="pickles">Pickles AU</option>
          </select>
          <input type="number" className="auto-input" value={limit} onChange={(e) => setLimit(e.target.value)} data-testid="sources-limit" />
          <button type="button" className="auto-btn" onClick={scan} disabled={busy} data-testid="sources-scan-btn">
            {busy ? "Сканируем…" : "Сканировать"}
          </button>
        </div>
        <div className="auto-muted" style={{ fontSize: 13 }}>
          Сканирование не сохраняет автомобили. Выберите интересующие и нажмите «Импортировать выбранные».
        </div>
      </div>

      {result?.ok === false && (
        <div className="auto-card auto-muted" data-testid="sources-error">
          Ошибка: {result.error}
        </div>
      )}

      {result?.ok && (
        <div className="auto-card" data-testid="sources-result">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
            <div>
              <div style={{ fontWeight: 600 }}>
                Найдено: {result.fetched} · Новых: {result.new} · Дубликатов: {result.duplicates}
              </div>
              <div className="auto-muted" style={{ fontSize: 13 }}>Снимите галочки с тех, что не нужны.</div>
            </div>
            <button type="button" className="auto-btn auto-btn-success" onClick={importSelected} disabled={busy} data-testid="sources-import-btn">
              Импортировать выбранные
            </button>
          </div>
          <table className="auto-table" style={{ marginTop: 10 }}>
            <thead>
              <tr>
                <th style={{ width: 30 }}></th>
                <th>Название</th><th>Год</th><th>Цена</th><th>URL</th><th>Статус</th>
              </tr>
            </thead>
            <tbody>
              {(result.items || []).map((it, i) => {
                const v = it.vehicle || {};
                const ref = v.source_reference || `idx-${i}`;
                return (
                  <tr key={ref} data-testid={`sources-row-${ref}`}>
                    <td>
                      <input
                        type="checkbox"
                        checked={!!selected[ref]}
                        onChange={(e) => setSelected({ ...selected, [ref]: e.target.checked })}
                      />
                    </td>
                    <td>{v.title_ru || v.title_original || "?"}</td>
                    <td>{v.year || "—"}</td>
                    <td>{v.current_price_nzd ? `NZ$${v.current_price_nzd}` : "—"}</td>
                    <td className="auto-muted" style={{ fontSize: 12, maxWidth: 280, overflow: "hidden", textOverflow: "ellipsis" }}>
                      {v.source_url ? (
                        <a href={v.source_url} target="_blank" rel="noopener noreferrer" style={{ color: "var(--auto-primary)" }}>
                          {v.source_url.slice(0, 60)}…
                        </a>
                      ) : "—"}
                    </td>
                    <td>
                      {it.is_new
                        ? <span className="auto-badge auto-badge-success">новый</span>
                        : <span className="auto-badge auto-badge-warning">дубликат</span>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <div className="auto-card">
        <div style={{ fontWeight: 600, marginBottom: 8 }}>История запусков</div>
        {runs.length === 0 ? (
          <div className="auto-muted">Запусков пока не было.</div>
        ) : (
          <table className="auto-table">
            <thead><tr><th>Источник</th><th>Получено</th><th>Создано</th><th>Обновлено</th><th>Статус</th><th>Дата</th></tr></thead>
            <tbody>
              {runs.map((r, i) => (
                <tr key={i}>
                  <td>{r.importer}</td>
                  <td>{r.fetched}</td>
                  <td>{r.created}</td>
                  <td>{r.updated}</td>
                  <td><span className="auto-badge">{r.sync_status}</span></td>
                  <td>{r.finished_at ? new Date(r.finished_at).toLocaleString("ru-RU") : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function BrandingTab() {
  const [limit, setLimit] = useState(10);
  const [force, setForce] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);

  const run = async () => {
    setBusy(true); setResult(null);
    try {
      const r = await autoApi.post("/admin/images/backfill-branding", { limit: Number(limit || 10), force });
      setResult(r.data);
    } catch (e) {
      setResult({ error: e.response?.data?.detail || String(e) });
    } finally { setBusy(false); }
  };

  return (
    <div style={{ display: "grid", gap: 14 }} data-testid="admin-branding">
      <div className="auto-card">
        <div style={{ fontWeight: 600, marginBottom: 8 }}>Брендирование фотографий АвтоРесурс</div>
        <p className="auto-muted" style={{ fontSize: 13, marginBottom: 12 }}>
          Скачиваем исходное фото, добавляем шапку с логотипом и подпись «Источник: …» в подвале, сохраняем как локальное брендированное фото.
          Третьи логотипы не удаляются. По умолчанию обрабатываются только автомобили, у которых ещё нет brended-фото.
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "100px auto auto", gap: 10, alignItems: "center" }}>
          <input className="auto-input" type="number" value={limit} onChange={(e) => setLimit(e.target.value)} data-testid="branding-limit" />
          <label style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
            <input type="checkbox" checked={force} onChange={(e) => setForce(e.target.checked)} data-testid="branding-force" />
            <span>Переобработать существующие</span>
          </label>
          <button type="button" className="auto-btn" onClick={run} disabled={busy} data-testid="branding-run-btn">
            {busy ? "Обрабатываем…" : "Запустить брендирование"}
          </button>
        </div>
      </div>
      {result && (
        <div className="auto-card" data-testid="branding-result">
          {result.error ? (
            <div className="auto-muted">Ошибка: {result.error}</div>
          ) : (
            <>
              <div style={{ fontWeight: 600 }}>
                Обработано автомобилей: {result.processed} · создано фото: {result.branded_images}
              </div>
              {result.errors?.length > 0 && (
                <details style={{ marginTop: 8 }}>
                  <summary className="auto-muted">Ошибки ({result.errors.length})</summary>
                  <pre style={{ fontSize: 12, overflowX: "auto" }}>{JSON.stringify(result.errors, null, 2)}</pre>
                </details>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

function AuctionsTab() {
  const [data, setData] = useState(null);
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [c, s] = await Promise.all([
        autoApi.get("/auctions/calendar", { params: { days_ahead: 21 } }),
        autoApi.get("/admin/scheduler/status"),
      ]);
      setData(c.data);
      setStatus(s.data);
    } catch {}
  }, []);
  useEffect(() => { load(); }, [load]);

  const refresh = async () => {
    setBusy(true);
    try {
      await autoApi.post("/admin/auctions/refresh", { categories: ["cars"] });
      await load();
    } catch (e) { alert(e.response?.data?.detail || "Ошибка."); }
    finally { setBusy(false); }
  };

  return (
    <div style={{ display: "grid", gap: 14 }} data-testid="admin-auctions">
      <div className="auto-card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
          <div>
            <div style={{ fontWeight: 600 }}>Календарь аукционов</div>
            <div className="auto-muted" style={{ fontSize: 13 }}>
              Автообновление: {status?.running ? "✓ включено" : "✗ выключено"}
              {status?.last_run_at && ` · последний запуск ${new Date(status.last_run_at).toLocaleString("ru-RU")}`}
              {data && ` · сейчас в базе: ${data.count} событий`}
            </div>
          </div>
          <button type="button" className="auto-btn" onClick={refresh} disabled={busy} data-testid="auctions-refresh-admin-btn">
            {busy ? "Обновляем…" : "Обновить сейчас"}
          </button>
        </div>
      </div>
      {data?.by_day?.length > 0 && (
        <div className="auto-card">
          <table className="auto-table">
            <thead><tr><th>Дата</th><th>Аукционов</th><th>Лотов</th><th>Города</th></tr></thead>
            <tbody>
              {data.by_day.map((d) => (
                <tr key={d.date}>
                  <td>{d.date}</td>
                  <td>{d.events}</td>
                  <td style={{ fontWeight: 700 }}>{d.lots}</td>
                  <td className="auto-muted">{d.cities.join(", ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
