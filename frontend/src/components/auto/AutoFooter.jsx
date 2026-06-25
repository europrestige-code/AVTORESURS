import React from "react";
import { Link } from "react-router-dom";
import { Phone, Mail, MapPin, MessageCircle, Send, Instagram, Facebook } from "lucide-react";

const NAV_COLS = [
  {
    title: "Покупка",
    links: [
      { to: "/auto/catalog",     label: "Каталог авто" },
      { to: "/auto/auctions",    label: "Календарь аукционов" },
      { to: "/auto/damaged",     label: "Повреждённые" },
      { to: "/auto/buynow",      label: "Купить сейчас" },
      { to: "/auto/end-of-life", label: "Списанные авто" },
    ],
  },
  {
    title: "Услуги",
    links: [
      { to: "/auto/fees",  label: "Инспекция и документы" },
      { to: "/auto/fees",  label: "Транспорт по НЗ" },
      { to: "/auto/fees",  label: "Морской фрахт" },
      { to: "/auto/fees",  label: "Растаможка РФ" },
      { to: "/auto/fees",  label: "Доставка под ключ" },
    ],
  },
  {
    title: "Компания",
    links: [
      { to: "/auto/terms", label: "О компании" },
      { to: "/auto/fees",  label: "Как это работает" },
      { to: "/auto/terms", label: "Условия" },
      { to: "/auto/terms", label: "Политика конфиденциальности" },
    ],
  },
];

export default function AutoFooter() {
  return (
    <footer className="mt-16 border-t border-white/10 bg-[var(--ar-black)]" data-testid="auto-footer">
      <div className="mx-auto grid max-w-7xl gap-10 px-6 py-12 lg:grid-cols-5">
        {/* Brand + contacts */}
        <div className="lg:col-span-2">
          <Link to="/auto" className="inline-block" data-testid="footer-brand">
            <img
              src="/branding/avtoresurs-lockup.png?v=3"
              alt="АвтоРесурс — автомобили со всего мира"
              className="h-20 w-auto select-none"
              draggable="false"
            />
          </Link>
          <p className="mt-4 max-w-sm text-sm text-gray-400">
            Покупаем авто на аукционах Новой Зеландии и Австралии, инспектируем,
            оформляем документы и доставляем под ключ до Владивостока и далее.
          </p>
          <div className="mt-5 space-y-2 text-sm text-gray-300">
            <a className="flex items-center gap-2 hover:text-white" href="tel:+6421425233">
              <Phone size={14} className="text-blue-400" /> +64 21 425 233 (NZ)
            </a>
            <a className="flex items-center gap-2 hover:text-white" href="tel:+79135121934">
              <Phone size={14} className="text-blue-400" /> +7 913 512 1934 (RU)
            </a>
            <a className="flex items-center gap-2 hover:text-white" href="mailto:europrestige@gmail.com">
              <Mail size={14} className="text-blue-400" /> europrestige@gmail.com
            </a>
            <div className="flex items-center gap-2">
              <MapPin size={14} className="text-blue-400" /> Auckland, New Zealand
            </div>
          </div>
          {/* Social */}
          <div className="mt-5 flex items-center gap-2">
            <Social href="https://wa.me/6421425233" Icon={MessageCircle} title="WhatsApp" tint="#25D366" testid="social-wa" />
            <Social href="https://t.me/avtoresurs" Icon={Send} title="Telegram" tint="#229ED9" testid="social-tg" />
            <Social href="#" Icon={Instagram} title="Instagram" tint="#E1306C" testid="social-ig" />
            <Social href="#" Icon={Facebook} title="Facebook" tint="#1877F2" testid="social-fb" />
          </div>
        </div>

        {/* Nav columns */}
        {NAV_COLS.map((col) => (
          <div key={col.title}>
            <div className="mb-3 text-xs uppercase tracking-[0.2em] text-gray-500">
              {col.title}
            </div>
            <ul className="space-y-2 text-sm">
              {col.links.map((l) => (
                <li key={l.label}>
                  <Link to={l.to} className="text-gray-300 transition hover:text-white">
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="border-t border-white/5">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-6 py-5 text-xs text-gray-500">
          <div>© {new Date().getFullYear()} АвтоРесурс · BuyAnywhere. Все права защищены.</div>
          <div className="flex items-center gap-4">
            <Link to="/auto/terms" className="hover:text-white">Условия</Link>
            <Link to="/auto/terms" className="hover:text-white">Конфиденциальность</Link>
            <Link to="/auto/terms" className="hover:text-white">Cookies</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}

function Social({ href, Icon, title, tint, testid }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      title={title}
      data-testid={testid}
      className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-white/5 transition hover:bg-white/10"
    >
      <Icon size={15} style={{ color: tint }} />
    </a>
  );
}
