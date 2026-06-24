import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_BACKEND_URL || 'https://rumarket.preview.emergentagent.com/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    // Add customer token if available
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add admin token if available (admin routes have priority)
    const adminToken = localStorage.getItem('admin_token');
    if (adminToken && config.url?.includes('/admin/')) {
      config.headers.Authorization = `Bearer ${adminToken}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle 401 errors by removing tokens
    if (error.response?.status === 401) {
      if (error.config.url?.includes('/admin/')) {
        localStorage.removeItem('admin_token');
      } else {
        localStorage.removeItem('token');
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;