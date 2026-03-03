/**
 * AdminSidebar.jsx â€” Phase F5 Fix
 * Only change: logout navigates to /login (not /admin/login)
 * All other F4 content preserved exactly.
 */
import { NavLink, useNavigate } from 'react-router-dom';
import useAuthStore from '../../stores/authStore';

const NAV_ITEMS = [
  { section: 'Overview', items: [
    { label: 'Dashboard', path: '/admin/dashboard', icon: 'ðŸ“Š', roles: ['admin', 'product_manager', 'order_manager', 'finance_manager'] },
  ]},
  { section: 'Catalog', items: [
    { label: 'Products',   path: '/admin/products',   icon: 'ðŸ‘•', roles: ['admin', 'product_manager'] },
    { label: 'Categories', path: '/admin/categories', icon: 'ðŸ“', roles: ['admin', 'product_manager'] },
    { label: 'Attributes', path: '/admin/attributes', icon: 'ðŸ·ï¸', roles: ['admin', 'product_manager'] },
    { label: 'Inventory',  path: '/admin/inventory',  icon: 'ðŸ“¦', roles: ['admin', 'product_manager'] },
    { label: 'Coupons',    path: '/admin/coupons',    icon: 'ðŸŽ«', roles: ['admin', 'product_manager'] },
  ]},
  { section: 'Orders', items: [
    { label: 'Order Manager',    path: '/admin/orders',  icon: 'ðŸ›’', roles: ['admin', 'order_manager'] },
    { label: 'Returns & Refunds', path: '/admin/returns', icon: 'â†©ï¸', roles: ['admin', 'order_manager'] },
  ]},
  { section: 'Finance', items: [
    { label: 'Invoices & CN', path: '/admin/invoices', icon: 'ðŸ§¾', roles: ['admin', 'finance_manager'] },
    { label: 'Reports',       path: '/admin/reports',  icon: 'ðŸ“ˆ', roles: ['admin', 'finance_manager'] },
  ]},
  { section: 'System', items: [
    { label: 'Users',      path: '/admin/users',      icon: 'ðŸ‘¥', roles: ['admin'] },
    { label: 'Audit Logs', path: '/admin/audit-logs', icon: 'ðŸ“‹', roles: ['admin'] },
    { label: 'Settings',   path: '/admin/settings',   icon: 'âš™ï¸', roles: ['admin'] },
  ]},
];

export default function AdminSidebar({ collapsed, onToggle }) {
  const user     = useAuthStore((s) => s.user);
  const logout   = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const userRole = user?.role || '';

  const handleLogout = async () => {
    await logout();
    navigate('/login');   // â† FIXED: was /admin/login
  };

  return (
    <aside className={`fixed top-0 left-0 h-screen bg-gray-900 text-white z-30 transition-all duration-300 ${collapsed ? 'w-16' : 'w-60'} flex flex-col`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 h-14 border-b border-gray-800">
        {!collapsed && <span className="text-sm font-bold tracking-wider">ASHMI ADMIN</span>}
        <button onClick={onToggle} className="p-1.5 hover:bg-gray-800 rounded-lg text-gray-400">
          {collapsed ? 'â˜°' : 'âœ•'}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-3 px-2">
        {NAV_ITEMS.map((section) => {
          const visibleItems = section.items.filter((item) =>
            item.roles.includes(userRole)
          );
          if (visibleItems.length === 0) return null;
          return (
            <div key={section.section} className="mb-3">
              {!collapsed && (
                <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-widest text-gray-400">
                  {section.section}
                </div>
              )}
              {visibleItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors mb-0.5 ${
                      isActive
                        ? 'bg-blue-600/20 text-blue-400'
                        : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
                    }`
                  }
                >
                  <span className="text-base flex-shrink-0">{item.icon}</span>
                  {!collapsed && <span>{item.label}</span>}
                </NavLink>
              ))}
            </div>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-gray-800 p-3">
        {!collapsed && (
          <div className="mb-2">
            <div className="text-xs font-medium text-gray-300 truncate">{user?.email}</div>
            <div className="text-[10px] text-gray-400 capitalize">
              {(userRole || '').replace(/_/g, ' ')}
            </div>
          </div>
        )}
        <button
          onClick={handleLogout}
          className={`w-full flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-red-900/20 rounded-lg ${collapsed ? 'justify-center' : ''}`}
        >
          <span>ðŸšª</span>
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  );
}
