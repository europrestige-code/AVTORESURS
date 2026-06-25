import React, { useEffect, useMemo, useState } from "react";
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
  ChevronRight,
} from "lucide-react";
import autoApi from "../../services/autoApi";
import BodyTypeStrip from "../../components/auto/BodyTypeStrip";
import LiveMarketStrip from "../../components/auto/LiveMarketStrip";
import DepositExplainer from "../../components/auto/DepositExplainer";
import EndingSoonCarousel from "../../components/auto/EndingSoonCarousel";
import LeadModal from "../../components/auto/LeadModal";
import { getFxRate, formatRub } from "../../services/autoCurrency";

/* ==========================================================================
 * Imagery — placeholder URLs; replace with API-driven photos once available.
 * ========================================================================== */
const HERO_IMG =
  "https://images.unsplash.com/photo-1542362567-b07e54358753?q=80&w=2000&auto=format&fit=crop";
const HERO_MAP_OVERLAY =
  "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2000&auto=format&fit=crop"; // earth/network feel

const CATEGORY_IMAGES = {
  // User-supplied: smashed black Porsche 911 at an auction yard (IAA)
  damaged:    "/branding/damaged-porsche.jpg",
  buynow:     "https://images.unsplash.com/photo-1503376780353-7e6692767b70?q=80&w=900&auto=format&fit=crop",
  commercial: "https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?q=80&w=900&auto=format&fit=crop",
  premium:    "https://images.unsplash.com/photo-1555215695-3004980ad54e?q=80&w=900&auto=format&fit=crop",
  // User-supplied: red 1990s Toyota Prado SWB — classic EOL/JDM-export shot
  eol:        "/branding/eol-prado.webp",
};

/* Per-branch hero image. The user requested a relevant photo per Turners
 * site (Napier, Hornby, Otahuhu, …). Each branch maps to an Unsplash photo
 * that suits the location — outdoor NZ car-yard, urban skyline, etc. Falls
 * back to the generic AUCTION_IMAGES rotation when the branch is unknown. */
const BRANCH_IMAGES = {
  "Уонгареи":              "https://images.unsplash.com/photo-1583121274602-3e2820c69888?q=80&w=900&auto=format&fit=crop",
  "Норт-Шор":              "https://images.unsplash.com/photo-1502877338535-766e1452684a?q=80&w=900&auto=format&fit=crop",
  "Окленд":                "https://images.unsplash.com/photo-1502877338535-766e1452684a?q=80&w=900&auto=format&fit=crop",
  "Отахуху":               "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?q=80&w=900&auto=format&fit=crop",
  "Гамильтон":             "https://images.unsplash.com/photo-1542362567-b07e54358753?q=80&w=900&auto=format&fit=crop",
  "Гамильтон (Avalon Drive)":"https://images.unsplash.com/photo-1542362567-b07e54358753?q=80&w=900&auto=format&fit=crop",
  "Гамильтон (Te Rapa)":   "https://images.unsplash.com/photo-1542362567-b07e54358753?q=80&w=900&auto=format&fit=crop",
  "Тауранга":              "https://images.unsplash.com/photo-1554744512-d6c603f27c54?q=80&w=900&auto=format&fit=crop",
  "Роторуа":               "https://images.unsplash.com/photo-1554744512-d6c603f27c54?q=80&w=900&auto=format&fit=crop",
  "Нэйпир":                "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?q=80&w=900&auto=format&fit=crop",
  "Палмерстон-Норт":       "https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?q=80&w=900&auto=format&fit=crop",
  "Нью-Плимут":            "https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?q=80&w=900&auto=format&fit=crop",
  "Порируа":               "https://images.unsplash.com/photo-1503376780353-7e6692767b70?q=80&w=900&auto=format&fit=crop",
  "Веллингтон":            "https://images.unsplash.com/photo-1503376780353-7e6692767b70?q=80&w=900&auto=format&fit=crop",
  "Нельсон":               "https://images.unsplash.com/photo-1583121274602-3e2820c69888?q=80&w=900&auto=format&fit=crop",
  "Бленем":                "https://images.unsplash.com/photo-1583121274602-3e2820c69888?q=80&w=900&auto=format&fit=crop",
  "Крайстчёрч":            "https://images.unsplash.com/photo-1591293836027-e05b48473b67?q=80&w=900&auto=format&fit=crop",
  "Крайстчёрч (Hornby)":   "https://images.unsplash.com/photo-1591293836027-e05b48473b67?q=80&w=900&auto=format&fit=crop",
  "Тимару":                "https://images.unsplash.com/photo-1591293836027-e05b48473b67?q=80&w=900&auto=format&fit=crop",
  "Данидин":               "https://images.unsplash.com/photo-1517649763962-0c623066013b?q=80&w=900&auto=format&fit=crop",
  "Инверкаргилл":          "https://images.unsplash.com/photo-1517649763962-0c623066013b?q=80&w=900&auto=format&fit=crop",
};
const FALLBACK_BRANCH_IMG =
  "https://images.unsplash.com/photo-1502877338535-766e1452684a?q=80&w=900&auto=format&fit=crop";

function imageForBranch(branchOrCity) {
  if (!branchOrCity) return FALLBACK_BRANCH_IMG;
  // direct hit
  if (BRANCH_IMAGES[branchOrCity]) return BRANCH_IMAGES[branchOrCity];
  // substring hit (e.g. "Крайстчёрч (Hornby)" inside a longer label)
  for (const k of Object.keys(BRANCH_IMAGES)) {
    if (branchOrCity.includes(k)) return BRANCH_IMAGES[k];
  }
  return FALLBACK_BRANCH_IMG;
}

const AUCTION_IMAGES = [
  "https://images.unsplash.com/photo-1554744512-d6c603f27c54?q=80&w=900&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?q=80&w=900&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1502877338535-766e1452684a?q=80&w=900&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1542362567-b07e54358753?q=80&w=900&auto=format&fit=crop",
];

const LEAD_CAR_SILHOUETTE =
  "https://images.unsplash.com/photo-1583121274602-3e2820c69888?q=80&w=900&auto=format&fit=crop";

/* ==========================================================================
 * Static / fallback data — replaced by API responses where available.
 * ========================================================================== */
const FALLBACK_AUCTIONS = [
  { city: "Auckland",     source: "Turners", lots: 997,  badge: "Завершается скоро", badgeTone: "green",  starts_at: addMs(2 * 3600e3 + 15 * 60e3) },
  { city: "Christchurch", source: "Manheim", lots: 743,  badge: "Через 1 день",       badgeTone: "orange", starts_at: addMs(86400e3 + 14 * 3600e3) },
  { city: "Auckland",     source: "Pickles", lots: 1120, badge: "Через 2 дня",        badgeTone: "orange", starts_at: addMs(2 * 86400e3 + 3 * 3600e3) },
  { city: "Wellington",   source: "Turners", lots: 612,  badge: "Через 3 дня",        badgeTone: "orange", starts_at: addMs(3 * 86400e3 + 11 * 3600e3) },
];

const CATEGORIES = [
  { key: "damaged",    title: "Повреждённые автомобили", count: 1248, to: "/auto/damaged",   img: CATEGORY_IMAGES.damaged },
  { key: "buynow",     title: "Купить сейчас",            count: 892,  to: "/auto/buynow",    img: CATEGORY_IMAGES.buynow },
  { key: "commercial", title: "Коммерческий транспорт",   count: 456,  to: "/auto/catalog?body=commercial", img: CATEGORY_IMAGES.commercial },
  { key: "premium",    title: "Premium & Luxury",          count: 312,  to: "/auto/catalog?segment=premium", img: CATEGORY_IMAGES.premium },
  { key: "eol",        title: "Списанные авто",            count: 1932, to: "/auto/end-of-life", img: CATEGORY_IMAGES.eol },
];

const TRUST = [
  { icon: ShieldCheck, label: "Проверенные площадки" },
  { icon: FileText,    label: "Прозрачные условия" },
  { icon: Headphones,  label: "Поддержка на каждом этапе" },
  { icon: Globe2,      label: "Доставка по всему миру" },
];

const STATS = [
  { icon: Trophy,      number: "10+",      text: "Аукционных площадок" },
  { icon: Car,         number: "50 000+",  text: "Автомобилей ежемесячно" },
  { icon: Globe2,      number: "30+",      text: "Стран доставки" },
  { icon: ShieldCheck, number: "100%",     text: "Прозрачные условия" },
];

const BOTTOM_FEATURES = [
  { icon: FileText,    title: "Профессиональная инспекция", text: "Фото и видео отчёты" },
  { icon: FileText,    title: "Помощь с документами",       text: "Полное сопровождение" },
  { icon: ShieldCheck, title: "Без скрытых платежей",        text: "Прозрачное ценообразование" },
  { icon: Truck,       title: "Доставка под ключ",           text: "От склада до вашего порога" },
];

function addMs(ms) {
  return new Date(Date.now() + ms).toISOString();
}

function pad(n) { return String(n).padStart(2, "0"); }

function fmtCountdown(iso, nowMs) {
  if (!iso) return "—";
  const ms = new Date(iso).getTime() - nowMs;
  if (ms <= 0) return "00 : 00 : 00";
  const days = Math.floor(ms / 86400000);
  const h = Math.floor((ms / 3600000) % 24);
  const m = Math.floor((ms / 60000) % 60);
  const s = Math.floor((ms / 1000) % 60);
  if (days > 0) return `${days} дн : ${pad(h)} : ${pad(m)} : ${pad(s)}`;
  return `${pad(h)} : ${pad(m)} : ${pad(s)}`;
}

function relLabel(iso) {
  if (!iso) return "Скоро";
  const ms = new Date(iso).getTime() - Date.now();
  if (ms <= 0) return "Идёт сейчас";
  const days = Math.floor(ms / 86400000);
  if (days === 0) return "Завершается скоро";
  if (days === 1) return "Через 1 день";
  return `Через ${days} дн.`;
}

function sourceFromBranch(branch = "") {
  const b = branch.toLowerCase();
  if (b.includes("porirua") || b.includes("manukau")) return "Pickles";
  if (b.includes("penrose") || b.includes("avalon")) return "Manheim";
  return "Turners";
}

/* ==========================================================================
 * Page
 * ========================================================================== */
export default function AutoHome() {
  const navigate = useNavigate();
  const [auctions, setAuctions] = useState(FALLBACK_AUCTIONS);
  const [totals, setTotals] = useState({ total: 1248 });
  const [now, setNow] = useState(Date.now());

  // 1-second tick for countdowns
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  // Warm up FX cache so all <formatRub> calls below render immediately
  useEffect(() => { getFxRate(); }, []);

  // Pull live data
  useEffect(() => {
    (async () => {
      try {
        const [cal, sum] = await Promise.all([
          autoApi.get("/auctions/calendar?days_ahead=10"),
          autoApi.get("/catalog-summary"),
        ]);
        const events = (cal.data?.events || []).slice(0, 4);
        if (events.length) {
          setAuctions(
            events.map((e, i) => {
              const city = e.city || e.branch || "—";
              return {
                city,
                source: sourceFromBranch(e.branch),
                lots: e.lot_count || 0,
                starts_at: e.starts_at,
                badge: relLabel(e.starts_at),
                badgeTone: i === 0 ? "green" : "orange",
                img: imageForBranch(e.branch) || imageForBranch(city),
              };
            })
          );
        }
        if (sum.data) setTotals({ total: sum.data.total ?? 1248 });
      } catch {}
    })();
  }, []);

  return (
    <main className="auto-home-v2 -mx-4 lg:-mx-6 bg-[var(--ar-black)] text-white" data-testid="auto-home">
      <Hero onView={() => navigate("/auto/catalog")} />
      <SearchPanel total={totals.total} onSubmit={() => navigate("/auto/catalog")} />

      <LiveMarketStrip />

      <section className="mx-auto max-w-7xl px-6 pt-6" data-testid="body-type-strip-section">
        <BodyTypeStrip />
      </section>

      <EndingSoonCarousel />

      <HotDaily />

      <section className="mx-auto grid max-w-7xl gap-6 px-6 py-10 lg:grid-cols-3">
        <UpcomingAuctions auctions={auctions} now={now} />
        <WhyUs />
        <PopularCategories />
        <LeadCapture />
      </section>

      <DepositExplainer />

      <BottomStrip />
    </main>
  );
}

/* ==========================================================================
 * 3. Hero
 * ========================================================================== */
function Hero({ onView }) {
  return (
    <section className="relative isolate overflow-hidden" data-testid="hero">
      {/* base gradient */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(circle at 70% 35%, rgba(0,102,255,0.35), transparent 45%), linear-gradient(180deg, #060A14 0%, var(--ar-black) 100%)",
        }}
      />
      {/* network/world map overlay */}
      <div
        className="absolute inset-0 mix-blend-screen opacity-20"
        style={{
          backgroundImage: `url('${HERO_MAP_OVERLAY}')`,
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      />
      {/* right-side car composition */}
      <div
        className="absolute right-0 top-0 h-full w-3/5 bg-cover bg-right-bottom opacity-90"
        style={{ backgroundImage: `url('${HERO_IMG}')` }}
      />
      {/* fade-from-left so text stays readable */}
      <div className="absolute inset-0 bg-gradient-to-r from-[var(--ar-black)] via-[var(--ar-black)]/85 to-[var(--ar-black)]/10" />

      <div className="relative mx-auto max-w-7xl px-6 py-24 lg:py-32">
        <div className="max-w-2xl">
          <h1 className="text-3xl font-black leading-[1.05] tracking-tight md:text-4xl lg:text-5xl">
            Автомобили <br />
            <span className="text-white">со всего мира</span>
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-gray-300 md:text-xl">
            Аукционные, повреждённые и целые автомобили из Новой Зеландии
            и Австралии под заказ.
          </p>

          <div className="mt-8 grid max-w-xl grid-cols-2 gap-x-6 gap-y-4 text-sm text-gray-300 sm:grid-cols-4">
            {TRUST.map(({ icon: Icon, label }) => (
              <div key={label} className="flex items-start gap-2.5">
                <Icon className="mt-0.5 h-5 w-5 shrink-0 text-blue-500" />
                <span className="leading-tight">{label}</span>
              </div>
            ))}
          </div>

          <div className="mt-10 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={onView}
              className="group inline-flex items-center gap-2 rounded-2xl bg-blue-600 px-7 py-4 font-bold text-white shadow-lg shadow-blue-600/30 transition hover:bg-blue-500"
              data-testid="hero-cta-view"
            >
              Смотреть автомобили
              <ArrowRight size={18} className="transition group-hover:translate-x-0.5" />
            </button>
            <Link
              to="/auto/fees"
              className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-7 py-4 font-bold transition hover:bg-white/10"
              data-testid="hero-cta-how"
            >
              Как это работает
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ==========================================================================
 * 4. Search panel — glassmorphism
 * ========================================================================== */
function SearchPanel({ total, onSubmit }) {
  const [tab, setTab] = useState("all");
  const [make, setMake] = useState("");
  const [model, setModel] = useState("");
  const [makes, setMakes] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    autoApi.get("/makes").then((r) => setMakes(r.data?.items || [])).catch(() => {});
  }, []);

  const models = useMemo(() => {
    if (!make) return [];
    return (makes.find((m) => m.make === make)?.models || []);
  }, [makes, make]);

  const handleSubmit = () => {
    const params = new URLSearchParams();
    if (make) params.set("make", make);
    if (model) params.set("model", model);
    if (tab === "damaged") {
      navigate(`/auto/damaged?${params.toString()}`);
    } else if (tab === "buynow") {
      navigate(`/auto/buynow?${params.toString()}`);
    } else {
      navigate(`/auto/catalog?${params.toString()}`);
    }
    onSubmit?.();
  };

  return (
    <section className="mx-auto -mt-12 max-w-7xl px-6">
      <div
        className="relative z-10 rounded-3xl border border-white/10 bg-[var(--ar-card)]/85 p-5 shadow-[0_28px_60px_-20px_rgba(0,102,255,0.25)] backdrop-blur-xl md:p-6"
        data-testid="search-panel"
      >
        <div className="mb-4 flex flex-wrap gap-2">
          <SearchTab id="all"     icon={Car}          label="Все автомобили" active={tab === "all"}     onClick={() => setTab("all")}     />
          <SearchTab id="damaged" icon={Wrench}       label="Повреждённые"   active={tab === "damaged"} onClick={() => setTab("damaged")} />
          <SearchTab id="buynow"  icon={CalendarDays} label="Купить сейчас"  active={tab === "buynow"} onClick={() => setTab("buynow")}  />
        </div>

        <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-6">
          <SelectMake label="Марка" value={make} onChange={(v) => { setMake(v); setModel(""); }} options={makes} />
          <SelectModel label="Модель" value={model} onChange={setModel} options={models} disabled={!make} />
          <SelectStatic label="Год от"     value="2010"           />
          <SelectStatic label="Год до"     value="2024"           />
          <SelectStatic label="Цена от"    value="₽ 0"            />
          <SelectStatic label="Цена до"    value="₽ 6 000 000+"   />
        </div>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <button
            type="button"
            onClick={handleSubmit}
            className="inline-flex items-center gap-2 rounded-2xl bg-blue-600 px-7 py-3 font-bold transition hover:bg-blue-500"
            data-testid="search-submit"
          >
            <Search size={18} />
            Найти ({(total || 0).toLocaleString("ru-RU")})
          </button>
          <Link
            to="/auto/catalog"
            className="inline-flex items-center gap-2 text-sm text-gray-300 transition hover:text-white"
            data-testid="advanced-search"
          >
            <SlidersHorizontal size={16} className="text-blue-500" />
            Расширенный поиск
          </Link>
        </div>
      </div>
    </section>
  );
}

function SelectMake({ label, value, onChange, options }) {
  return (
    <label className="rounded-xl bg-[#070A12] px-4 py-3 ring-1 ring-white/5 block cursor-pointer">
      <div className="text-[11px] uppercase tracking-[0.18em] text-gray-500">{label}</div>
      <select
        className="mt-1 w-full bg-transparent font-semibold text-white outline-none"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        data-testid="search-make"
      >
        <option value="" style={{ background: "#070A12" }}>Любая марка</option>
        {options.map((m) => (
          <option key={m.make} value={m.make} style={{ background: "#070A12" }}>{m.make} ({m.count})</option>
        ))}
      </select>
    </label>
  );
}

function SelectModel({ label, value, onChange, options, disabled }) {
  return (
    <label className={`rounded-xl bg-[#070A12] px-4 py-3 ring-1 ring-white/5 block ${disabled ? "opacity-60" : "cursor-pointer"}`}>
      <div className="text-[11px] uppercase tracking-[0.18em] text-gray-500">{label}</div>
      <select
        className="mt-1 w-full bg-transparent font-semibold text-white outline-none disabled:cursor-not-allowed"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        data-testid="search-model"
      >
        <option value="" style={{ background: "#070A12" }}>
          {disabled ? "Сначала марку" : "Любая модель"}
        </option>
        {options.map((m) => (
          <option key={m.model} value={m.model} style={{ background: "#070A12" }}>{m.model} ({m.count})</option>
        ))}
      </select>
    </label>
  );
}

function SearchTab({ id, icon: Icon, label, active, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={`search-tab-${id}`}
      className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm transition ${
        active
          ? "bg-blue-600 text-white shadow-md shadow-blue-600/30"
          : "bg-white/5 text-gray-300 hover:bg-white/10"
      }`}
    >
      <Icon size={15} />
      {label}
    </button>
  );
}

function SelectStatic({ label, value }) {
  return (
    <div className="rounded-xl bg-[#070A12] px-4 py-3 ring-1 ring-white/5">
      <div className="text-[11px] uppercase tracking-[0.18em] text-gray-500">{label}</div>
      <div className="mt-1 font-semibold text-white">{value}</div>
    </div>
  );
}

/* ==========================================================================
 * 5. Upcoming auctions
 * ========================================================================== */
function UpcomingAuctions({ auctions, now }) {
  return (
    <div
      className="rounded-2xl border border-white/10 bg-[var(--ar-card)] p-5 lg:col-span-2"
      data-testid="upcoming-auctions"
    >
      <div className="mb-5 flex items-center justify-between">
        <h2 className="text-2xl font-bold">Ближайшие аукционы</h2>
        <Link to="/auto/auctions" className="inline-flex items-center gap-1 text-sm font-semibold text-blue-400 hover:text-blue-300" data-testid="see-calendar">
          Смотреть календарь <ChevronRight size={14} />
        </Link>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {auctions.map((a, i) => (
          <AuctionCard key={`${a.city}-${i}`} a={a} now={now} i={i} />
        ))}
      </div>
    </div>
  );
}

function AuctionCard({ a, now, i }) {
  const tone = a.badgeTone === "green"
    ? "bg-emerald-500 text-emerald-950"
    : "bg-amber-500 text-amber-950";
  return (
    <div
      className="group overflow-hidden rounded-xl border border-white/10 bg-[#0B0F17] transition hover:-translate-y-0.5 hover:border-blue-500/40 hover:shadow-[0_18px_36px_-12px_rgba(0,102,255,0.35)]"
      data-testid={`auction-card-${i}`}
    >
      {/* photo with badge + countdown */}
      <div className="relative h-32 w-full overflow-hidden">
        <img
          src={a.img || AUCTION_IMAGES[i % AUCTION_IMAGES.length]}
          alt={a.city}
          className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
          loading="lazy"
          onError={(ev) => {
            ev.currentTarget.onerror = null;
            ev.currentTarget.src = AUCTION_IMAGES[i % AUCTION_IMAGES.length];
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/10 via-transparent to-black/70" />
        <span className={`absolute left-3 top-3 inline-block rounded-md px-2 py-0.5 text-[11px] font-bold ${tone}`}>
          {a.badge}
        </span>
        <div className="absolute right-3 top-3 rounded-md bg-black/55 px-2 py-1 font-mono text-[12px] font-bold text-white backdrop-blur-sm">
          {fmtCountdown(a.starts_at, now)}
        </div>
      </div>

      <div className="p-4">
        <div className="flex items-center gap-1.5 text-lg font-bold leading-tight">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--ar-blue)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
            <circle cx="12" cy="10" r="3"/>
          </svg>
          {a.city}
        </div>
        <div className="mt-0.5 text-xs text-gray-400">{a.source}</div>
        <div className="mt-2 text-sm text-gray-300">{(a.lots || 0).toLocaleString("ru-RU")} лотов</div>
        <Link
          to="/auto/auctions"
          className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-blue-400 transition hover:text-blue-300"
          data-testid={`auction-card-${i}-link`}
        >
          Смотреть лоты <ChevronRight size={14} />
        </Link>
      </div>
    </div>
  );
}

/* ==========================================================================
 * 6. Why us
 * ========================================================================== */
function WhyUs() {
  return (
    <div className="rounded-2xl border border-white/10 bg-[var(--ar-card)] p-5" data-testid="why-us">
      <h2 className="mb-5 text-2xl font-bold">Почему выбирают нас</h2>
      <div className="grid grid-cols-2 gap-4">
        {STATS.map(({ icon: Icon, number, text }) => (
          <div key={text} className="rounded-xl bg-white/[0.03] p-4 ring-1 ring-white/5">
            <Icon className="mb-3 h-7 w-7 text-blue-500" />
            <div className="text-2xl font-black text-blue-500">{number}</div>
            <div className="text-xs leading-snug text-gray-400">{text}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ==========================================================================
 * 7. Popular categories
 * ========================================================================== */
function PopularCategories() {
  return (
    <div className="lg:col-span-2" data-testid="popular-categories">
      <h2 className="mb-5 text-2xl font-bold">Популярные категории</h2>
      <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
        {CATEGORIES.map((c, i) => (
          <Link
            key={c.key}
            to={c.to}
            className="group block overflow-hidden rounded-2xl border border-white/10 bg-[var(--ar-card)] transition hover:-translate-y-0.5 hover:border-blue-500/50"
            data-testid={`category-${c.key}`}
          >
            <div className="p-4">
              <div className="text-sm font-bold leading-tight">{c.title}</div>
              <div className="mt-1 text-xs text-gray-400">
                {c.count.toLocaleString("ru-RU")} авто
              </div>
            </div>
            <div className="relative h-24 w-full">
              <img
                src={c.img}
                alt={c.title}
                loading="lazy"
                className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-[var(--ar-card)] via-[var(--ar-card)]/40 to-transparent" />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

/* ==========================================================================
 * 8. Lead capture
 * ========================================================================== */
function LeadCapture() {
  return (
    <div
      className="relative overflow-hidden rounded-2xl border border-white/10 p-6"
      style={{ background: "linear-gradient(135deg, var(--ar-card) 0%, rgba(6,44,117,0.5) 100%)" }}
      data-testid="lead-capture"
    >
      <div
        className="absolute right-0 top-0 h-full w-2/5 bg-cover bg-right opacity-30"
        style={{ backgroundImage: `url('${LEAD_CAR_SILHOUETTE}')` }}
      />
      <div className="absolute inset-0 bg-gradient-to-r from-[var(--ar-card)] via-[var(--ar-card)]/70 to-transparent" />
      <div className="relative">
        <h2 className="text-2xl font-bold leading-tight">Хотите найти конкретный автомобиль?</h2>
        <p className="mt-3 max-w-md text-gray-300">
          Оставьте заявку, и мы найдём автомобиль под ваши требования.
        </p>
        <Link
          to="/auto/fees"
          className="mt-6 inline-flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3 font-bold transition hover:bg-blue-500"
          data-testid="lead-cta"
        >
          Оставить заявку
          <ArrowRight size={16} />
        </Link>
      </div>
    </div>
  );
}

/* ==========================================================================
 * 9. Bottom feature strip
 * ========================================================================== */
function BottomStrip() {
  return (
    <section className="mx-auto grid max-w-7xl gap-4 px-6 pb-12 md:grid-cols-2 lg:grid-cols-4" data-testid="bottom-features">
      {BOTTOM_FEATURES.map(({ icon: Icon, title, text }) => (
        <div key={title} className="flex items-center gap-4 rounded-2xl border border-white/10 bg-[var(--ar-card)] p-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-blue-500/10 ring-1 ring-blue-500/20">
            <Icon className="h-6 w-6 text-blue-400" />
          </div>
          <div>
            <div className="font-bold leading-tight">{title}</div>
            <div className="mt-0.5 text-xs text-gray-400">{text}</div>
          </div>
        </div>
      ))}
    </section>
  );
}

/* ==========================================================================
 * Hot Daily — late-model, low-km, popular makes from AUCTIONS only.
 * Driven by GET /api/auto/hot-daily — server-side selection logic.
 * ========================================================================== */
function HotDaily() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const r = await autoApi.get("/hot-daily?limit=8");
        setItems(r.data?.items || []);
      } catch {
        setItems([]);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (!loading && items.length === 0) return null;

  return (
    <section className="mx-auto max-w-7xl px-6 pt-10" data-testid="hot-daily">
      <div className="mb-4 flex items-end justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-amber-300">
            <span>🔥</span> Хиты дня
          </div>
          <h2 className="mt-2 text-2xl font-bold lg:text-3xl">
            Лучший выбор сегодня
          </h2>
        </div>
        <Link
          to="/auto/catalog"
          className="hidden text-sm font-semibold text-blue-400 hover:text-blue-300 sm:inline"
          data-testid="hot-daily-see-all"
        >
          Весь каталог →
        </Link>
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="h-72 animate-pulse rounded-2xl border border-white/10 bg-[var(--ar-card)]" />
          ))}
        </div>
      ) : (
        <div className={`grid gap-4 ${items.length === 1 ? "sm:grid-cols-1 sm:max-w-2xl" : "sm:grid-cols-2"}`}>
          {items.map((v) => (
            <HotCard key={v.id} v={v} />
          ))}
        </div>
      )}
    </section>
  );
}

function HotCard({ v }) {
  const cover = (v.local_images?.[0] || v.images?.[0] || v.source_images?.[0]) || null;
  const initials = `${(v.make || "").slice(0, 1)}${(v.model || "").slice(0, 1)}`.toUpperCase() || "AR";
  return (
    <Link
      to={`/auto/vehicle/${v.id}`}
      className="group block overflow-hidden rounded-2xl border border-white/10 bg-[var(--ar-card)] transition hover:-translate-y-0.5 hover:border-blue-500/60"
      data-testid={`hot-card-${v.id}`}
    >
      <div className="relative aspect-[4/3] w-full overflow-hidden">
        {cover ? (
          <img src={cover} alt={v.title_ru} loading="lazy"
               className="h-full w-full object-cover transition duration-500 group-hover:scale-105" />
        ) : (
          <div
            className="flex h-full w-full items-center justify-center"
            style={{
              background:
                "radial-gradient(circle at 30% 30%, rgba(0,102,255,0.35), transparent 60%), linear-gradient(135deg, #0B1424 0%, var(--ar-black) 100%)",
            }}
          >
            <span className="font-black text-blue-500/70 text-5xl tracking-tight">{initials}</span>
          </div>
        )}
        <span className="absolute left-3 top-3 inline-block rounded-md bg-amber-500 px-2 py-0.5 text-[11px] font-bold text-amber-950">
          🔥 {v.pick_label || "ХИТ"}
        </span>
        {v.country && (
          <span className="absolute right-3 top-3 inline-block rounded-md bg-black/55 px-2 py-0.5 text-[11px] font-bold text-white backdrop-blur-sm">
            {v.country}
          </span>
        )}
        <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
      </div>
      <div className="p-4">
        <div className="line-clamp-1 font-bold leading-tight">{v.title_ru || `${v.year || ""} ${v.make || ""} ${v.model || ""}`.trim()}</div>
        <div className="mt-1 text-xs text-gray-400">
          {v.year ? `${v.year} · ` : ""}
          {v.mileage_km != null ? `${Number(v.mileage_km).toLocaleString("ru-RU")} км` : "—"}
          {v.location ? ` · ${v.location}` : ""}
        </div>
        <div className="mt-3 flex items-end justify-between">
          <div>
            <div className="text-[10px] uppercase tracking-wider text-gray-500">Цена · с аукциона</div>
            <div className="font-mono text-base font-bold text-white">
              {v.current_price_nzd ? formatRub(v.current_price_nzd) : <span className="text-gray-400">По запросу</span>}
            </div>
          </div>
          <span className="text-xs font-semibold text-blue-400 transition group-hover:text-blue-300">
            Смотреть →
          </span>
        </div>
      </div>
    </Link>
  );
}
