/**
 * App.jsx — Main Application Entry
 *
 * httpOnly cookie authentication:
 * - useEffect calls authStore.init() on mount to restore session from httpOnly cookie
 * - No localStorage access_token — browser sends cookie automatically
 * - AdminLayout from components/layouts/ (F5 production version with full sidebar nav)
 * - /admin/login redirects to /login (unified login)
 * - All 14 admin routes wired to page components
 * - ProtectedRoute wraps children correctly
 * - Lazy imports at top level
 *
 * Auth flow on F5 refresh:
 *   1. App mounts → useEffect calls authStore.init() → loading: true
 *   2. init() calls /auth/me → browser sends httpOnly cookie
 *   3. If valid → user restored, loading: false
 *   4. AdminRoute checks loading/user → renders AdminLayout
 *   5. AdminLayout has NO auth logic — trusts AdminRoute guard
 */

import { useEffect, lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import useAuthStore from './stores/authStore';
import useIdleTimeout from './hooks/useIdleTimeout';
import ToastContainer from './components/ui/ToastContainer';
import { SkipToContent } from './components/ui/Accessibility';
import { ErrorBoundary } from './components/ui/ErrorBoundary';

// -- Layouts ---------------------------------------------------------------
import CustomerLayout from './layouts/CustomerLayout';
import AdminLayout    from './components/layouts/AdminLayout';

// -- Auth Pages ------------------------------------------------------------
import AuthLayout         from './components/layouts/AuthLayout';
import LoginPage          from './pages/auth/LoginPage';
import RegisterPage       from './pages/auth/RegisterPage';
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';
import ResetPasswordPage from './pages/auth/ResetPasswordPage';
import VerifyOTPPage from './pages/auth/VerifyOTPPage';

// -- Public / Catalog Pages ------------------------------------------------
import LandingPage        from './pages/Landing/LandingPage';
import CategoryPage       from './pages/Category/CategoryPage';
import ProductListingPage from './pages/Products/ProductListingPage';
import ProductDetailPage  from './pages/Products/ProductDetailPage';
import SearchResultsPage  from './pages/Search/SearchResultsPage';

// -- Customer Pages (protected) --------------------------------------------
import CartPage          from './pages/cart/CartPage';
import CheckoutPage      from './pages/checkout/CheckoutPage';
import OrderHistoryPage  from './pages/orders/OrderHistoryPage';
import OrderDetailPage   from './pages/orders/OrderDetailPage';
import UserDashboard     from './pages/dashboard/UserDashboard';

// -- Lazy-loaded customer pages --------------------------------------------
const PrivacyConsentPage  = lazy(() => import('./pages/profile/PrivacyConsentPage'));
const PrivacyPolicyPage   = lazy(() => import('./pages/legal/PrivacyPolicyPage'));
const TermsOfServicePage  = lazy(() => import('./pages/legal/TermsOfServicePage'));
import CookieConsentBanner from './components/common/CookieConsentBanner';
const EditProfilePage     = lazy(() => import('./pages/profile/EditProfilePage'));
const ManageAddressesPage = lazy(() => import('./pages/profile/ManageAddressesPage'));
const InvoiceViewPage     = lazy(() => import('./pages/orders/InvoiceViewPage'));

// -- Admin Pages -----------------------------------------------------------
import AdminDashboard from './pages/admin/AdminDashboard';
import ProductManager     from './pages/admin/ProductManager';
import ProductForm        from './pages/admin/ProductForm';
import CategoryManager    from './pages/admin/CategoryManager';
import AttributeManager   from './pages/admin/AttributeManager';
import CouponManager      from './pages/admin/CouponManager';
import { InventoryManager, OrderManager, ReturnManager } from './pages/admin/InventoryOrderReturn';
import { InvoiceViewer, UserManager, AuditLogViewer, ReportsPage } from './pages/admin/InvoiceUserAuditReports';

// -- Admin Settings (Phase 13H) -------------------------------------------
const AdminSettingsPage = lazy(() => import('./pages/admin/AdminSettingsPage'));

// -- Route Guards ----------------------------------------------------------
import ProtectedRoute from './components/auth/ProtectedRoute';
import AdminRoute     from './components/auth/AdminRoute';

// -- Spinner for Suspense -------------------------------------------------
function PageSpinner() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

export default function App() {
  const init = useAuthStore((s) => s.init);

  // Restore session from httpOnly cookie on app startup
  useEffect(() => {
    init();
  }, []);
  useIdleTimeout();

  return (
    <BrowserRouter>
      <SkipToContent />
      <Suspense fallback={<PageSpinner />}>
        <ErrorBoundary>
          <Routes>

            {/* -- Auth (public, with AuthLayout) ------------------ */}
            <Route element={<AuthLayout />}>
              <Route path="/login"           element={<LoginPage />} />
              <Route path="/register"        element={<RegisterPage />} />
              <Route path="/forgot-password" element={<ForgotPasswordPage />} />
              <Route path="/reset-password" element={<ResetPasswordPage />} />
              <Route path="/verify-otp" element={<VerifyOTPPage />} />
            </Route>

            {/* Redirect old /admin/login to /login */}
            <Route path="/admin/login" element={<Navigate to="/login" replace />} />
            <Route path="admin/login"  element={<Navigate to="/login" replace />} />

            {/* -- Customer routes (with CustomerLayout) ----------- */}
            <Route element={<CustomerLayout />}>
              {/* Public */}
              <Route index                                   element={<LandingPage />} />
              <Route path="categories"                       element={<CategoryPage />} />
              <Route path="categories/:gender"               element={<CategoryPage />} />
              <Route path="categories/:gender/:ageGroup"     element={<CategoryPage />} />
              <Route path="shop"                             element={<ProductListingPage />} />
              <Route path="products/:slug"                   element={<ProductDetailPage />} />
              <Route path="search"                           element={<SearchResultsPage />} />

              {/* Protected customer pages */}
              <Route path="/dashboard"    element={<ProtectedRoute><UserDashboard /></ProtectedRoute>} />
              <Route path="/cart"         element={<CartPage />} />
              <Route path="/checkout"     element={<ProtectedRoute><CheckoutPage /></ProtectedRoute>} />
              <Route path="/orders"       element={<ProtectedRoute><OrderHistoryPage /></ProtectedRoute>} />
              <Route path="/orders/:id"   element={<ProtectedRoute><OrderDetailPage /></ProtectedRoute>} />
              <Route path="/profile"      element={<ProtectedRoute><EditProfilePage /></ProtectedRoute>} />
              <Route path="/privacy"        element={<ProtectedRoute><PrivacyConsentPage /></ProtectedRoute>} />
              <Route path="/privacy-policy" element={<PrivacyPolicyPage />} />
              <Route path="/terms"          element={<TermsOfServicePage />} />
              <Route path="/addresses"    element={<ProtectedRoute><ManageAddressesPage /></ProtectedRoute>} />
              <Route path="/orders/:orderId/invoice" element={<ProtectedRoute><InvoiceViewPage /></ProtectedRoute>} />
            </Route>

            {/* -- Admin routes ------------------------------------ */}
            <Route path="admin" element={<AdminRoute />}>
              <Route element={<AdminLayout />}>
                <Route index element={<Navigate to="/admin/dashboard" replace />} />
                <Route path="dashboard" element={<AdminDashboard />} />
                <Route path="products"            element={<ProductManager />} />
                <Route path="products/new"        element={<ProductForm />} />
                <Route path="products/:id/edit"   element={<ProductForm />} />
                <Route path="categories"          element={<CategoryManager />} />
                <Route path="attributes"          element={<AttributeManager />} />
                <Route path="coupons"             element={<CouponManager />} />
                <Route path="inventory"  element={<InventoryManager />} />
                <Route path="orders"     element={<OrderManager />} />
                <Route path="returns"    element={<ReturnManager />} />
                <Route path="invoices"   element={<InvoiceViewer />} />
                <Route path="reports"    element={<ReportsPage />} />
                <Route path="users"      element={<UserManager />} />
                <Route path="audit-logs" element={<AuditLogViewer />} />
                <Route path="settings"   element={<AdminSettingsPage />} />
              </Route>
            </Route>

            {/* -- Catch-all --------------------------------------- */}
            <Route path="*" element={<Navigate to="/" replace />} />

          </Routes>
        </ErrorBoundary>
      </Suspense>
      <ToastContainer />
      <CookieConsentBanner />
    </BrowserRouter>
  );
}
