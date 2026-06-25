import React, { useCallback, useEffect, useState } from "react";
import { ShieldCheck, ShieldAlert } from "lucide-react";
import autoApi from "../../services/autoApi";

/**
 * Gates the admin panel behind a TOTP prompt when the logged-in admin
 * has 2FA enabled. The actual children (admin tabs) are only rendered
 * after a fresh MFA token is in `localStorage.admin_mfa_token`.
 *
 * - If the admin has 2FA disabled → renders children immediately.
 * - If enabled and no valid token → renders a 6-digit code form.
 * - Token lifetime is server-enforced (1h); we don't track expiry here
 *   because the autoApi interceptor will simply 401 and the gate remounts.
 */
export default function AdminMfaGate({ children }) {
  const [status, setStatus] = useState(null);
  const [needsCode, setNeedsCode] = useState(false);
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const checkGate = useCallback(async () => {
    try {
      const r = await autoApi.get("/admin/2fa/status");
      setStatus(r.data);
      if (!r.data.enabled) {
        setNeedsCode(false);
        return;
      }
      // Try a cheap admin endpoint with the cached token — if it 200s we're in.
      try {
        await autoApi.get("/admin/clients?limit=1");
        setNeedsCode(false);
      } catch (err) {
        if (err.response?.status === 401) setNeedsCode(true);
      }
    } catch {
      // Status endpoint requires admin auth; treat any failure as «open».
      setStatus({ enabled: false });
    }
  }, []);

  useEffect(() => { checkGate(); }, [checkGate]);

  const submit = async (e) => {
    e?.preventDefault?.();
    if (busy || code.length < 6) return;
    setBusy(true);
    setError(null);
    try {
      const r = await autoApi.post("/admin/2fa/login", { code });
      localStorage.setItem("admin_mfa_token", r.data.mfa_token);
      setNeedsCode(false);
      setCode("");
    } catch (err) {
      setError(err.response?.data?.detail || "Неверный код. Попробуйте ещё раз.");
    } finally {
      setBusy(false);
    }
  };

  if (!status) return <div className="auto-section auto-muted">Проверяем 2FA…</div>;

  if (needsCode) {
    return (
      <div className="auto-section" data-testid="admin-mfa-gate">
        <div className="admin-mfa-card auto-card">
          <ShieldAlert size={22} className="text-blue-400" />
          <div style={{ fontSize: 18, fontWeight: 700, marginTop: 8 }}>
            Двухфакторная аутентификация
          </div>
          <div className="auto-muted" style={{ marginBottom: 14, fontSize: 13 }}>
            Введите 6-значный код из приложения-аутентификатора (Google
            Authenticator, Authy, 1Password) для входа в админ-панель.
          </div>
          <form onSubmit={submit} style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input
              className="auto-input"
              inputMode="numeric"
              maxLength={6}
              autoFocus
              placeholder="123 456"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
              data-testid="admin-mfa-code-input"
              style={{ letterSpacing: "0.18em", fontSize: 18, textAlign: "center", width: 160 }}
            />
            <button
              type="submit"
              className="auto-btn"
              disabled={busy || code.length < 6}
              data-testid="admin-mfa-submit"
            >
              {busy ? "Проверяем…" : "Войти"}
            </button>
          </form>
          {error && (
            <div className="auto-muted" style={{ color: "var(--ar-danger)", marginTop: 8 }} data-testid="admin-mfa-error">
              {error}
            </div>
          )}
        </div>
      </div>
    );
  }

  return children;
}

export function Admin2FASection() {
  const [status, setStatus] = useState(null);
  const [setupData, setSetupData] = useState(null);
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const load = useCallback(async () => {
    try {
      const r = await autoApi.get("/admin/2fa/status");
      setStatus(r.data);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { load(); }, [load]);

  const startSetup = async () => {
    setBusy(true);
    setError(null);
    try {
      const r = await autoApi.post("/admin/2fa/setup");
      setSetupData(r.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Не удалось запустить настройку.");
    } finally {
      setBusy(false);
    }
  };

  const verifySetup = async () => {
    if (code.length < 6) return;
    setBusy(true); setError(null);
    try {
      const r = await autoApi.post("/admin/2fa/verify-setup", { code });
      if (r.data?.mfa_token) localStorage.setItem("admin_mfa_token", r.data.mfa_token);
      setSuccess("2FA включена. Используйте код при следующем входе в админ-панель.");
      setSetupData(null);
      setCode("");
      load();
    } catch (e) {
      setError(e.response?.data?.detail || "Неверный код.");
    } finally { setBusy(false); }
  };

  const disable2fa = async () => {
    const c = window.prompt("Введите текущий 6-значный код, чтобы отключить 2FA:");
    if (!c) return;
    setBusy(true); setError(null);
    try {
      await autoApi.post("/admin/2fa/disable", { code: c });
      localStorage.removeItem("admin_mfa_token");
      setSuccess("2FA отключена.");
      load();
    } catch (e) {
      setError(e.response?.data?.detail || "Не удалось отключить.");
    } finally { setBusy(false); }
  };

  if (!status) return <div className="auto-muted">Загружаем…</div>;

  return (
    <div className="admin-2fa" data-testid="admin-2fa-section">
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <ShieldCheck size={22} className={status.enabled ? "text-emerald-400" : "text-amber-400"} />
        <div>
          <div style={{ fontWeight: 700 }} data-testid="admin-2fa-status">
            {status.enabled ? "2FA включена" : "2FA отключена"}
          </div>
          <div className="auto-muted" style={{ fontSize: 12 }}>
            {status.enabled
              ? "Каждый вход в админ-панель требует 6-значный код из приложения."
              : "Включите 2FA — это рекомендуемая защита для учётной записи администратора."}
          </div>
        </div>
      </div>

      {!status.enabled && !setupData && (
        <button
          type="button"
          className="auto-btn"
          onClick={startSetup}
          disabled={busy}
          data-testid="admin-2fa-start-btn"
          style={{ marginTop: 12 }}
        >
          Включить 2FA
        </button>
      )}

      {setupData && (
        <div className="admin-2fa__setup" data-testid="admin-2fa-setup">
          <ol style={{ paddingLeft: 18, lineHeight: 1.6, margin: "12px 0" }}>
            <li>Откройте Google Authenticator (или Authy, 1Password).</li>
            <li>Отсканируйте QR-код или введите секрет вручную.</li>
            <li>Введите 6-значный код, который покажет приложение.</li>
          </ol>
          {setupData.qr_data_url && (
            <img
              src={setupData.qr_data_url}
              alt="QR-код 2FA"
              className="admin-2fa__qr"
              data-testid="admin-2fa-qr"
            />
          )}
          {setupData.secret && (
            <div className="auto-muted" style={{ fontFamily: "monospace", fontSize: 12, marginTop: 6 }}>
              Секрет: <span data-testid="admin-2fa-secret">{setupData.secret}</span>
            </div>
          )}
          <div style={{ display: "flex", gap: 8, marginTop: 12, alignItems: "center" }}>
            <input
              className="auto-input"
              inputMode="numeric"
              maxLength={6}
              placeholder="6-значный код"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
              data-testid="admin-2fa-verify-input"
              style={{ width: 160 }}
            />
            <button
              type="button"
              className="auto-btn"
              onClick={verifySetup}
              disabled={busy || code.length < 6}
              data-testid="admin-2fa-verify-btn"
            >
              {busy ? "…" : "Подтвердить и включить"}
            </button>
          </div>
        </div>
      )}

      {status.enabled && (
        <button
          type="button"
          className="auto-btn auto-btn--ghost"
          onClick={disable2fa}
          disabled={busy}
          data-testid="admin-2fa-disable-btn"
          style={{ marginTop: 12 }}
        >
          Отключить 2FA
        </button>
      )}

      {error && <div data-testid="admin-2fa-error" style={{ color: "var(--ar-danger)", marginTop: 10 }}>{error}</div>}
      {success && <div data-testid="admin-2fa-success" style={{ color: "var(--ar-success)", marginTop: 10 }}>{success}</div>}
    </div>
  );
}
