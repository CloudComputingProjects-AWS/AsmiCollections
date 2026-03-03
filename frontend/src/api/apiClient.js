/**
 * apiClient.js — Axios HTTP Client
 *
 * SECURITY (Updated 01-Mar-2026 S16): Full httpOnly cookie authentication.
 * - access_token: httpOnly cookie, path="/", sent on ALL requests
 * - refresh_token: httpOnly cookie, path="/api/v1/auth", sent only on auth endpoints
 * - NO tokens in localStorage — zero JS access to any token
 * - Browser sends cookies automatically — no manual handling needed
 *
 * Error handling:
 * - 401 on API calls -> attempt refresh (cookie-based) -> retry original request
 * - 429 (rate limit) -> propagate to caller (do NOT trigger logout)
 * - Auth routes (login/register/refresh/me) -> skip interceptor, bubble up naturally
 */

import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api/v1',             // Goes through Vite proxy -> same origin -> cookies work
  withCredentials: true,           // Send httpOnly cookies with every request
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor — no Authorization header needed (cookie is automatic)
apiClient.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
);

// Response interceptor — handle 401 + token refresh
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error) => {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error);
    else prom.resolve();
  });
  failedQueue = [];
};

// Routes that should NOT trigger the 401 refresh/redirect logic
const AUTH_ROUTES = ['/auth/login', '/auth/register', '/auth/refresh', '/auth/me'];

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const requestUrl = originalRequest?.url || '';
    const status = error.response?.status;

    // SKIP interceptor for auth routes — let errors bubble up naturally
    const isAuthRoute = AUTH_ROUTES.some((route) => requestUrl.includes(route));
    if (isAuthRoute) {
      return Promise.reject(error);
    }

    // 429 = rate limited — do NOT trigger logout, just propagate the error
    if (status === 429) {
      return Promise.reject(error);
    }

    // 401 = unauthorized — try to refresh the access token
    if (status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(() => apiClient(originalRequest));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // POST refresh — browser sends refresh_token httpOnly cookie automatically
        // No request body needed — backend reads token from cookie
        await axios.post(
          '/api/v1/auth/refresh',
          {},
          { withCredentials: true }
        );

        processQueue(null);
        // Retry original request — browser sends new access_token cookie automatically
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError);
        window.dispatchEvent(new CustomEvent('auth:expired'));
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
