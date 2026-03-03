/**
 * authStore.js — Zustand Auth Store
 *
 * SECURITY (Updated 01-Mar-2026 S16): Full httpOnly cookie authentication.
 * - access_token: httpOnly cookie (set by backend, path="/")
 * - refresh_token: httpOnly cookie (set by backend, path="/api/v1/auth")
 * - NO tokens in localStorage — zero JS access to any token
 * - init() calls /auth/me — browser sends cookie automatically
 *
 * Blueprint ref: Phase 1 — "Login with JWT in httpOnly cookies"
 */

import { create } from 'zustand';
import apiClient from '../api/apiClient';

const useAuthStore = create((set, get) => ({
  user: null,
  loading: true,       // true until initial session check completes
  error: null,

  /**
   * Initialize session on app startup (cold page load / F5 refresh).
   * Calls /auth/me — browser automatically sends httpOnly access_token cookie.
   * If cookie is valid -> user is restored.
   * If expired/missing -> user stays null, loading set to false.
   *
   * Handles 429 (rate limit) with retry after delay.
   * Only 401 means "not authenticated".
   */
  init: async () => {
    const fetchMe = async () => {
      const res = await apiClient.get('/auth/me');
      return res.data;
    };

    try {
      const userData = await fetchMe();
      set({ user: userData, loading: false });
    } catch (err) {
      const status = err?.status || err?.response?.status;

      // 429 = rate limited — wait and retry once
      if (status === 429) {
        try {
          await new Promise((r) => setTimeout(r, 1500));
          const userData = await fetchMe();
          set({ user: userData, loading: false });
          return;
        } catch {
          // Retry failed — treat as unauthenticated
        }
      }

      // 401 or any other failure — not authenticated
      set({ user: null, loading: false });
    }
  },

  /**
   * Login — POST credentials, backend sets httpOnly access_token + refresh_token cookies.
   * No tokens in JSON body — nothing to store client-side.
   * Then fetches /auth/me to get full user profile with role.
   */
  login: async (email, password) => {
    set({ loading: true, error: null });
    try {
      const res = await apiClient.post('/auth/login', { email, password });

      // Handle 2FA requirement
      if (res.data.requires_2fa) {
        set({ loading: false });
        return res.data;
      }

      // Both tokens are now in httpOnly cookies — nothing to store in JS

      // Fetch full user profile (cookies are now set, browser sends them)
      const meRes = await apiClient.get('/auth/me');
      set({ user: meRes.data, loading: false, error: null });
      return meRes.data;
    } catch (err) {
      set({ loading: false });
      throw err;
    }
  },

  /**
   * Register — no auth needed, returns response for email verification flow.
   */
  register: async (data) => {
    try {
      const res = await apiClient.post('/auth/register', data);
      return res.data;
    } catch (err) {
      throw err;
    }
  },

  /**
   * Logout — backend clears both httpOnly cookies via response headers.
   * No localStorage cleanup needed — tokens are not in JS.
   */
  logout: async () => {
    try {
      await apiClient.post('/auth/logout');
    } catch {
      // Silent — clear local state regardless
      // Backend logout may fail if token already expired — that's fine
    }
    set({ user: null });
  },

  clearError: () => set({ error: null }),
}));

// Listen for session expiry from API interceptor (401 after refresh fails)
if (typeof window !== 'undefined') {
  window.addEventListener('auth:expired', () => {
    useAuthStore.setState({ user: null, loading: false });
  });
}

// Role-based redirect map (used by LoginPage)
export const ROLE_DEFAULT_ROUTE = {
  customer: '/',
  admin: '/admin/dashboard',
  product_manager: '/admin/products',
  order_manager: '/admin/orders',
  finance_manager: '/admin/reports',
};

export default useAuthStore;
