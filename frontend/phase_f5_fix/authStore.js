/**
 * authStore.js — Unified Auth Store (Phase F5 Fix)
 *
 * Critical fix: login() always fetches /auth/me after token receipt
 * so user.role is GUARANTEED before caller navigates.
 *
 * Role → default route map (used by LoginPage for redirect):
 *   customer        → /dashboard
 *   superadmin      → /admin/dashboard
 *   product_manager → /admin/products
 *   order_manager   → /admin/orders
 *   finance_manager → /admin/reports
 */

import { create } from 'zustand';
import apiClient from '../api/apiClient';

export const ROLE_DEFAULT_ROUTE = {
  customer:        '/dashboard',
  superadmin:      '/admin/dashboard',
  product_manager: '/admin/products',
  order_manager:   '/admin/orders',
  finance_manager: '/admin/reports',
};

export const ADMIN_ROLES = ['superadmin', 'product_manager', 'order_manager', 'finance_manager'];

const useAuthStore = create((set, get) => ({
  user:    null,
  loading: false,
  error:   null,

  // ── Init (cold page load / F5 refresh) ─────────────────────────────
  init: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      set({ user: null, loading: false });
      return null;
    }
    set({ loading: true });
    try {
      const res = await apiClient.get('/auth/me');
      set({ user: res.data, loading: false });
      return res.data;
    } catch {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      set({ user: null, loading: false });
      return null;
    }
  },

  // ── Login ───────────────────────────────────────────────────────────
  // Always fetches /auth/me after token so role is guaranteed present.
  login: async (email, password) => {
    set({ error: null, loading: true });
    try {
      // Step 1: get tokens
      const res = await apiClient.post('/auth/login', { email, password });
      const { access_token, refresh_token } = res.data;

      if (!access_token) throw new Error('No access token in response');

      localStorage.setItem('access_token', access_token);
      if (refresh_token) localStorage.setItem('refresh_token', refresh_token);

      // Step 2: fetch full profile (guarantees role field)
      const profileRes = await apiClient.get('/auth/me');
      const user = profileRes.data;

      set({ user, loading: false, error: null });
      return user;   // caller reads user.role to navigate
    } catch (err) {
      const msg = err?.response?.data?.detail
        ?? err?.response?.data?.message
        ?? err.message
        ?? 'Login failed';
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      set({ user: null, loading: false, error: msg });
      throw new Error(msg);
    }
  },

  // ── Register ────────────────────────────────────────────────────────
  register: async (data) => {
    set({ error: null });
    try {
      const res = await apiClient.post('/auth/register', data);
      return res.data;
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Registration failed';
      set({ error: msg });
      throw err;
    }
  },

  // ── Logout ──────────────────────────────────────────────────────────
  logout: async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        await apiClient.post('/auth/logout', { refresh_token: refreshToken });
      }
    } catch { /* silent */ }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null, error: null });
  },

  clearError: () => set({ error: null }),
}));

export default useAuthStore;
