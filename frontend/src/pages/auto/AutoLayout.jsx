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
  { to: "/auto/auctions",                   label: "Календарь" },
  { to: "/auto/damaged",                    label: "Повреждённые" },
  { to: "/auto/end-of-life",                label: "End of Life" },
  { to: "/auto/buynow",                     label: "Купить сейчас" },
  { to: "/auto/fees",                       label: "Услуги" },
  { to: "/auto/terms",                      label: "О компании" },
];

export default function AutoLayout() {
  const { isAuthenticated, user, logout } = useAuth();
  return (
    <div className="auto-root min-h-screen bg-[var(--ar-black)] text-white" data-testid="auto-root">
      {/* Sliding contact marquee — sticky, full-width, opaque dark bg.
       *  Sits ABOVE the main brand+nav header so the AR lockup is never
       *  overlapped or visually affected. */}
      <div className="sticky top-0 z-[60]">
        <ContactsBar variant="header" />
      </div>

      {/* Sticky main header — sits below the contact marquee. */}
      <header className="sticky top-[28px] z-40 border-b border-white/10 bg-[var(--ar-black)]">
        <div className="mx-auto flex max-w-[1600px] items-end justify-between gap-4 px-5 py-2 xl:gap-6 xl:px-6">
          <NavLink to="/auto" end className="flex items-center shrink-0" data-testid="auto-brand">
            <img
              src="/branding/avtoresurs-lockup.png?v=3"
              alt="АвтоРесурс — автомобили со всего мира"
              className="h-[52px] w-auto select-none lg:h-[60px]"
              style={{ minWidth: 200 }}
              draggable="false"
            />
          </NavLink>

          <nav className="hidden items-center gap-2.5 text-[13px] text-gray-300 xl:flex xl:gap-4" aria-label="Главная навигация">
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

          <div className="flex shrink-0 items-center gap-2">
            {isAuthenticated ? (
              <>
                <NavLink to="/auto/my/searches" className="inline-flex items-center justify-center rounded-xl border border-white/10 bg-white/5 px-3 h-11 text-[13px] hover:bg-white/10" data-testid="nav-my-searches">
                  Подписки
                </NavLink>
                <NavLink to="/auto/dashboard" className="inline-flex items-center justify-center rounded-xl border border-white/10 bg-white/5 px-3 h-11 text-[13px] hover:bg-white/10" data-testid="nav-dashboard">
                  Кабинет
                </NavLink>
                {user?.role === "admin" && (
                  <NavLink to="/auto/admin" className="inline-flex items-center justify-center rounded-xl bg-blue-600 px-4 h-11 text-[13px] font-semibold text-white hover:bg-blue-500" data-testid="nav-admin">
                    Админ
                  </NavLink>
                )}
                <button onClick={logout} className="inline-flex items-center justify-center rounded-xl border border-white/10 bg-white/5 px-3 h-11 text-[13px] hover:bg-white/10" data-testid="nav-logout">
                  Выйти
                </button>
              </>
            ) : (
              <>
                <NavLink to="/" className="inline-flex items-center justify-center rounded-xl border border-white/10 bg-white/5 px-4 h-11 text-[13px] font-medium hover:bg-white/10 transition whitespace-nowrap" data-testid="nav-login">
                  <User className="mr-1.5 h-4 w-4" />
                  Войти
                </NavLink>
                <NavLink to="/" className="inline-flex items-center justify-center rounded-xl bg-blue-600 px-4 h-11 text-[13px] font-semibold text-white hover:bg-blue-500 transition whitespace-nowrap" data-testid="nav-register">
                  Регистрация
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
