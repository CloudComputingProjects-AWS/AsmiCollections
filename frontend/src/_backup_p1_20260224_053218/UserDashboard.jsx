/**
 * UserDashboard — Overview: recent orders, addresses, profile summary, quick links.
 */
import { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, Package, Heart, MapPin, Settings, ChevronRight, Shield, LogOut } from 'lucide-react';
import useAuthStore from '../../stores/authStore';
import useOrderStore from '../../stores/orderStore';
import useWishlistStore from '../../stores/wishlistStore';
import useAddressStore from '../../stores/addressStore';

const STATUS_COLORS = {
  placed: 'bg-blue-100 text-blue-700',
  confirmed: 'bg-indigo-100 text-indigo-700',
  processing: 'bg-yellow-100 text-yellow-700',
  shipped: 'bg-purple-100 text-purple-700',
  delivered: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-700',
};

export default function UserDashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { orders, fetchOrders } = useOrderStore();
  const { items: wishlistItems, fetchWishlist } = useWishlistStore();
  const { addresses, fetchAddresses } = useAddressStore();

  useEffect(() => {
    if (!user) { navigate('/login?redirect=/dashboard'); return; }
    fetchOrders(1);
    fetchWishlist();
    fetchAddresses();
  }, [user]);

  const recentOrders = (orders || []).slice(0, 3);
  const fmt = (p) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(p || 0);
  const fmtDate = (d) => new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });

  const quickLinks = [
    { to: '/orders', icon: Package, label: 'My Orders', count: orders.length },
    { to: '/wishlist', icon: Heart, label: 'Wishlist', count: wishlistItems.length },
    { to: '/dashboard/addresses', icon: MapPin, label: 'Addresses', count: addresses.length },
    { to: '/dashboard/profile', icon: Settings, label: 'Edit Profile' },
    { to: '/dashboard/privacy', icon: Shield, label: 'Privacy & Consent' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b">
        <div className="max-w-5xl mx-auto px-4 py-8">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-black text-white rounded-full flex items-center justify-center text-xl font-bold">
              {(user?.first_name?.[0] || user?.email?.[0] || 'U').toUpperCase()}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {user?.first_name ? `Hi, ${user.first_name}!` : 'My Account'}
              </h1>
              <p className="text-sm text-gray-500">{user?.email}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl border overflow-hidden">
            {quickLinks.map((link, i) => {
              const Icon = link.icon;
              return (
                <Link key={link.to} to={link.to}
                  className={`flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition ${i < quickLinks.length - 1 ? 'border-b' : ''}`}>
                  <div className="flex items-center gap-3">
                    <Icon className="w-5 h-5 text-gray-500" />
                    <span className="font-medium text-gray-900 text-sm">{link.label}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {link.count !== undefined && (
                      <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{link.count}</span>
                    )}
                    <ChevronRight className="w-4 h-4 text-gray-300" />
                  </div>
                </Link>
              );
            })}
            <button onClick={async () => { await logout(); navigate('/'); }}
              className="w-full flex items-center gap-3 px-5 py-4 hover:bg-red-50 transition text-left border-t">
              <LogOut className="w-5 h-5 text-red-500" />
              <span className="font-medium text-red-600 text-sm">Logout</span>
            </button>
          </div>
        </div>

        {/* Main */}
        <div className="lg:col-span-2 space-y-6">
          {/* Recent Orders */}
          <div className="bg-white rounded-xl border">
            <div className="flex items-center justify-between px-5 py-4 border-b">
              <h2 className="font-bold text-gray-900">Recent Orders</h2>
              <Link to="/orders" className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1">
                View All <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
            {recentOrders.length === 0 ? (
              <div className="text-center py-10">
                <Package className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                <p className="text-sm text-gray-500">No orders yet</p>
                <Link to="/shop" className="text-sm text-blue-600 mt-2 inline-block">Start Shopping</Link>
              </div>
            ) : (
              <div>
                {recentOrders.map((order) => (
                  <Link key={order.id} to={`/orders/${order.id}`}
                    className="flex items-center justify-between px-5 py-4 border-b last:border-0 hover:bg-gray-50 transition">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                        <Package className="w-5 h-5 text-gray-400" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{order.order_number}</p>
                        <p className="text-xs text-gray-500">{fmtDate(order.created_at)}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">{fmt(order.grand_total)}</p>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${STATUS_COLORS[order.order_status] || 'bg-gray-100 text-gray-700'}`}>
                        {order.order_status?.replace(/_/g, ' ')}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Addresses */}
          <div className="bg-white rounded-xl border">
            <div className="flex items-center justify-between px-5 py-4 border-b">
              <h2 className="font-bold text-gray-900">Saved Addresses</h2>
              <Link to="/dashboard/addresses" className="text-sm text-blue-600 flex items-center gap-1">
                Manage <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
            {addresses.length === 0 ? (
              <div className="text-center py-8">
                <MapPin className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-500 mb-3">No saved addresses</p>
                <Link to="/dashboard/addresses" className="text-sm text-blue-600">Add Address</Link>
              </div>
            ) : (
              <div className="p-5 space-y-3">
                {addresses.slice(0, 2).map((addr) => (
                  <div key={addr.id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                    <MapPin className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                    <div className="text-sm text-gray-600">
                      <span className="font-medium text-gray-900">{addr.full_name}</span>
                      <span className="text-xs ml-2 bg-gray-200 text-gray-500 px-1.5 py-0.5 rounded uppercase">{addr.label}</span>
                      <p className="mt-0.5">{addr.address_line_1}, {addr.city}, {addr.state} — {addr.postal_code}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
