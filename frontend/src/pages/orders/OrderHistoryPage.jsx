/**
 * OrderHistoryPage — Order listing with status badges, timeline, invoice download.
 */
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Package, ChevronRight, FileText, Clock, CheckCircle,
  XCircle, Truck, RotateCcw, ArrowLeft, Search,
} from 'lucide-react';
import useOrderStore from '../../stores/orderStore';
import useAuthStore from '../../stores/authStore';

const STATUS_MAP = {
  placed: { label: 'Placed', color: 'bg-blue-100 text-blue-700', icon: Clock },
  confirmed: { label: 'Confirmed', color: 'bg-indigo-100 text-indigo-700', icon: CheckCircle },
  processing: { label: 'Processing', color: 'bg-yellow-100 text-yellow-700', icon: Package },
  shipped: { label: 'Shipped', color: 'bg-purple-100 text-purple-700', icon: Truck },
  out_for_delivery: { label: 'Out for Delivery', color: 'bg-orange-100 text-orange-700', icon: Truck },
  delivered: { label: 'Delivered', color: 'bg-green-100 text-green-700', icon: CheckCircle },
  cancelled: { label: 'Cancelled', color: 'bg-red-100 text-red-700', icon: XCircle },
  return_requested: { label: 'Return Requested', color: 'bg-amber-100 text-amber-700', icon: RotateCcw },
  return_approved: { label: 'Return Approved', color: 'bg-amber-100 text-amber-700', icon: RotateCcw },
  return_received: { label: 'Return Received', color: 'bg-teal-100 text-teal-700', icon: CheckCircle },
  refunded: { label: 'Refunded', color: 'bg-gray-100 text-gray-700', icon: RotateCcw },
  return_rejected: { label: 'Return Rejected', color: 'bg-red-100 text-red-700', icon: XCircle },
};

export default function OrderHistoryPage() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { orders, loading, pagination, fetchOrders } = useOrderStore();
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    if (!user) {
      navigate('/login?next=/orders');
      return;
    }
    fetchOrders(1);
  }, [user]);

  const filteredOrders =
    filter === 'all' ? orders : orders.filter((o) => o.order_status === filter);

  const formatPrice = (price) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(price || 0);

  const formatDate = (dateStr) =>
    new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });

  if (loading && orders.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 pt-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="animate-pulse space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-xl h-36 w-full" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate('/dashboard')} className="p-2 hover:bg-gray-100 rounded-lg" aria-label="Back to dashboard">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">My Orders</h1>
              <p className="text-sm text-gray-500 mt-1">{pagination.total} orders total</p>
            </div>
          </div>

          {/* Filter tabs */}
          <div className="flex gap-2 mt-4 overflow-x-auto pb-1">
            {['all', 'placed', 'confirmed', 'shipped', 'delivered', 'cancelled'].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition ${
                  filter === f
                    ? 'bg-black text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {f === 'all' ? 'All' : STATUS_MAP[f]?.label || f}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {filteredOrders.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-2xl border">
            <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-700 mb-2">No orders found</h2>
            <p className="text-gray-500 mb-6">
              {filter === 'all'
                ? "You haven't placed any orders yet."
                : `No ${STATUS_MAP[filter]?.label?.toLowerCase() || filter} orders.`}
            </p>
            <Link
              to="/shop"
              className="inline-flex items-center gap-2 bg-black text-white px-6 py-3 rounded-lg hover:bg-gray-800 transition"
            >
              Start Shopping
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredOrders.map((order) => {
              const status = STATUS_MAP[order.order_status] || {
                label: order.order_status,
                color: 'bg-gray-100 text-gray-700',
                icon: Package,
              };
              const StatusIcon = status.icon;
              const firstItem = order.items?.[0] || {};

              return (
                <Link
                  key={order.id}
                  to={`/orders/${order.id}`}
                  className="block bg-white rounded-xl border p-5 hover:shadow-md transition group"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      {/* Order number + date */}
                      <div className="flex items-center gap-3 mb-2">
                        <p className="text-sm font-mono text-gray-500">
                          {order.order_number}
                        </p>
                        <span className="text-xs text-gray-400">
                          {formatDate(order.created_at)}
                        </span>
                      </div>

                      {/* Status badge */}
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${status.color}`}
                      >
                        <StatusIcon className="w-3.5 h-3.5" />
                        {status.label}
                      </span>

                      {/* Items preview */}
                      <div className="mt-3 flex items-center gap-2">
                        {(order.items || []).slice(0, 3).map((item, idx) => (
                          <div
                            key={idx}
                            className="w-10 h-10 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0"
                          >
                            <img
                              src={item.image_url_snapshot || '/placeholder-product.jpg'}
                              alt=""
                              className="w-full h-full object-cover"
                            />
                          </div>
                        ))}
                        {(order.items?.length || 0) > 3 && (
                          <span className="text-xs text-gray-400">
                            +{order.items.length - 3} more
                          </span>
                        )}
                        <span className="text-sm text-gray-600 ml-2">
                          {order.items?.length || 0} item{(order.items?.length || 0) !== 1 ? 's' : ''}
                        </span>
                      </div>
                    </div>

                    {/* Total + Arrow */}
                    <div className="text-right flex-shrink-0">
                      <p className="font-bold text-gray-900">{formatPrice(order.grand_total)}</p>
                      <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-gray-500 mt-2 ml-auto transition" />
                    </div>
                  </div>
                </Link>
              );
            })}

            {/* Pagination */}
            {pagination.totalPages > 1 && (
              <div className="flex justify-center gap-2 pt-4">
                {Array.from({ length: pagination.totalPages }, (_, i) => i + 1).map((page) => (
                  <button
                    key={page}
                    onClick={() => fetchOrders(page)}
                    className={`w-9 h-9 rounded-lg text-sm font-medium transition ${
                      pagination.page === page
                        ? 'bg-black text-white'
                        : 'bg-white border text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    {page}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
