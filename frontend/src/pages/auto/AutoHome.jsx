import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ShieldCheck,
  FileText,
  Headphones,
  Globe2,
  Search,
  SlidersHorizontal,
  Car,
  Wrench,
  CalendarDays,
  Trophy,
  Truck,
  ArrowRight,
} from "lucide-react";
import autoApi from "../../services/autoApi";

const HERO_BG =
  "https://images.unsplash.com/photo-1542362567-b07e54358753?q=80&w=1800&auto=format&fit=crop";

const FALLBACK_AUCTIONS = [
  { city: "Auckland",     source: "Turners",  lots: "997 лотов",   time: "02 : 15 : 30",       label: "Завершается скоро" },
  { city: "Christchurch", source: "Manheim",  lots: "743 лота",    time: "14 : 22 : 45",       label: "Через 1 день" },
  { city: "Auckland",     source: "Pickles",  lots: "1 120 лотов", time: "2 дн : 03 : 10",     label: "Через 2 дня" },
  { city: "Wellington",   source: "Turners",  lots: "612 лотов",   time: "3 дн : 11 : 40",     label: "Через 3 дня" },
];

const FALLBACK_CATEGORIES = [
  { title: "Повреждённые автомобили", count: "1 248 авто", to: "/auto/damaged" },
  { title: "Купить сейчас",            count: "892 авто",   to: "/auto/buynow" },
  { title: "Коммерческий транспорт",   count: "456 авто",   to: "/auto/catalog?body=commercial" },
  { title: "Premium & Luxury",         count: "312 авто",   to: "/auto/catalog?segment=premium" },
  { title: "Списанные авто",            count: "1 932 авто", to: "/auto/end-of-life" },
];

function relLabel(starts_at) {
  if (!starts_at) return "Скоро";
  const ms = new Date(starts_at).getTime() - Date.now();
  if (ms <= 0) return "Идёт сейчас";
  const days = Math.floor(ms / 86400000);
  if (days === 0) return "Завершается скоро";
  if (days === 1) return "Через 1 день";
  return `Через ${days} дня`;
}

function durationLabel(starts_at) {
  if (!starts_at) return "—";
  const ms = new Date(starts_at).getTime() - Date.now();
  if (ms <= 0) return "00 : 00 : 00";
  const days = Math.floor(ms / 86400000);
  const hours = Math.floor((ms / 3600000) % 24);
  const mins = Math.floor((ms / 60000) % 60);
  const secs = Math.floor((ms / 1000) % 60);
  const pad = (n) => String(n).padStart(2, "0");
  if (days > 0) return `${days} дн : ${pad(hours)} : ${pad(mins)}`;
  return `${pad(hours)} : ${pad(mins)} : ${pad(secs)}`;
}

const SOURCE_FROM_BRANCH = (branch = "") => {
  const b = (branch || "").toLowerCase();
  if (b.includes("porirua") || b.includes("manukau")) return "Pickles";
  if (b.includes("penrose") || b.includes("avalon")) return "Manheim";
  return "Turners";
};

export default function AutoHome() {
  const navigate = useNavigate();
  const [auctions, setAuctions] = useState(FALLBACK_AUCTIONS);
  const [totals, setTotals] = useState({ total: 1248, damaged: 1248, buy_now: 892 });
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setTick((x) => x + 1), 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const [cal, sum] = await Promise.all([
          autoApi.get("/auctions/calendar?days=10"),
          autoApi.get("/catalog-summary"),
        ]);
        const events = (cal.data?.events || []).slice(0, 4);
        if (events.length) {
          setAuctions(
            events.map((e) => ({
              city: e.city || e.branch || "—",
              source: SOURCE_FROM_BRANCH(e.branch),
              lots: `${(e.lot_count || 0).toLocaleString("ru-RU")} лотов`,
              starts_at: e.starts_at,
              label: relLabel(e.starts_at),
            }))
          );
        }
        const s = sum.data || {};
        setTotals({
          total: s.total ?? 1248,
          damaged: s.damaged ?? 1248,
          buy_now: s.buy_now ?? 892,
        });
      } catch {}
    })();
  }, []);

  const goCatalog = () => navigate("/auto/catalog");

  return (
    <main className="auto-home min-h-screen bg-[#05070B] text-white -mx-4 lg:-mx-6" data-testid="auto-home">
      {/* HERO */}
      <section className="relative overflow-hidden" data-testid="hero">
        <div
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(circle at 65% 40%, rgba(0,102,255,0.35), transparent 35%), linear-gradient(to bottom, #07111F, #05070B)",
          }}
        />
        <div
          className="absolute right-0 top-0 h-full w-2/3 bg-cover bg-center opacity-60"
          style={{ backgroundImage: `url('${HERO_BG}')` }}
        />
        <div className="absolute inset-0 bg-gradient-to-r from-[#05070B] via-[#05070B]/80 to-[#05070B]/20" />

        <div className="relative mx-auto max-w-7xl px-6 py-20">
          <div className="max-w-2xl">
            <h1 className="text-5xl font-black leading-tight md:text-7xl">
              Автомобили <br />
              <span className="text-white">со всего мира</span>
            </h1>
            <p className="mt-6 text-xl leading-relaxed text-gray-300">
              Аукционные, повреждённые и целые автомобили из Новой Зеландии
              и Австралии под заказ.
            </p>

            <div className="mt-8 grid grid-cols-2 gap-4 text-sm text-gray-300 md:grid-cols-4">
              <Feature icon={<ShieldCheck />} text="Проверенные площадки" />
              <Feature icon={<FileText />} text="Прозрачные условия" />
              <Feature icon={<Headphones />} text="Поддержка на каждом этапе" />
              <Feature icon={<Globe2 />} text="Доставка по всему миру" />
            </div>

            <div className="mt-10 flex flex-wrap gap-4">
              <button
                onClick={goCatalog}
                className="rounded-xl bg-blue-600 px-7 py-4 font-bold transition hover:bg-blue-500"
                data-testid="cta-view-cars"
              >
                Смотреть автомобили <ArrowRight className="ml-2 inline h-5 w-5" />
              </button>
              <Link
                to="/auto/fees"
                className="rounded-xl border border-white/15 bg-white/5 px-7 py-4 font-bold transition hover:bg-white/10"
                data-testid="cta-how-it-works"
              >
                Как это работает
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* SEARCH PANEL */}
      <section className="mx-auto -mt-10 max-w-7xl px-6">
        <div className="relative z-10 rounded-2xl border border-white/10 bg-[#111827]/90 p-5 shadow-2xl backdrop-blur-xl" data-testid="search-panel">
          <div className="mb-4 flex flex-wrap gap-3">
            <Tab icon={<Car />} text="Все автомобили" active onClick={() => navigate("/auto/catalog")} />
            <Tab icon={<Wrench />} text="Повреждённые" onClick={() => navigate("/auto/damaged")} />
            <Tab icon={<CalendarDays />} text="Купить сейчас" onClick={() => navigate("/auto/buynow")} />
          </div>

          <div className="grid gap-3 md:grid-cols-6">
            <SelectStatic label="Марка" value="Любая марка" />
            <SelectStatic label="Модель" value="Любая модель" />
            <SelectStatic label="Год от" value="2010" />
            <SelectStatic label="Год до" value="2024" />
            <SelectStatic label="Цена от" value="NZ$ 0" />
            <SelectStatic label="Цена до" value="NZ$ 100 000+" />
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
            <button
              onClick={goCatalog}
              className="rounded-xl bg-blue-600 px-8 py-3 font-bold transition hover:bg-blue-500"
              data-testid="search-submit"
            >
              <Search className="mr-2 inline h-5 w-5" />
              Найти {(totals.total || 0).toLocaleString("ru-RU")}
            </button>
            <Link
              to="/auto/catalog"
              className="text-sm text-gray-300 transition hover:text-white"
              data-testid="advanced-search"
            >
              <SlidersHorizontal className="mr-2 inline h-5 w-5 text-blue-500" />
              Расширенный поиск
            </Link>
          </div>
        </div>
      </section>

      {/* CONTENT */}
      <section className="mx-auto grid max-w-7xl gap-6 px-6 py-10 lg:grid-cols-3">
        {/* AUCTIONS */}
        <div className="rounded-2xl border border-white/10 bg-[#0D111A] p-5 lg:col-span-2" data-testid="upcoming-auctions">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-2xl font-bold">Ближайшие аукционы</h2>
            <Link to="/auto/auctions" className="text-sm text-blue-400 hover:text-blue-300" data-testid="see-calendar">
              Смотреть календарь →
            </Link>
          </div>

          <div className="grid gap-4 md:grid-cols-4">
            {auctions.map((a, i) => (
              <div
                key={`${a.city}-${i}`}
                className="rounded-xl border border-white/10 bg-white/[0.03] p-4 transition hover:border-blue-500/60"
                data-testid={`auction-card-${i}`}
              >
                <span className="inline-block rounded-md bg-blue-600 px-2 py-1 text-xs font-bold">
                  {a.label}
                </span>
                <div className="mt-4 font-mono text-lg font-bold">
                  {a.starts_at ? durationLabel(a.starts_at) : a.time}
                </div>
                <div className="mt-4 text-lg font-bold">{a.city}</div>
                <div className="text-sm text-gray-400">{a.source}</div>
                <div className="mt-1 text-sm text-gray-300">{a.lots}</div>
                <Link
                  to="/auto/auctions"
                  className="mt-4 inline-block text-sm font-semibold text-blue-400 hover:text-blue-300"
                  data-testid={`auction-card-${i}-link`}
                >
                  Смотреть лоты →
                </Link>
              </div>
            ))}
          </div>
        </div>

        {/* STATS */}
        <div className="rounded-2xl border border-white/10 bg-[#0D111A] p-5" data-testid="stats">
          <h2 className="mb-5 text-2xl font-bold">Почему выбирают нас</h2>
          <div className="grid gap-4 grid-cols-2">
            <Stat icon={<Trophy />} number="10+" text="Аукционных площадок" />
            <Stat icon={<Car />} number="50 000+" text="Автомобилей ежемесячно" />
            <Stat icon={<Globe2 />} number="30+" text="Стран доставки" />
            <Stat icon={<ShieldCheck />} number="100%" text="Прозрачные условия" />
          </div>
        </div>

        {/* CATEGORIES */}
        <div className="lg:col-span-2" data-testid="popular-categories">
          <h2 className="mb-5 text-2xl font-bold">Популярные категории</h2>
          <div className="grid gap-4 md:grid-cols-5">
            {FALLBACK_CATEGORIES.map((c, i) => (
              <Link
                key={c.title}
                to={c.to}
                className="group block rounded-2xl border border-white/10 bg-[#0D111A] p-4 transition hover:border-blue-500/60"
                data-testid={`category-${i}`}
              >
                <div className="text-sm font-bold">{c.title}</div>
                <div className="mt-1 text-sm text-gray-400">{c.count}</div>
                <div className="mt-8 h-16 rounded-xl bg-gradient-to-br from-blue-600/40 to-transparent opacity-70 transition group-hover:opacity-100" />
              </Link>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div
          className="rounded-2xl border border-white/10 p-6"
          style={{ background: "linear-gradient(135deg, #0D111A 0%, rgba(6,44,117,0.4) 100%)" }}
          data-testid="cta-request"
        >
          <h2 className="text-2xl font-bold">Хотите найти конкретный автомобиль?</h2>
          <p className="mt-3 text-gray-300">
            Оставьте заявку, и мы найдём автомобиль под ваши требования.
          </p>
          <Link
            to="/auto/fees"
            className="mt-6 inline-block rounded-xl bg-blue-600 px-6 py-3 font-bold transition hover:bg-blue-500"
            data-testid="cta-request-btn"
          >
            Оставить заявку
          </Link>
        </div>
      </section>

      {/* FOOTER FEATURES */}
      <section className="mx-auto grid max-w-7xl gap-4 px-6 pb-12 md:grid-cols-4" data-testid="footer-features">
        <FooterFeature icon={<FileText />} title="Профессиональная инспекция" text="Фото и видео отчёты" />
        <FooterFeature icon={<FileText />} title="Помощь с документами" text="Полное сопровождение" />
        <FooterFeature icon={<ShieldCheck />} title="Без скрытых платежей" text="Прозрачное ценообразование" />
        <FooterFeature icon={<Truck />} title="Доставка под ключ" text="От склада до вашего порта" />
      </section>
    </main>
  );
}

function Feature({ icon, text }) {
  return (
    <div className="flex items-center gap-3">
      {React.cloneElement(icon, { className: "h-6 w-6 text-blue-500" })}
      <span>{text}</span>
    </div>
  );
}

function Tab({ icon, text, active, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-xl px-4 py-2 text-sm transition ${
        active ? "bg-blue-600 text-white" : "bg-white/5 text-gray-300 hover:bg-white/10"
      }`}
    >
      {React.cloneElement(icon, { className: "mr-2 inline h-4 w-4" })}
      {text}
    </button>
  );
}

function SelectStatic({ label, value }) {
  return (
    <div className="rounded-xl bg-[#0B0F17] p-3">
      <div className="text-xs uppercase tracking-wider text-gray-500">{label}</div>
      <div className="mt-1 font-semibold">{value}</div>
    </div>
  );
}

function Stat({ icon, number, text }) {
  return (
    <div className="rounded-xl bg-white/[0.03] p-4">
      {React.cloneElement(icon, { className: "mb-3 h-7 w-7 text-blue-500" })}
      <div className="text-2xl font-black text-blue-500">{number}</div>
      <div className="text-sm text-gray-400">{text}</div>
    </div>
  );
}

function FooterFeature({ icon, title, text }) {
  return (
    <div className="flex items-center gap-4 rounded-2xl bg-[#0D111A] p-4">
      {React.cloneElement(icon, { className: "h-7 w-7 text-blue-500" })}
      <div>
        <div className="font-bold">{title}</div>
        <div className="text-sm text-gray-400">{text}</div>
      </div>
    </div>
  );
}
