import React from "react";
import { NavLink, Outlet } from "react-router-dom";
import { User } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import ChatWidget from "../../components/auto/ChatWidget";
import ContactsBar from "../../components/auto/ContactsBar";
import AutoFooter from "../../components/auto/AutoFooter";
import "./auto.css";

const NAV = [
  { to: "/auto",                end: true,  label: "Главная" },
  { to: "/auto/catalog",                    label: "Каталог" },
  { to: "/auto/auctions",                   label: "Календарь аукционов" },
  { to: "/auto/damaged",                    label: "Повреждённые" },
  { to: "/auto/end-of-life",                label: "End of Life" },
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
        <div className="mx-auto flex max-w-screen-2xl items-center justify-between gap-6 px-6 py-4">
          <NavLink to="/auto" end className="flex items-center" data-testid="auto-brand">
            <img
              src="/branding/avtoresurs-lockup.png?v=3"
              alt="АвтоРесурс — автомобили со всего мира"
              className="h-20 w-auto select-none lg:h-24"
              style={{ minWidth: 320 }}
              draggable="false"
            />
          </NavLink>

          <nav className="hidden items-center gap-3 text-[13px] text-gray-300 lg:flex xl:gap-5" aria-label="Главная навигация">
            {NAV.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.end}
                className={({ isActive }) =>
                  `whitespace-nowrap pb-2 border-b-2 transition ${isActive ? "border-blue-500 text-white" : "border-transparent hover:text-white"}`
                }
                data-testid={`nav-${n.to.replace(/\//g, "-")}`}
              >
                {n.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <>
                <NavLink to="/auto/dashboard" className="inline-flex items-center justify-center rounded-xl border border-white/10 bg-white/5 px-6 h-20 text-sm hover:bg-white/10 lg:h-24" data-testid="nav-dashboard">
                  Мой кабинет
                </NavLink>
                {user?.role === "admin" && (
                  <NavLink to="/auto/admin" className="inline-flex items-center justify-center rounded-xl bg-blue-600 px-6 h-20 text-sm font-semibold text-white hover:bg-blue-500 lg:h-24" data-testid="nav-admin">
                    Админ
                  </NavLink>
                )}
                <button onClick={logout} className="inline-flex items-center justify-center rounded-xl border border-white/10 bg-white/5 px-5 h-20 text-sm hover:bg-white/10 lg:h-24" data-testid="nav-logout">
                  Выйти
                </button>
              </>
            ) : (
              <>
                <NavLink to="/" className="inline-flex items-center justify-center rounded-xl border border-white/10 bg-white/5 px-6 h-20 text-base font-medium hover:bg-white/10 transition whitespace-nowrap lg:h-24" data-testid="nav-login">
                  <User className="mr-2 h-5 w-5" />
                  Войти
                </NavLink>
                <NavLink to="/" className="inline-flex items-center justify-center rounded-xl bg-blue-600 px-6 h-20 text-base font-semibold text-white hover:bg-blue-500 transition whitespace-nowrap lg:h-24" data-testid="nav-register">
                  Зарегистрироваться
                </NavLink>
              </>
            )}
          </div>
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
