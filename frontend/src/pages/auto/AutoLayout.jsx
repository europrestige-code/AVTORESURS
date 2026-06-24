import React from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import "./auto.css";

const NAV = [
  { to: "/auto", label: "Главная", end: true },
  { to: "/auto/catalog", label: "Каталог" },
  { to: "/auto/how-it-works", label: "Как это работает" },
  { to: "/auto/fees", label: "Стоимость" },
  { to: "/auto/australia", label: "Австралия" },
];

export default function AutoLayout() {
  const { isAuthenticated, user, logout } = useAuth();
  const location = useLocation();
  return (
    <div className="auto-root" data-testid="auto-root">
      <div className="auto-container">
        <div className="auto-nav" data-testid="auto-nav">
          <div style={{ display: "flex", alignItems: "center", gap: 24, flex: 1 }}>
            <NavLink to="/auto" end style={{ textDecoration: "none" }} data-testid="auto-brand">
              <div style={{ fontWeight: 800, fontSize: 18, letterSpacing: "-0.01em" }}>
                BuyAnywhere <span style={{ color: "var(--auto-primary)" }}>Auto</span>
              </div>
            </NavLink>
            <div style={{ display: "flex", gap: 18, flexWrap: "wrap" }}>
              {NAV.map((n) => (
                <NavLink
                  key={n.to}
                  to={n.to}
                  end={n.end}
                  className={({ isActive }) => (isActive ? "active" : "")}
                  data-testid={`auto-nav-link-${n.to.replace(/\//g, "-")}`}
                >
                  {n.label}
                </NavLink>
              ))}
            </div>
          </div>
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            {isAuthenticated ? (
              <>
                <NavLink
                  to="/auto/dashboard"
                  className="auto-btn auto-btn-outline"
                  data-testid="auto-link-dashboard"
                >
                  Мой кабинет
                </NavLink>
                {user?.role === "admin" && (
                  <NavLink to="/auto/admin" className="auto-btn" data-testid="auto-link-admin">
                    Админ
                  </NavLink>
                )}
                <button onClick={logout} className="auto-btn auto-btn-outline" data-testid="auto-logout-btn">
                  Выйти
                </button>
              </>
            ) : (
              <NavLink to="/" className="auto-btn auto-btn-outline" data-testid="auto-login-link">
                Войти
              </NavLink>
            )}
          </div>
        </div>
        <Outlet />
      </div>
      <div className="auto-container" style={{ marginTop: 60, paddingBottom: 32, color: "var(--auto-muted)", fontSize: 13 }}>
        <div className="auto-divider" />
        BuyAnywhere Auto · {new Date().getFullYear()} · {location.pathname}
      </div>
    </div>
  );
}
