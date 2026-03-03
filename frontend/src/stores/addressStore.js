/**
 * Address Store — Zustand
 * Manages user shipping/billing addresses.
 */
import { create } from 'zustand';
import apiClient from '../api/apiClient';

const useAddressStore = create((set, get) => ({
  addresses: [],
  loading: false,
  error: null,

  fetchAddresses: async () => {
    set({ loading: true, error: null });
    try {
      const res = await apiClient.get('/addresses');
      set({ addresses: res.data.addresses || res.data, loading: false });
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed to load addresses', loading: false });
    }
  },

  addAddress: async (data) => {
    try {
      const res = await apiClient.post('/addresses', data);
      await get().fetchAddresses();
      return res.data;
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed to add address' });
      return null;
    }
  },

  updateAddress: async (id, data) => {
    try {
      await apiClient.put(`/addresses/${id}`, data);
      await get().fetchAddresses();
      return true;
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed to update address' });
      return false;
    }
  },

  deleteAddress: async (id) => {
    try {
      await apiClient.delete(`/addresses/${id}`);
      set((state) => ({
        addresses: state.addresses.filter((a) => a.id !== id),
      }));
      return true;
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed to delete address' });
      return false;
    }
  },

  setDefault: async (id) => {
    try {
      await apiClient.put(`/addresses/${id}`, { is_default: true });
      await get().fetchAddresses();
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed to set default' });
    }
  },

  getDefault: () => {
    return get().addresses.find((a) => a.is_default) || get().addresses[0];
  },

  clearError: () => set({ error: null }),
}));

export default useAddressStore;
