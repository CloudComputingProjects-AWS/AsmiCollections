/**
 * Admin Auth Store â€” Shim for Phase F4
 */
import useAuthStore from './authStore';

export const useAdminAuthStore = () => {
  const store = useAuthStore();
  const user = store.user || null;
  const adminRoles = ['admin', 'product_manager', 'order_manager', 'finance_manager'];
  const isAdmin = user && adminRoles.includes(user.role);

  return {
    admin: user,
    isAuthenticated: !!user && isAdmin,
    logout: store.logout,
  };
};
