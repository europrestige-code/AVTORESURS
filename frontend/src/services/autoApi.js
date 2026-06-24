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
  return config;
});

export default autoApi;
