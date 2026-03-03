/**
 * Route Guards â€” protect routes based on auth state and role.
 */
import { Navigate, useLocation } from 'react-router-dom';
import useAuthStore from '@/stores/authStore';
import Spinner from '@/components/common/Spinner';

/** Requires authenticated user (any role) */
export function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuthStore();
  const location = useLocation();

  if (isLoading) return <PageLoader />;
  if (!isAuthenticated) return <Navigate to="/login" state={{ from: location }} replace />;
  return children;
}

/** Requires admin role */
export function AdminRoute({ children, requiredRole = null }) {
  const { isAuthenticated, isLoading, user } = useAuthStore();
  const isAdmin = useAuthStore((s) => s.isAdmin);
  const location = useLocation();

  if (isLoading) return <PageLoader />;
  if (!isAuthenticated) return <Navigate to="/admin/login" state={{ from: location }} replace />;
  if (!isAdmin()) return <Navigate to="/" replace />;
  if (requiredRole && user?.role !== requiredRole && user?.role !== 'admin') {
    return <Navigate to="/admin" replace />;
  }
  return children;
}

/** Redirects authenticated users away (e.g., login page) */
export function GuestRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) return <PageLoader />;
  if (isAuthenticated) return <Navigate to="/" replace />;
  return children;
}

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-surface">
      <Spinner size="lg" />
    </div>
  );
}
