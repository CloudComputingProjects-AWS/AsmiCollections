/**
 * Axios API Client — Auto-handles JWT refresh, 401 retries, error normalization.
 * Backend uses httpOnly cookies, so tokens are sent automatically.
 */
import axios from 'axios';

const API_BASE = '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,          // send httpOnly cookies
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

// ── Request interceptor ──
api.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
);

// ── Response interceptor: auto-refresh on 401 ──
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error);
    else prom.resolve();
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Skip refresh for auth endpoints
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url.includes('/auth/login') &&
      !originalRequest.url.includes('/auth/refresh')
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(() => api(originalRequest));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        await axios.post(`${API_BASE}/auth/refresh`, {}, { withCredentials: true });
        processQueue(null);
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError);
        // Auth store will handle redirect to login
        window.dispatchEvent(new CustomEvent('auth:session-expired'));
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(normalizeError(error));
  }
);

// ── Error normalizer ──
function normalizeError(error) {
  if (error.response) {
    const data = error.response.data;
    return {
      status: error.response.status,
      message: data?.detail || data?.message || 'Something went wrong',
      errors: data?.errors || null,
    };
  }
  if (error.request) {
    return { status: 0, message: 'Network error — check your connection', errors: null };
  }
  return { status: 0, message: error.message, errors: null };
}

export default api;
