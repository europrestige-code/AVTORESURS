import axios from "axios";

const BASE = process.env.REACT_APP_BACKEND_URL;

// Dedicated axios instance for /api/auto. Uses the customer JWT
// stored under `access_token` (set by AuthContext on login).
const autoApi = axios.create({
  baseURL: `${BASE}/api/auto`,
  timeout: 30000,
});

autoApi.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  // Admin endpoints with 2FA enabled require this header. The frontend
  // stores the latest MFA token under `admin_mfa_token` after the OTP
  // exchange — see AdminMfaGate.
  const mfa = localStorage.getItem("admin_mfa_token");
  if (mfa && (config.url || "").startsWith("/admin")) {
    config.headers["X-Admin-MFA-Token"] = mfa;
  }
  return config;
});

export default autoApi;
