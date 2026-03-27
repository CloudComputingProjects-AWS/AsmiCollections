/**
 * OrderDetailPage — Full order detail with timeline, invoice, cancel, return.
 */
import { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft, FileText, RotateCcw, XCircle, CheckCircle2,
  Clock, Truck, Package, MapPin, CreditCard, Download,
  ChevronDown, ChevronUp, AlertCircle,
} from 'lucide-react';
import useOrderStore from '../../stores/orderStore';
import useAuthStore from '../../stores/authStore';
import toast from 'react-hot-toast';
import confetti from 'canvas-confetti';

const STATUS_STEPS = [
  { key: 'placed', label: 'Placed', icon: Clock },
  { key: 'confirmed', label: 'Confirmed', icon: CheckCircle2 },
  { key: 'processing', label: 'Processing', icon: Package },
  { key: 'shipped', label: 'Shipped', icon: Truck },
  { key: 'delivered', label: 'Delivered', icon: CheckCircle2 },
];

const CANCEL_REASONS = [
  'Changed my mind',
  'Found a better price elsewhere',
  'Ordered by mistake',
  'Delivery taking too long',
  'Other',
];

const RETURN_REASONS = [
  'Wrong item received',
  'Item damaged/defective',
  'Size doesn\'t fit',
  'Color/style different from listing',
  'Quality not as expected',
  'Other',
];

export default function OrderDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isNew = searchParams.get('new') === 'true';
  const { user } = useAuthStore();
  const {
    currentOrder: order, timeline, loading,
    fetchOrderDetail, fetchTimeline, cancelOrder, requestReturn, downloadInvoice,
  } = useOrderStore();

  const [showCancel, setShowCancel] = useState(false);
  const [cancelReason, setCancelReason] = useState('');
  const [showReturn, setShowReturn] = useState(null); // item id
  const [returnData, setReturnData] = useState({ reason: '', reason_detail: '', return_type: 'refund', quantity: 1 });
  const [showTimeline, setShowTimeline] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    fetchOrderDetail(id);
    fetchTimeline(id);
  }, [id, user]);

  useEffect(() => {
    if (isNew && order) {
      // Celebration for new order
      try { confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } }); } catch {}
    }
  }, [isNew, order]);

  const canCancel = ['placed', 'confirmed', 'processing'].includes(order?.order_status);
  const canReturn = order?.order_status === 'delivered';

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
      hour: '2-digit',
      minute: '2-digit',
    });

  const handleCancel = async () => {
    if (!cancelReason) {
      toast.error('Please select a reason');
      return;
    }
    setActionLoading(true);
    const ok = await cancelOrder(id, cancelReason);
    setActionLoading(false);
    if (ok) {
      toast.success('Order cancelled');
      setShowCancel(false);
    }
  };

  const handleReturn = async (itemId) => {
    if (!returnData.reason) {
      toast.error('Please select a reason');
      return;
    }
    setActionLoading(true);
    const ok = await requestReturn(id, itemId, returnData);
    setActionLoading(false);
    if (ok) {
      toast.success('Return requested');
      setShowReturn(null);
    }
  };

  // Progress bar position
  const getProgress = () => {
    const statusOrder = ['placed', 'confirmed', 'processing', 'shipped', 'delivered'];
    const idx = statusOrder.indexOf(order?.order_status);
    if (idx < 0) return 0;
    return ((idx) / (statusOrder.length - 1)) * 100;
  };

  if (loading || !order) {
    return (
      <div className="bg-gray-50 pt-8 pb-12">
        <div className="max-w-4xl mx-auto px-4">
          <div className="animate-pulse space-y-4">
            <div className="bg-white rounded-xl h-48 w-full" />
            <div className="bg-white rounded-xl h-64 w-full" />
          </div>
        </div>
      </div>
    );
  }

  const isCancelled = order.order_status === 'cancelled';
  const isRefunded = order.order_status === 'refunded';

  return (
    <div className="bg-gray-50 pb-12">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button onClick={() => navigate('/orders')} className="p-2 hover:bg-gray-100 rounded-lg" aria-label="Back to orders">
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-lg font-bold text-gray-900">{order.order_number}</h1>
                <p className="text-sm text-gray-500">{formatDate(order.created_at)}</p>
              </div>
            </div>

            {/* Invoice download */}
            <button
              onClick={() => downloadInvoice(id)}
              className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-700 bg-blue-50 px-3 py-2 rounded-lg transition"
            >
              <Download className="w-4 h-4" />
              Invoice
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* New order celebration banner */}
        {isNew && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-5 flex items-center gap-4">
            <CheckCircle2 className="w-10 h-10 text-green-500 flex-shrink-0" />
            <div>
              <h2 className="font-bold text-green-800 text-lg">Order Placed Successfully!</h2>
              <p className="text-sm text-green-600 mt-0.5">
                Thank you for your order. You will receive a confirmation email shortly.
              </p>
            </div>
          </div>
        )}

        {/* Progress Tracker (for active orders) */}
        {!isCancelled && !isRefunded && (
          <div className="bg-white rounded-xl border p-6">
            <h3 className="font-bold text-gray-900 mb-6">Order Progress</h3>
            <div className="relative">
              {/* Progress bar */}
              <div className="absolute top-5 left-6 right-6 h-1 bg-gray-200 rounded">
                <div
                  className="h-full bg-black rounded transition-all duration-500"
                  style={{ width: `${getProgress()}%` }}
                />
              </div>
              {/* Steps */}
              <div className="flex justify-between relative">
                {STATUS_STEPS.map((s, i) => {
                  const statusOrder = ['placed', 'confirmed', 'processing', 'shipped', 'delivered'];
                  const currentIdx = statusOrder.indexOf(order.order_status);
                  const isActive = i <= currentIdx;
                  const isCurrent = statusOrder[i] === order.order_status;
                  const Icon = s.icon;

                  return (
                    <div key={s.key} className="flex flex-col items-center z-10">
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center transition ${
                          isActive
                            ? isCurrent
                              ? 'bg-black text-white ring-4 ring-gray-200'
                              : 'bg-black text-white'
                            : 'bg-gray-100 text-gray-400'
                        }`}
                      >
                        <Icon className="w-5 h-5" />
                      </div>
                      <span
                        className={`text-xs mt-2 font-medium ${
                          isActive ? 'text-gray-900' : 'text-gray-400'
                        }`}
                      >
                        {s.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Cancelled/Refunded banner */}
        {(isCancelled || isRefunded) && (
          <div className={`rounded-xl border p-5 flex items-center gap-3 ${
            isCancelled ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200'
          }`}>
            <XCircle className={`w-8 h-8 ${isCancelled ? 'text-red-500' : 'text-gray-500'}`} />
            <div>
              <p className="font-bold text-gray-900">
                {isCancelled ? 'Order Cancelled' : 'Refund Processed'}
              </p>
              <p className="text-sm text-gray-600">
                {isCancelled
                  ? 'This order has been cancelled. Refund will be processed if payment was made.'
                  : 'Refund has been processed to your original payment method.'}
              </p>
            </div>
          </div>
        )}

        {/* Order Items */}
        <div className="bg-white rounded-xl border p-5">
          <h3 className="font-bold text-gray-900 mb-4">Items ({order.items?.length || 0})</h3>
          <div className="space-y-4">
            {(order.items || []).map((item) => (
              <div key={item.id} className="flex gap-4 pb-4 border-b last:border-0 last:pb-0">
                <div className="w-16 h-20 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                  <img
                    src={item.image_url_snapshot || '/placeholder-product.jpg'}
                    alt={item.product_title_snapshot}
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-gray-900 text-sm line-clamp-1">
                    {item.product_title_snapshot}
                  </h4>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {item.size_snapshot && `Size: ${item.size_snapshot}`}
                    {item.color_snapshot && ` • Color: ${item.color_snapshot}`}
                    {` • SKU: ${item.sku_snapshot}`}
                  </p>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-sm text-gray-600">
                      {formatPrice(item.unit_price)} × {item.quantity}
                    </span>
                    <span className="font-medium text-gray-900">{formatPrice(item.line_total)}</span>
                  </div>

                  {/* Return button (per item) */}
                  {canReturn && (
                    <button
                      onClick={() => setShowReturn(item.id)}
                      className="mt-2 text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1"
                    >
                      <RotateCcw className="w-3 h-3" />
                      Request Return
                    </button>
                  )}

                  {/* Return form */}
                  {showReturn === item.id && (
                    <div className="mt-3 p-3 bg-gray-50 rounded-lg border space-y-3">
                      <select
                        value={returnData.reason}
                        onChange={(e) => setReturnData((d) => ({ ...d, reason: e.target.value }))}
                        className="w-full border rounded-lg px-3 py-2 text-sm"
                      >
                        <option value="">Select reason</option>
                        {RETURN_REASONS.map((r) => <option key={r} value={r}>{r}</option>)}
                      </select>
                      <textarea
                        value={returnData.reason_detail}
                        onChange={(e) => setReturnData((d) => ({ ...d, reason_detail: e.target.value }))}
                        placeholder="Additional details (optional)"
                        rows={2}
                        className="w-full border rounded-lg px-3 py-2 text-sm"
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleReturn(item.id)}
                          disabled={actionLoading}
                          className="bg-black text-white px-4 py-2 rounded-lg text-sm disabled:opacity-50"
                        >
                          Submit Return
                        </button>
                        <button
                          onClick={() => setShowReturn(null)}
                          className="text-gray-500 px-3 py-2 text-sm"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Price Breakdown */}
        <div className="bg-white rounded-xl border p-5">
          <h3 className="font-bold text-gray-900 mb-4">Price Details</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between text-gray-600">
              <span>Subtotal</span>
              <span>{formatPrice(order.subtotal)}</span>
            </div>
            {order.cgst_amount > 0 && (
              <div className="flex justify-between text-gray-600">
                <span>CGST</span><span>{formatPrice(order.cgst_amount)}</span>
              </div>
            )}
            {order.sgst_amount > 0 && (
              <div className="flex justify-between text-gray-600">
                <span>SGST</span><span>{formatPrice(order.sgst_amount)}</span>
              </div>
            )}
            {order.igst_amount > 0 && (
              <div className="flex justify-between text-gray-600">
                <span>IGST</span><span>{formatPrice(order.igst_amount)}</span>
              </div>
            )}
            <div className="flex justify-between text-gray-600">
              <span>Shipping</span>
              <span>{order.shipping_fee ? formatPrice(order.shipping_fee) : 'FREE'}</span>
            </div>
            {order.discount_amount > 0 && (
              <div className="flex justify-between text-green-600">
                <span>Discount {order.coupon_code_snapshot && `(${order.coupon_code_snapshot})`}</span>
                <span>-{formatPrice(order.discount_amount)}</span>
              </div>
            )}
            <hr />
            <div className="flex justify-between font-bold text-base text-gray-900">
              <span>Total</span>
              <span>{formatPrice(order.grand_total)}</span>
            </div>
          </div>
        </div>

        {/* Shipping Address */}
        <div className="bg-white rounded-xl border p-5">
          <h3 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
            <MapPin className="w-4 h-4" />
            Shipping Address
          </h3>
          <p className="text-sm text-gray-600">
            <span className="font-medium text-gray-900">{order.shipping_name}</span><br />
            {order.shipping_address_text}<br />
            {order.shipping_city}, {order.shipping_state} — {order.shipping_postal_code}<br />
            {order.shipping_country}
          </p>
        </div>

        {/* Payment Info */}
        <div className="bg-white rounded-xl border p-5">
          <h3 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
            <CreditCard className="w-4 h-4" />
            Payment
          </h3>
          <div className="text-sm text-gray-600 space-y-1">
            <p>Method: <span className="font-medium text-gray-900 capitalize">{order.payment_method || order.payment_gateway}</span></p>
            <p>Status: <span className="font-medium text-gray-900 capitalize">{order.payment_status}</span></p>
            {order.payment_gateway_txn_id && (
              <p>Transaction: <span className="font-mono text-xs">{order.payment_gateway_txn_id}</span></p>
            )}
          </div>
        </div>

        {/* Timeline */}
        <div className="bg-white rounded-xl border p-5">
          <button
            onClick={() => setShowTimeline(!showTimeline)}
            className="w-full flex items-center justify-between"
          >
            <h3 className="font-bold text-gray-900 flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Order Timeline
            </h3>
            {showTimeline ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
          {showTimeline && timeline.length > 0 && (
            <div className="mt-4 space-y-3 ml-2">
              {timeline.map((entry, i) => (
                <div key={i} className="flex gap-3 relative">
                  <div className="flex flex-col items-center">
                    <div className={`w-3 h-3 rounded-full ${i === 0 ? 'bg-black' : 'bg-gray-300'}`} />
                    {i < timeline.length - 1 && <div className="w-px h-full bg-gray-200 mt-1" />}
                  </div>
                  <div className="pb-4">
                    <p className="text-sm font-medium text-gray-900 capitalize">
                      {entry.to_status?.replace(/_/g, ' ')}
                    </p>
                    <p className="text-xs text-gray-500">{formatDate(entry.created_at)}</p>
                    {entry.change_reason && (
                      <p className="text-xs text-gray-400 mt-0.5">{entry.change_reason}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Cancel Order */}
        {canCancel && (
          <div className="bg-white rounded-xl border p-5">
            {!showCancel ? (
              <button
                onClick={() => setShowCancel(true)}
                className="text-red-600 hover:text-red-700 text-sm font-medium flex items-center gap-1.5"
              >
                <XCircle className="w-4 h-4" />
                Cancel Order
              </button>
            ) : (
              <div className="space-y-3">
                <p className="text-sm font-medium text-gray-900">Why are you cancelling?</p>
                <select
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  className="w-full border rounded-lg px-3 py-2.5 text-sm"
                >
                  <option value="">Select reason</option>
                  {CANCEL_REASONS.map((r) => <option key={r} value={r}>{r}</option>)}
                </select>
                <div className="flex gap-2">
                  <button
                    onClick={handleCancel}
                    disabled={actionLoading}
                    className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-red-700 disabled:opacity-50"
                  >
                    Confirm Cancel
                  </button>
                  <button
                    onClick={() => setShowCancel(false)}
                    className="text-gray-500 px-3 py-2 text-sm"
                  >
                    Keep Order
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
