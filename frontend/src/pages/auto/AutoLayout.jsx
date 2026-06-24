import React from "react";
import { NavLink, Outlet } from "react-router-dom";
import { User } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import QuickCategoryStrip from "../../components/auto/QuickCategoryStrip";
import ChatWidget from "../../components/auto/ChatWidget";
import ContactsBar from "../../components/auto/ContactsBar";
import AutoFooter from "../../components/auto/AutoFooter";
import "./auto.css";

const NAV = [
  { to: "/auto",                end: true,  label: "Главная" },
  { to: "/auto/catalog",                    label: "Каталог" },
  { to: "/auto/auctions",                   label: "Календарь аукционов" },
  { to: "/auto/damaged",                    label: "Повреждённые" },
  { to: "/auto/end-of-life",                label: "Списанные авто" },
  { to: "/auto/buynow",                     label: "Купить сейчас" },
  { to: "/auto/fees",                       label: "Услуги" },
  { to: "/auto/terms",                      label: "О компании" },
];

export default function AutoLayout() {
  const { isAuthenticated, user, logout } = useAuth();
  return (
    <div className="auto-root min-h-screen bg-[#05070B] text-white" data-testid="auto-root">
      {/* Top contact bar */}
      <div className="border-b border-white/5 bg-[#05070B]">
        <div className="mx-auto flex max-w-7xl items-center justify-end gap-4 px-6 py-1.5 text-xs">
          <ContactsBar variant="header" />
        </div>
      </div>

      {/* Sticky main header */}
      <header className="sticky top-0 z-40 border-b border-white/10 bg-[#05070B]/85 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-6 py-4">
          <NavLink to="/auto" end className="flex items-center gap-4" data-testid="auto-brand">
            <img
              src="/branding/avtoresurs-mark.png"
              alt="АвтоРесурс"
              className="h-[120px] w-[140px] rounded-xl object-cover bg-blue-600"
            />
            <div>
              <div className="text-lg font-black italic tracking-wide leading-none">
                <span className="text-white">АВТО</span>
                <span className="text-blue-500">РЕСУРС</span>
              </div>
              <div className="mt-1 text-[10px] uppercase tracking-[0.25em] text-gray-400">
                автомобили со всего мира
              </div>
            </div>
          </NavLink>

          <nav className="hidden items-center gap-6 text-sm text-gray-300 lg:flex" aria-label="Главная навигация">
            {NAV.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.end}
                className={({ isActive }) =>
                  `pb-2 border-b-2 transition ${isActive ? "border-blue-500 text-white" : "border-transparent hover:text-white"}`
                }
                data-testid={`nav-${n.to.replace(/\//g, "-")}`}
              >
                {n.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            {isAuthenticated ? (
              <>
                <NavLink to="/auto/dashboard" className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm hover:bg-white/10" data-testid="nav-dashboard">
                  Мой кабинет
                </NavLink>
                {user?.role === "admin" && (
                  <NavLink to="/auto/admin" className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500" data-testid="nav-admin">
                    Админ
                  </NavLink>
                )}
                <button onClick={logout} className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm hover:bg-white/10" data-testid="nav-logout">
                  Выйти
                </button>
              </>
            ) : (
              <>
                <NavLink to="/" className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm hover:bg-white/10" data-testid="nav-login">
                  <User className="mr-2 inline h-4 w-4" />
                  Войти
                </NavLink>
                <NavLink to="/" className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500" data-testid="nav-register">
                  Зарегистрироваться
                </NavLink>
              </>
            )}
          </div>
        </div>
        {/* Quick category strip just under main nav */}
        <div className="mx-auto max-w-7xl px-3">
          <QuickCategoryStrip />
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 lg:px-6">
        <Outlet />
      </main>

      <AutoFooter />

      {/* Floating AI chat */}
      <ChatWidget />
    </div>
  );
}
