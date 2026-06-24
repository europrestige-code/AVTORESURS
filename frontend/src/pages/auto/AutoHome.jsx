import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import autoApi from "../../services/autoApi";
import CountdownTimer from "../../components/auto/CountdownTimer";
import {
  ShieldCheck, FileText, Headphones, Globe2,
  Search, SlidersHorizontal,
  Car, Wrench, CalendarDays, Trophy, Truck,
  ArrowRight, CreditCard, FileSearch, Package,
} from "lucide-react";

const HERO_BG =
  "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?q=80&w=1800&auto=format&fit=crop";

const FALLBACK_AUCTIONS = [
  { key: "f1", city: "Auckland",     branch: "Auckland",      lots: 997,  starts_at: new Date(Date.now() + 2 * 3600e3 + 15 * 60e3).toISOString(), title: "Big Wednesday Auction", auction_url: "/auto/auctions" },
  { key: "f2", city: "Christchurch", branch: "Hornby",        lots: 743,  starts_at: new Date(Date.now() + 1 * 86400e3 + 14 * 3600e3).toISOString(), title: "Damaged Vehicles", auction_url: "/auto/auctions" },
  { key: "f3", city: "Auckland",     branch: "Penrose",       lots: 1120, starts_at: new Date(Date.now() + 2 * 86400e3 + 3 * 3600e3).toISOString(),  title: "Light Commercial", auction_url: "/auto/auctions" },
  { key: "f4", city: "Wellington",   branch: "Porirua",       lots: 612,  starts_at: new Date(Date.now() + 3 * 86400e3 + 11 * 3600e3).toISOString(), title: "Wellington Cars", auction_url: "/auto/auctions" },
];

const SOURCE_FROM_BRANCH = (branch = "") => {
  const b = branch.toLowerCase();
  if (b.includes("hornby") || b.includes("moorhouse") || b.includes("wairakei")) return "Turners";
  if (b.includes("porirua") || b.includes("manukau")) return "Pickles";
  if (b.includes("penrose") || b.includes("avalon")) return "Manheim";
  return "Turners";
};

function relLabel(starts_at) {
  if (!starts_at) return { label: "Скоро", cls: "bg-blue-600" };
  const ms = new Date(starts_at).getTime() - Date.now();
  if (ms <= 0) return { label: "Завершён", cls: "bg-red-600" };
  const h = ms / 3_600_000;
  if (h <= 12) return { label: "Завершается скоро", cls: "bg-emerald-600" };
  const d = Math.floor(h / 24);
  if (d === 0) return { label: "Сегодня", cls: "bg-amber-600" };
  return { label: `Через ${d} ${d === 1 ? "день" : d < 5 ? "дня" : "дней"}`, cls: "bg-amber-600" };
}

const CATEGORY_DEFS_LOCAL = [
  { key: "damaged",    title: "Повреждённые автомобили", to: "/auto/damaged",
    img: "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?auto=format&fit=crop&w=600&q=70" },
  { key: "buynow",     title: "Купить сейчас",           to: "/auto/buynow",
    img: "https://images.unsplash.com/photo-1610647752706-3bb12232b3ab?auto=format&fit=crop&w=600&q=70" },
  { key: "commercial", title: "Коммерческий транспорт",  to: "/auto/catalog?body_type=Фургон",
    img: "https://images.unsplash.com/photo-1597009622933-ffeefbc4b51a?auto=format&fit=crop&w=600&q=70" },
  { key: "premium",    title: "Premium & Luxury",        to: "/auto/catalog?price_from=20000",
    img: "https://images.unsplash.com/photo-1542362567-b07e54358753?auto=format&fit=crop&w=600&q=70" },
  { key: "eol",        title: "Списанные авто",          to: "/auto/end-of-life",
    img: "https://images.unsplash.com/photo-1567808291548-fc3ee04dbcf0?auto=format&fit=crop&w=600&q=70" },
];

export default function AutoHome() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [auctions, setAuctions] = useState([]);
  const [tab, setTab] = useState("all");
  const [form, setForm] = useState({ make: "", model: "", yFrom: "", yTo: "", pFrom: "", pTo: "" });

  useEffect(() => {
    autoApi.get("/catalog-summary").then((r) => setSummary(r.data)).catch(() => {});
    autoApi.get("/auctions/calendar", { params: { days_ahead: 14 } })
      .then((r) => {
        const evts = (r.data?.events || []).slice(0, 4);
        setAuctions(evts.length ? evts : FALLBACK_AUCTIONS);
      })
      .catch(() => setAuctions(FALLBACK_AUCTIONS));
  }, []);

  const total = summary?.total ?? 0;
  const makes = summary?.makes || [];
  const models = summary?.models_by_make?.[form.make] || [];
  const counts = {
    damaged: summary?.damaged_count ?? null,
    buynow: (summary?.listing_types || []).find((x) => x.value === "fixed_price")?.count ?? null,
    eol: summary?.eol_count ?? null,
  };

  const goSearch = () => {
    const p = new URLSearchParams();
    if (tab === "damaged") p.set("condition", "Повреждённое");
    if (tab === "buynow") p.set("listing_type", "fixed_price");
    Object.entries({ make: form.make, model: form.model, year_from: form.yFrom, year_to: form.yTo, price_from: form.pFrom, price_to: form.pTo })
      .forEach(([k, v]) => { if (v) p.set(k, v); });
    navigate(`/auto/catalog?${p.toString()}`);
  };

  return (
    <div className="ah-tw">
      {/* HERO */}
      <section className="relative overflow-hidden rounded-3xl border border-white/10 mt-2">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_65%_40%,rgba(0,102,255,0.35),transparent_35%),linear-gradient(to_bottom,#07111F,#05070B)]" />
        <div className="absolute right-0 top-0 h-full w-2/3 opacity-50 bg-cover bg-center" style={{ backgroundImage: `url(${HERO_BG})` }} />
        <div className="absolute inset-0 bg-gradient-to-r from-[#05070B] via-[#05070B]/80 to-[#05070B]/20" />
        <div className="relative px-6 py-16 lg:px-12 lg:py-20" data-testid="ah-hero">
          <div className="max-w-2xl">
            <h1 className="text-4xl font-black leading-tight md:text-6xl text-white">
              Автомобили<br />
              <span className="text-white">со всего мира</span>
            </h1>
            <p className="mt-6 text-lg leading-relaxed text-gray-300 md:text-xl">
              Аукционные, повреждённые и целые автомобили из Новой Зеландии и Австралии под заказ.
            </p>
            <div className="mt-8 grid grid-cols-2 gap-4 text-sm text-gray-300 md:grid-cols-4">
              <Trust Icon={ShieldCheck} text="Проверенные площадки" />
              <Trust Icon={FileText}    text="Прозрачные условия" />
              <Trust Icon={Headphones}  text="Поддержка на каждом этапе" />
              <Trust Icon={Globe2}      text="Доставка по всему миру" />
            </div>
            <div className="mt-10 flex flex-wrap gap-3">
              <Link to="/auto/catalog" className="inline-flex items-center rounded-xl bg-blue-600 px-6 py-3 font-bold text-white hover:bg-blue-500" data-testid="ah-cta-catalog">
                Смотреть автомобили <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
              <Link to="/auto/how-it-works" className="rounded-xl border border-white/15 bg-white/5 px-6 py-3 font-bold text-white hover:bg-white/10" data-testid="ah-cta-how">
                Как это работает
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* SEARCH PANEL */}
      <section className="relative -mt-8 px-2" data-testid="ah-mega-search">
        <div className="relative z-10 rounded-2xl border border-white/10 bg-[#111827]/95 p-5 shadow-2xl backdrop-blur-xl">
          <div className="mb-4 flex flex-wrap gap-2">
            <SearchTab Icon={Car}           text="Все автомобили" active={tab === "all"}     onClick={() => setTab("all")}     testid="ah-tab-all" />
            <SearchTab Icon={Wrench}        text="Повреждённые"   active={tab === "damaged"} onClick={() => setTab("damaged")} testid="ah-tab-damaged" />
            <SearchTab Icon={CreditCard}    text="Купить сейчас"  active={tab === "buynow"}  onClick={() => setTab("buynow")}  testid="ah-tab-buynow" />
          </div>
          <div className="grid gap-3 md:grid-cols-6">
            <FieldSelect label="Марка" value={form.make} onChange={(v) => setForm({ ...form, make: v, model: "" })} testid="ah-make">
              <option value="">Любая марка</option>
              {makes.map((m) => <option key={m.value} value={m.value}>{m.value} ({m.count})</option>)}
            </FieldSelect>
            <FieldSelect label="Модель" value={form.model} onChange={(v) => setForm({ ...form, model: v })} disabled={!form.make} testid="ah-model">
              <option value="">Любая модель</option>
              {models.map((m) => <option key={m.value} value={m.value}>{m.value}</option>)}
            </FieldSelect>
            <FieldInput label="Год от" placeholder="2010" value={form.yFrom} onChange={(v) => setForm({ ...form, yFrom: v })} testid="ah-year-from" />
            <FieldInput label="Год до" placeholder="2024" value={form.yTo}   onChange={(v) => setForm({ ...form, yTo: v })}   testid="ah-year-to" />
            <FieldInput label="Цена от" placeholder="NZ$ 0" value={form.pFrom} onChange={(v) => setForm({ ...form, pFrom: v })} testid="ah-price-from" />
            <FieldInput label="Цена до" placeholder="NZ$ 100 000+" value={form.pTo} onChange={(v) => setForm({ ...form, pTo: v })} testid="ah-price-to" />
          </div>
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
            <button type="button" onClick={goSearch} className="inline-flex items-center rounded-xl bg-blue-600 px-7 py-3 font-bold text-white hover:bg-blue-500" data-testid="ah-mega-submit">
              <Search className="mr-2 h-5 w-5" />
              Найти ({total.toLocaleString("ru-RU")})
            </button>
            <Link to="/auto/catalog" className="text-sm text-gray-300 hover:text-white" data-testid="ah-advanced">
              <SlidersHorizontal className="mr-2 inline h-5 w-5 text-blue-500" />
              Расширенный поиск
            </Link>
          </div>
        </div>
      </section>

      {/* AUCTIONS + STATS */}
      <section className="mt-10 grid gap-6 lg:grid-cols-3">
        <div className="rounded-2xl border border-white/10 bg-[#0D111A] p-5 lg:col-span-2" data-testid="ah-upcoming">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-2xl font-bold">Ближайшие аукционы</h2>
            <Link to="/auto/auctions" className="text-sm text-blue-400 hover:text-blue-300">Смотреть календарь →</Link>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {auctions.map((a) => {
              const pill = relLabel(a.starts_at);
              const source = SOURCE_FROM_BRANCH(a.branch || a.city);
              return (
                <a
                  key={a.key || a.auction_url}
                  href={a.auction_url || "/auto/auctions"}
                  target={a.auction_url && a.auction_url.startsWith("http") ? "_blank" : undefined}
                  rel="noopener noreferrer"
                  className="block rounded-xl border border-white/10 bg-white/[0.03] p-4 transition hover:border-blue-500/60"
                  data-testid={`ah-auction-${a.key || a.auction_url}`}
                >
                  <span className={`inline-block rounded-md ${pill.cls} px-2 py-1 text-xs font-bold text-white`}>
                    {pill.label}
                  </span>
                  <div className="mt-3 font-mono text-base font-bold tabular-nums">
                    <CountdownTimer target={a.starts_at} compact testid={`ah-cd-${a.key}`} />
                  </div>
                  <div className="mt-3 text-lg font-bold">{a.city || a.branch}</div>
                  <div className="text-sm text-gray-400">{source}</div>
                  <div className="mt-1 text-sm text-gray-300">{a.lots} {pluralLots(a.lots)}</div>
                  <span className="mt-4 inline-block text-sm font-semibold text-blue-400">
                    Смотреть лоты →
                  </span>
                </a>
              );
            })}
          </div>
        </div>
        <div className="rounded-2xl border border-white/10 bg-[#0D111A] p-5" data-testid="ah-why">
          <h2 className="mb-5 text-2xl font-bold">Почему выбирают нас</h2>
          <div className="grid gap-3">
            <StatTile Icon={Trophy}      number="10+"      text="Аукционных площадок" />
            <StatTile Icon={Car}         number="50 000+"  text="Автомобилей ежемесячно" />
            <StatTile Icon={Globe2}      number="30+"      text="Стран доставки" />
            <StatTile Icon={ShieldCheck} number="100%"     text="Прозрачные условия" />
          </div>
        </div>
      </section>

      {/* CATEGORIES + CTA */}
      <section className="mt-10 grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2" data-testid="ah-popular">
          <h2 className="mb-5 text-2xl font-bold">Популярные категории</h2>
          <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-5">
            {CATEGORY_DEFS_LOCAL.map((c) => {
              const n = counts[c.key];
              return (
                <Link
                  key={c.key}
                  to={c.to}
                  className="group block overflow-hidden rounded-2xl border border-white/10 bg-[#0D111A] transition hover:border-blue-500/60"
                  data-testid={`ah-cat-${c.key}`}
                >
                  <div
                    className="h-28 bg-cover bg-center"
                    style={{ backgroundImage: `linear-gradient(to top, rgba(13,17,26,0.85), rgba(13,17,26,0.1)), url(${c.img})` }}
                  />
                  <div className="p-4">
                    <div className="text-sm font-bold text-white">{c.title}</div>
                    <div className="mt-1 text-sm text-gray-400">{n != null ? `${n.toLocaleString("ru-RU")} авто` : "Каталог"}</div>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
        <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-[#0D111A] to-[#062C75]/40 p-6" data-testid="ah-cta-find">
          <h2 className="text-2xl font-bold">Хотите найти конкретный автомобиль?</h2>
          <p className="mt-3 text-gray-300">
            Оставьте заявку и мы найдём автомобиль под ваши требования.
          </p>
          <Link to="/auto/catalog" className="mt-6 inline-flex items-center rounded-xl bg-blue-600 px-6 py-3 font-bold text-white hover:bg-blue-500">
            Оставить заявку <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* FOOTER FEATURES */}
      <section className="mt-10 mb-12 grid gap-4 md:grid-cols-2 lg:grid-cols-4" data-testid="ah-benefits">
        <Feature Icon={FileSearch}     title="Профессиональная инспекция" text="Фото и видео отчёты" />
        <Feature Icon={FileText}       title="Помощь с документами"       text="Полное сопровождение" />
        <Feature Icon={ShieldCheck}    title="Без скрытых платежей"       text="Прозрачное ценообразование" />
        <Feature Icon={Truck}          title="Доставка под ключ"          text="От склада до вашего порога" />
      </section>
    </div>
  );
}

function pluralLots(n) {
  const i = Number(n) || 0;
  const m10 = i % 10;
  const m100 = i % 100;
  if (m10 === 1 && m100 !== 11) return "лот";
  if ([2, 3, 4].includes(m10) && ![12, 13, 14].includes(m100)) return "лота";
  return "лотов";
}

function Trust({ Icon, text }) {
  return (
    <div className="flex items-center gap-3">
      <Icon className="h-6 w-6 shrink-0 text-blue-500" />
      <span>{text}</span>
    </div>
  );
}

function SearchTab({ Icon, text, active, onClick, testid }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm transition ${active ? "bg-blue-600 text-white" : "bg-white/5 text-gray-300 hover:bg-white/10"}`}
      data-testid={testid}
    >
      <Icon className="h-4 w-4" />
      {text}
    </button>
  );
}

function FieldSelect({ label, value, onChange, children, disabled, testid }) {
  return (
    <label className="block rounded-xl bg-[#0B0F17] p-3">
      <div className="text-xs uppercase tracking-wider text-gray-500">{label}</div>
      <select
        className="mt-1 w-full bg-transparent font-semibold text-white outline-none"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        data-testid={testid}
      >
        {children}
      </select>
    </label>
  );
}

function FieldInput({ label, placeholder, value, onChange, testid }) {
  return (
    <label className="block rounded-xl bg-[#0B0F17] p-3">
      <div className="text-xs uppercase tracking-wider text-gray-500">{label}</div>
      <input
        type="number"
        className="mt-1 w-full bg-transparent font-semibold text-white outline-none placeholder:text-gray-500"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        data-testid={testid}
      />
    </label>
  );
}

function StatTile({ Icon, number, text }) {
  return (
    <div className="flex items-start gap-4 rounded-xl bg-white/[0.03] p-4">
      <Icon className="h-7 w-7 shrink-0 text-blue-500" />
      <div>
        <div className="text-2xl font-black text-blue-500">{number}</div>
        <div className="text-sm text-gray-400">{text}</div>
      </div>
    </div>
  );
}

function Feature({ Icon, title, text }) {
  return (
    <div className="flex items-center gap-4 rounded-2xl bg-[#0D111A] p-4">
      <Icon className="h-7 w-7 shrink-0 text-blue-500" />
      <div>
        <div className="font-bold text-white">{title}</div>
        <div className="text-sm text-gray-400">{text}</div>
      </div>
    </div>
  );
}
