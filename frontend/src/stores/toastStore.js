// ============================================
// Phase 13F — Toast Notification Store (FIXED)
// Zustand store for global toast notifications
// Usage: const { success, error, info, warning } = useToast();
//        success('Product saved!');
// ============================================
import { create } from 'zustand';

let _toastId = 0;

export const useToastStore = create((set) => ({
  toasts: [],

  add: (toast) => {
    const id = ++_toastId;
    const duration = toast.duration != null ? toast.duration : (toast.type === 'error' ? 8000 : 5000);
    set((s) => {
      // Prevent duplicate messages within short window
      const isDupe = s.toasts.some((t) => t.message === toast.message);
      if (isDupe) return s;
      return { toasts: [...s.toasts, { ...toast, id }] };
    });
    if (duration > 0) {
      setTimeout(() => {
        set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
      }, duration);
    }
    return id;
  },

  remove: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),

  clear: () => set({ toasts: [] }),
}));

// Convenience hook — use in components
export function useToast() {
  const add = useToastStore((s) => s.add);
  return {
    success: (message, opts) => add({ type: 'success', message, ...opts }),
    error: (message, opts) => add({ type: 'error', message, ...opts }),
    warning: (message, opts) => add({ type: 'warning', message, ...opts }),
    info: (message, opts) => add({ type: 'info', message, ...opts }),
  };
}

// Imperative API — use outside React components (e.g., in API interceptors)
export const toast = {
  success: (message, opts) => useToastStore.getState().add({ type: 'success', message, ...opts }),
  error: (message, opts) => useToastStore.getState().add({ type: 'error', message, ...opts }),
  warning: (message, opts) => useToastStore.getState().add({ type: 'warning', message, ...opts }),
  info: (message, opts) => useToastStore.getState().add({ type: 'info', message, ...opts }),
};
