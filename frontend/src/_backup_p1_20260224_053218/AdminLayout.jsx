/**
 * Admin Layout — Production (components/layouts/)
 *
 * IMPORTANT: Authentication is handled by AdminRoute wrapper.
 * AdminLayout does NOT perform its own auth check.
 * By the time AdminLayout renders, AdminRoute has already confirmed:
 *   - authStore.init() completed
 *   - user is authenticated
 *   - user has an admin role
 *
 * NAV_ITEMS must match exactly the routes defined in App.jsx under /admin.
 * Do NOT add nav items without corresponding routes.
 *
 * Fix log:
 *   - v3 (Feb 24 2026): No auth logic, trusts AdminRoute guard
 *   - v3.1: Removed Shipping nav item (no /admin/shipping route exists)
 */
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Package, FolderTree, Tags, Layers,
  ShoppingCart, RefreshCcw, FileText, Users, Shield,
  LogOut, Menu, X, Receipt,
} from 'lucide-react';
import clsx from 'clsx';
import useAuthStore from '@/stores/authStore';
import useUIStore from '@/stores/uiStore';

/**
 * NAV_ITEMS — must match App.jsx admin routes exactly.
 * Current App.jsx routes:
 *   dashboard, products, categories, attributes, coupons,
 *   inventory, orders, returns, invoices, reports, users, audit-logs, settings
 */
const NAV_ITEMS = [
  { label: 'Dashboard', icon: LayoutDashboard, path: '/admin', roles: ['superadmin', 'product_manager', 'order_manager', 'finance_manager'] },
  { label: 'Products', icon: Package, path: '/admin/products', roles: ['superadmin', 'product_manager'] },
  { label: 'Categories', icon: FolderTree, path: '/admin/categories', roles: ['superadmin', 'product_manager'] },
  { label: 'Attributes', icon: Tags, path: '/admin/attributes', roles: ['superadmin', 'product_manager'] },
  { label: 'Inventory', icon: Layers, path: '/admin/inventory', roles: ['superadmin', 'product_manager'] },
  { label: 'Orders', icon: ShoppingCart, path: '/admin/orders', roles: ['superadmin', 'order_manager'] },
  { label: 'Returns', icon: RefreshCcw, path: '/admin/returns', roles: ['superadmin', 'order_manager'] },
  { label: 'Invoices', icon: FileText, path: '/admin/invoices', roles: ['superadmin', 'finance_manager'] },
  { label: 'Coupons', icon: Receipt, path: '/admin/coupons', roles: ['superadmin', 'product_manager'] },
  { label: 'Users', icon: Users, path: '/admin/users', roles: ['superadmin'] },
  { label: 'Audit Logs', icon: Shield, path: '/admin/audit-logs', roles: ['superadmin'] },
];

export default function AdminLayout() {
  const { sidebarOpen, toggleSidebar } = useUIStore();

  return (
    <div className="flex h-screen bg-surface-sunken overflow-hidden">
      {/* Sidebar overlay (mobile) */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 bg-black/40 lg:hidden" onClick={toggleSidebar} />
      )}

      {/* Sidebar */}
      <aside className={clsx(
        'fixed inset-y-0 left-0 z-50 w-64 bg-surface-dark text-ink-inverse flex flex-col transition-transform duration-200 lg:translate-x-0 lg:static lg:z-auto',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      )}>
        <SidebarContent />
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <AdminTopBar />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function SidebarContent() {
  const { user, logout } = useAuthStore();
  const location = useLocation();
  const navigate = useNavigate();
  const { toggleSidebar } = useUIStore();

  const filteredNav = NAV_ITEMS.filter(
    (item) => item.roles.includes(user?.role)
  );

  return (
    <>
      {/* Logo */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-ink-inverse/10">
        <Link to="/admin" className="font-display text-lg">Ashmi Admin</Link>
        <button onClick={toggleSidebar} className="lg:hidden text-ink-inverse/60 hover:text-ink-inverse">
          <X size={20} />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-0.5">
        {filteredNav.map((item) => {
          const isActive = location.pathname === item.path ||
            (item.path !== '/admin' && location.pathname.startsWith(item.path));
          return (
            <Link
              key={item.path}
              to={item.path}
              onClick={() => window.innerWidth < 1024 && toggleSidebar()}
              className={clsx(
                'flex items-center gap-3 px-3 py-2 rounded-[var(--radius-md)] text-sm font-medium transition-colors',
                isActive
                  ? 'bg-brand-600 text-white'
                  : 'text-ink-inverse/70 hover:bg-ink-inverse/10 hover:text-ink-inverse'
              )}
            >
              <item.icon size={18} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* User info & logout */}
      <div className="px-4 py-3 border-t border-ink-inverse/10">
        <div className="text-xs text-ink-inverse/50 mb-1">{user?.role?.replace('_', ' ')}</div>
        <div className="text-sm font-medium text-ink-inverse/80 truncate">{user?.email}</div>
        <button
          onClick={async () => { await logout(); navigate('/login'); }}
          className="mt-2 flex items-center gap-2 text-xs text-ink-inverse/50 hover:text-error transition-colors"
        >
          <LogOut size={14} /> Sign out
        </button>
      </div>
    </>
  );
}

function AdminTopBar() {
  const { toggleSidebar } = useUIStore();

  return (
    <div className="flex items-center justify-between px-4 py-3 bg-surface-raised border-b border-ink-faint/10 lg:px-6">
      <button onClick={toggleSidebar} className="lg:hidden text-ink-muted hover:text-ink">
        <Menu size={22} />
      </button>
      <div className="hidden lg:block" />
      <Link to="/" className="text-sm text-ink-muted hover:text-brand-600 transition-colors">
        View Store →
      </Link>
    </div>
  );
}
