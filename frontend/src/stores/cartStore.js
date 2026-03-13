/**
 * Cart Store — Zustand
 * Guest cart in localStorage, server-side for authenticated users.
 * Auto-merges guest cart on login.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import apiClient from '../api/apiClient';

const GUEST_CART_KEY = 'ashmi_guest_cart';

const useCartStore = create(
  persist(
    (set, get) => ({
      items: [],
      cartId: null,
      loading: false,
      error: null,
      coupon: null,
      couponDiscount: 0,
      itemCount: 0,

      // ── Server cart (authenticated) ──────────────────
      fetchCart: async () => {
        set({ loading: true, error: null });
        try {
          const res = await apiClient.get('/cart');
          const data = res.data;
          set({
            items: data.items || [],
            cartId: data.id || data.cart_id,
            itemCount: (data.items || []).reduce((sum, i) => sum + i.quantity, 0),
            loading: false,
          });
        } catch (err) {
          set({ error: err.response?.data?.detail || 'Failed to load cart', loading: false });
        }
      },

      addToCart: async (variantId, quantity = 1, isAuthenticated = false) => {
        if (!isAuthenticated) {
          // Guest: localStorage
          const { items } = get();
          const existing = items.find((i) => i.product_variant_id === variantId);
          let newItems;
          if (existing) {
            newItems = items.map((i) =>
              i.product_variant_id === variantId ? { ...i, quantity: i.quantity + quantity } : i
            );
          } else {
            newItems = [...items, { variant_id: variantId, quantity }];
          }
          set({
            items: newItems,
            itemCount: newItems.reduce((sum, i) => sum + i.quantity, 0),
          });
          return true;
        }

        // Authenticated: server-side
        try {
          await apiClient.post('/cart/add', {
            variant_id: variantId,
            quantity,
          });
          await get().fetchCart();
          return true;
        } catch (err) {
          set({ error: err.response?.data?.detail || 'Failed to add to cart' });
          return false;
        }
      },

      updateQuantity: async (itemId, quantity, isAuthenticated = false) => {
        if (!isAuthenticated) {
          const { items } = get();
          const newItems = items.map((i) =>
            (i.id || i.product_variant_id) === itemId ? { ...i, quantity } : i
          );
          set({
            items: newItems,
            itemCount: newItems.reduce((sum, i) => sum + i.quantity, 0),
          });
          return;
        }
        try {
          await apiClient.put(`/cart/${itemId}`, { quantity });
          await get().fetchCart();
        } catch (err) {
          set({ error: err.response?.data?.detail || 'Failed to update' });
        }
      },

      removeItem: async (itemId, isAuthenticated = false) => {
        if (!isAuthenticated) {
          const { items } = get();
          const newItems = items.filter((i) => (i.id || i.product_variant_id) !== itemId);
          set({
            items: newItems,
            itemCount: newItems.reduce((sum, i) => sum + i.quantity, 0),
          });
          return;
        }
        try {
          await apiClient.delete(`/cart/${itemId}`);
          await get().fetchCart();
        } catch (err) {
          set({ error: err.response?.data?.detail || 'Failed to remove' });
        }
      },

      clearCart: async (isAuthenticated = false) => {
        if (!isAuthenticated) {
          set({ items: [], itemCount: 0, coupon: null, couponDiscount: 0 });
          return;
        }
        try {
          await apiClient.delete('/cart');
          set({ items: [], itemCount: 0, coupon: null, couponDiscount: 0 });
        } catch (err) {
          set({ error: err.response?.data?.detail || 'Failed to clear cart' });
        }
      },

      // ── Guest cart merge on login ────────────────────
      mergeGuestCart: async () => {
        const { items } = get();
        if (items.length === 0) return;

        try {
          await apiClient.post('/cart/merge', { items });
          // Clear local guest items after merge
          set({ items: [], itemCount: 0 });
          await get().fetchCart();
        } catch {
          // Fallback: just fetch server cart
          await get().fetchCart();
        }
      },

      // ── Coupon ───────────────────────────────────────
      applyCoupon: async (code) => {
        try {
          const res = await apiClient.post('/cart/apply-coupon', { code });
          set({
            coupon: res.data.coupon || { code },
            couponDiscount: res.data.discount || res.data.coupon_discount || 0,
          });
          return { success: true, discount: res.data.discount || 0 };
        } catch (err) {
          return {
            success: false,
            error: err.response?.data?.detail || 'Invalid coupon',
          };
        }
      },

      removeCoupon: () => {
        set({ coupon: null, couponDiscount: 0 });
      },

      // ── Computed ─────────────────────────────────────
      getSubtotal: () => {
        const { items } = get();
        return items.reduce((sum, i) => {
          const price = i.unit_price || i.price || i.product?.sale_price || i.product?.base_price || 0;
          return sum + price * i.quantity;
        }, 0);
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: GUEST_CART_KEY,
      partialize: (state) => ({
        items: state.items,
        itemCount: state.itemCount,
      }),
    }
  )
);

export default useCartStore;

