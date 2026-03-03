/**
 * Admin Routes — Phase F4
 * Wire all admin pages into the React Router.
 * 
 * INTEGRATION: Add these routes to your existing App.jsx
 * inside the AdminLayout wrapper.
 */
import { lazy } from 'react';

// Lazy-load all admin pages for code splitting
const AdminDashboard = lazy(() => import('../pages/admin/AdminDashboard'));
const ProductManager = lazy(() => import('../pages/admin/ProductManager'));
const ProductForm = lazy(() => import('../pages/admin/ProductForm'));
const CategoryManager = lazy(() => import('../pages/admin/CategoryManager'));
const AttributeManager = lazy(() => import('../pages/admin/AttributeManager'));
const CouponManager = lazy(() => import('../pages/admin/CouponManager'));

// These export multiple components from single files
const InventoryOrderReturn = () => import('../pages/admin/InventoryOrderReturn');
const InvoiceUserAuditReports = () => import('../pages/admin/InvoiceUserAuditReports');

/**
 * ROUTE DEFINITIONS — paste inside your <Route path="/admin" element={<AdminLayout />}>
 * 
 * <Route index element={<AdminDashboard />} />
 * <Route path="dashboard" element={<AdminDashboard />} />
 * <Route path="products" element={<ProductManager />} />
 * <Route path="products/new" element={<ProductForm />} />
 * <Route path="products/:id/edit" element={<ProductForm />} />
 * <Route path="categories" element={<CategoryManager />} />
 * <Route path="attributes" element={<AttributeManager />} />
 * <Route path="inventory" element={<InventoryManager />} />
 * <Route path="orders" element={<OrderManager />} />
 * <Route path="returns" element={<ReturnManager />} />
 * <Route path="coupons" element={<CouponManager />} />
 * <Route path="invoices" element={<InvoiceViewer />} />
 * <Route path="users" element={<UserManager />} />
 * <Route path="audit-logs" element={<AuditLogViewer />} />
 * <Route path="reports" element={<ReportsPage />} />
 */

export {
  AdminDashboard,
  ProductManager,
  ProductForm,
  CategoryManager,
  AttributeManager,
  CouponManager,
};

// Re-export named exports from combined files
export { InventoryManager } from '../pages/admin/InventoryOrderReturn';
export { OrderManager } from '../pages/admin/InventoryOrderReturn';
export { ReturnManager } from '../pages/admin/InventoryOrderReturn';
export { InvoiceViewer } from '../pages/admin/InvoiceUserAuditReports';
export { UserManager } from '../pages/admin/InvoiceUserAuditReports';
export { AuditLogViewer } from '../pages/admin/InvoiceUserAuditReports';
export { ReportsPage } from '../pages/admin/InvoiceUserAuditReports';
