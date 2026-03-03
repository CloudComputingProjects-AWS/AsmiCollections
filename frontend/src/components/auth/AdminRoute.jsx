import { Navigate, Outlet } from 'react-router-dom';
import useAuthStore from '../../stores/authStore';

const ADMIN_ROLES = ['admin', 'product_manager', 'order_manager', 'finance_manager'];

export default function AdminRoute() {
  const { user, loading } = useAuthStore();

  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-900 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user || !ADMIN_ROLES.includes(user.role)) {
    return <Navigate to="/admin/login" replace />;
  }

  return <Outlet />;
}
