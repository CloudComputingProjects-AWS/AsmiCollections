/**
 * App.jsx — Phase F5 Fix
 *
 * Changes from old version:
 * 1. AdminLayout imported from components/admin/ (the F4 version with full sidebar)
 * 2. /admin/login → redirects to /login (no separate admin login)
 * 3. All 13 admin routes wired to existing F4 page components
 * 4. ProtectedRoute used correctly (wraps children, not as Outlet)
 * 5. Lazy imports fixed (lazy() must be at top level)
 */

import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// ── Layouts ────────────────────────────────────────────────────────────
import CustomerLayout from './layouts/CustomerLayout';
import AdminLayout    from './components/admin/AdminLayout';   // ← F4 version (full sidebar)

// ── Auth Pages ─────────────────────────────────────────────────────────
import LoginPage          from './pages/auth/LoginPage';        // ← unified login
import RegisterPage       from './pages/auth/RegisterPage';
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';

// ── Public / Catalog Pages ─────────────────────────────────────────────
import LandingPage        from './pages/Landing/LandingPage';
import CategoryPage       from './pages/Category/CategoryPage';
import ProductListingPage from './pages/Products/ProductListingPage';
import ProductDetailPage  from './pages/Products/ProductDetailPage';
import SearchResultsPage  from './pages/Search/SearchResultsPage';

// ── Customer Pages (protected) ─────────────────────────────────────────
import WishlistPage      from './pages/wishlist/WishlistPage';
import CartPage          from './pages/cart/CartPage';
import CheckoutPage      from './pages/checkout/CheckoutPage';
import OrderHistoryPage  from './pages/orders/OrderHistoryPage';
import OrderDetailPage   from './pages/orders/OrderDetailPage';
import UserDashboard     from './pages/dashboard/UserDashboard';

// ── Lazy-loaded customer pages ─────────────────────────────────────────
const EditProfilePage    = lazy(() => import('./pages/profile/EditProfilePage'));
const ManageAddressesPage = lazy(() => import('./pages/profile/ManageAddressesPage'));
const PrivacyConsentPage  = lazy(() => import('./pages/privacy/PrivacyConsentPage'));
const InvoiceViewPage     = lazy(() => import('./pages/orders/InvoiceViewPage'));

// ── Admin Pages (F4 — already built) ──────────────────────────────────
import AdminDashboardPage   from './pages/admin/AdminDashboardPage';
import ProductManager       from './pages/admin/ProductManager';
import ProductForm          from './pages/admin/ProductForm';
import CategoryManager      from './pages/admin/CategoryManager';
import AttributeManager     from './pages/admin/AttributeManager';
import CouponManager        from './pages/admin/CouponManager';
import InventoryOrderReturn from './pages/admin/InventoryOrderReturn';
import InvoiceUserAuditReports from './pages/admin/InvoiceUserAuditReports';

// ── Route Guards ────────────────────────────────────────────────────────
import ProtectedRoute from './components/auth/ProtectedRoute';
import AdminRoute     from './components/auth/AdminRoute';

// ── Spinner for Suspense ────────────────────────────────────────────────
function PageSpinner() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageSpinner />}>
        <Routes>

          {/* ── Auth (public, no layout) ──────────────────────── */}
          <Route path="/login"           element={<LoginPage />} />
          <Route path="/register"        element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />

          {/* Redirect old /admin/login → /login */}
          <Route path="/admin/login" element={<Navigate to="/login" replace />} />
          <Route path="admin/login"  element={<Navigate to="/login" replace />} />

          {/* ── Customer routes (with CustomerLayout) ─────────── */}
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
            <Route path="/wishlist"     element={<ProtectedRoute><WishlistPage /></ProtectedRoute>} />
            <Route path="/cart"         element={<CartPage />} />
            <Route path="/checkout"     element={<ProtectedRoute><CheckoutPage /></ProtectedRoute>} />
            <Route path="/orders"       element={<ProtectedRoute><OrderHistoryPage /></ProtectedRoute>} />
            <Route path="/orders/:id"   element={<ProtectedRoute><OrderDetailPage /></ProtectedRoute>} />
            <Route path="/profile"      element={<ProtectedRoute><EditProfilePage /></ProtectedRoute>} />
            <Route path="/addresses"    element={<ProtectedRoute><ManageAddressesPage /></ProtectedRoute>} />
            <Route path="/privacy"      element={<ProtectedRoute><PrivacyConsentPage /></ProtectedRoute>} />
            <Route path="/orders/:orderId/invoice" element={<ProtectedRoute><InvoiceViewPage /></ProtectedRoute>} />
          </Route>

          {/* ── Admin routes ──────────────────────────────────── */}
          {/*
            AdminRoute  = checks user is logged in AND has admin role
            AdminLayout = renders sidebar + <Outlet />
          */}
          <Route path="admin" element={<AdminRoute />}>
            <Route element={<AdminLayout />}>
              {/* /admin → /admin/dashboard */}
              <Route index element={<Navigate to="/admin/dashboard" replace />} />

              {/* Dashboard (all admin roles) */}
              <Route path="dashboard" element={<AdminDashboardPage />} />

              {/* Catalog — product_manager + superadmin */}
              <Route path="products"            element={<ProductManager />} />
              <Route path="products/new"        element={<ProductForm />} />
              <Route path="products/:id/edit"   element={<ProductForm />} />
              <Route path="categories"          element={<CategoryManager />} />
              <Route path="attributes"          element={<AttributeManager />} />
              <Route path="coupons"             element={<CouponManager />} />

              {/* Orders + Inventory + Returns — order_manager + superadmin */}
              <Route path="inventory"  element={<InventoryOrderReturn />} />
              <Route path="orders"     element={<InventoryOrderReturn />} />
              <Route path="returns"    element={<InventoryOrderReturn />} />

              {/* Finance + Users + Audit — finance_manager / superadmin */}
              <Route path="invoices"   element={<InvoiceUserAuditReports />} />
              <Route path="reports"    element={<InvoiceUserAuditReports />} />
              <Route path="users"      element={<InvoiceUserAuditReports />} />
              <Route path="audit-logs" element={<InvoiceUserAuditReports />} />
            </Route>
          </Route>

          {/* ── Catch-all ─────────────────────────────────────── */}
          <Route path="*" element={<Navigate to="/" replace />} />

        </Routes>
      </Suspense>
      <Toaster position="top-right" />
    </BrowserRouter>
  );
}
