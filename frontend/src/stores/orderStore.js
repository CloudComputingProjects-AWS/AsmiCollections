/**
 * Order Store — Zustand
 * Manages order history, detail, cancellation, returns.
 */
import { create } from 'zustand';
import apiClient from '../api/apiClient';

const useOrderStore = create((set, get) => ({
  orders: [],
  currentOrder: null,
  timeline: [],
  loading: false,
  error: null,
  pagination: { page: 1, totalPages: 1, total: 0 },

  fetchOrders: async (page = 1) => {
    set({ loading: true, error: null });
    try {
      const res = await apiClient.get('/orders', { params: { page, limit: 10 } });
      const data = res.data;
      set({
        orders: data.items || data.orders || data,
        pagination: {
          page: data.page || page,
          totalPages: data.total_pages || Math.ceil((data.total || 0) / 10),
          total: data.total || 0,
        },
        loading: false,
      });
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed to load orders', loading: false });
    }
  },

  fetchOrderDetail: async (orderId) => {
    set({ loading: true, error: null, currentOrder: null });
    try {
      const res = await apiClient.get(`/orders/${orderId}`);
      set({ currentOrder: res.data, loading: false });
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed to load order', loading: false });
    }
  },

  fetchTimeline: async (orderId) => {
    try {
      const res = await apiClient.get(`/orders/${orderId}/timeline`);
      set({ timeline: res.data.history || res.data || [] });
    } catch {
      set({ timeline: [] });
    }
  },

  cancelOrder: async (orderId, reason) => {
    try {
      await apiClient.post(`/orders/${orderId}/cancel`, { reason });
      // Refresh
      await get().fetchOrderDetail(orderId);
      await get().fetchTimeline(orderId);
      return true;
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed to cancel order' });
      return false;
    }
  },

  requestReturn: async (orderId, itemId, data) => {
    try {
      await apiClient.post(`/returns`, {
        order_id: orderId,
        order_item_id: itemId,
        ...data,
      });
      return true;
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed to request return' });
      return false;
    }
  },

  downloadInvoice: async (orderId) => {
    try {
      const res = await apiClient.get(`/orders/${orderId}/invoice`);
      const { download_url, filename } = res.data;
      const a = document.createElement('a');
      a.href = download_url;
      a.download = filename;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (err) {
      set({ error: 'Failed to download invoice' });
    }
  },

  clearError: () => set({ error: null }),
}));

export default useOrderStore;
