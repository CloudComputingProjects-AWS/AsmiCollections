/**
 * CheckoutPage - Address selection, tax/GST breakdown, order placement.
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MapPin, CreditCard, ChevronRight, Plus, Shield, Truck,
  Package, CheckCircle, AlertCircle, ArrowLeft, Pencil,
} from 'lucide-react';
import useCartStore from '../../stores/cartStore';
import useAddressStore from '../../stores/addressStore';
import useAuthStore from '../../stores/authStore';
import apiClient from '../../api/apiClient';
import toast from 'react-hot-toast';
import AddressFormModal from '../../components/checkout/AddressFormModal';
import UpiPayment from '../../components/checkout/UpiPayment';

export default function CheckoutPage() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { items, coupon, couponDiscount, getSubtotal, clearCart } = useCartStore();
  const { addresses, fetchAddresses } = useAddressStore();

  const [selectedAddressId, setSelectedAddressId] = useState(null);
  const [showAddressModal, setShowAddressModal] = useState(false);
  const [editingAddress, setEditingAddress] = useState(null);
  const [orderSummary, setOrderSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [paymentMethod] = useState('upi');
  const [placedOrderId, setPlacedOrderId] = useState(null);
  const [step, setStep] = useState(1); // 1=address, 2=review, 3=payment
  const [shippingConfig, setShippingConfig] = useState({ shipping_fee: 0, free_shipping_threshold: 0 });

  // Fetch shipping config from API (dynamic, not hardcoded)
  useEffect(() => {
    apiClient.get('/catalog/shipping-config')
      .then((res) => setShippingConfig(res.data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!user) {
      navigate('/login?redirect=/checkout');
      return;
    }
    if (items.length === 0) {
      navigate('/cart');
      return;
    }
    fetchAddresses().catch((err) => {
      console.error('Address fetch failed:', err);
      toast.error('Failed to load saved addresses. Please try again.');
    });
  }, [user]);

  useEffect(() => {
    if (addresses.length > 0 && !selectedAddressId) {
      const def = addresses.find((a) => a.is_default) || addresses[0];
      setSelectedAddressId(def.id);
    }
  }, [addresses]);

  // Fetch order summary with tax calculation when address changes
  useEffect(() => {
    if (selectedAddressId && step >= 2) {
      fetchOrderSummary();
    }
  }, [selectedAddressId, step]);

  const fetchOrderSummary = async () => {
    setSummaryLoading(true);
    try {
      const res = await apiClient.post('/checkout/summary', {
        shipping_address_id: selectedAddressId,
        coupon_code: coupon?.code || null,
      });
      setOrderSummary(res.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to calculate order');
    }
    setSummaryLoading(false);
  };

  const formatPrice = (price) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(price || 0);

  const selectedAddress = addresses.find((a) => a.id === selectedAddressId);

  const openAddModal = () => {
    setEditingAddress(null);
    setShowAddressModal(true);
  };

  const openEditModal = (addr) => {
    setEditingAddress(addr);
    setShowAddressModal(true);
  };

  const handleAddressSaved = (addr) => {
    setSelectedAddressId(addr.id);
    setEditingAddress(null);
    setShowAddressModal(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-5xl mx-auto px-4 py-5">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate('/cart')} className="p-2 hover:bg-gray-100 rounded-lg" aria-label="Back to cart">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h1 className="text-xl font-bold text-gray-900">Checkout</h1>
          </div>

          {/* Steps */}
          <div className="flex items-center gap-2 mt-4 text-sm">
            {['Address', 'Review', 'Payment'].map((s, i) => (
              <div key={s} className="flex items-center gap-2">
                <button
                  onClick={() => i + 1 <= step && setStep(i + 1)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full transition ${
                    step === i + 1
                      ? 'bg-black text-white'
                      : step > i + 1
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-400'
                  }`}
                >
                  {step > i + 1 ? <CheckCircle className="w-4 h-4" /> : <span>{i + 1}</span>}
                  <span>{s}</span>
                </button>
                {i < 2 && <ChevronRight className="w-4 h-4 text-gray-300" />}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          {/* Left: Steps */}
          <div className="lg:col-span-3 space-y-6">
            {/* Step 1: Address */}
            {step === 1 && (
              <div className="bg-white rounded-xl border p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-bold text-gray-900 flex items-center gap-2">
                    <MapPin className="w-5 h-5" />
                    Shipping Address
                  </h2>
                </div>

                {addresses.length === 0 ? (
                  <div className="text-center py-8">
                    <MapPin className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500 mb-4">No saved addresses</p>
                    <button
                      onClick={openAddModal}
                      className="bg-black text-white px-5 py-2.5 rounded-lg text-sm font-medium flex items-center gap-2 mx-auto"
                    >
                      <Plus className="w-4 h-4" />
                      Add Address
                    </button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {addresses.map((addr) => (
                      <div
                        key={addr.id}
                        className={`p-4 border rounded-lg transition ${
                          selectedAddressId === addr.id
                            ? 'border-black bg-gray-50 ring-1 ring-black'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <label className="flex items-start gap-3 cursor-pointer">
                          <input
                            type="radio"
                            name="address"
                            checked={selectedAddressId === addr.id}
                            onChange={() => setSelectedAddressId(addr.id)}
                            className="mt-1 accent-black"
                          />
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-gray-900">
                                {addr.full_name || `${user?.first_name} ${user?.last_name}`}
                              </span>
                              <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded uppercase">
                                {addr.label}
                              </span>
                              {addr.is_default && (
                                <span className="text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded">
                                  Default
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-600 mt-1">
                              {addr.address_line_1}
                              {addr.address_line_2 ? `, ${addr.address_line_2}` : ''}
                            </p>
                            <p className="text-sm text-gray-600">
                              {addr.city}, {addr.state} {'\u2014'} {addr.postal_code}
                            </p>
                            {addr.phone && (
                              <p className="text-sm text-gray-500 mt-1">Phone: {addr.phone}</p>
                            )}
                          </div>
                        </label>
                        <div className="flex justify-end mt-2">
                          <button
                            type="button"
                            onClick={() => openEditModal(addr)}
                            className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1 px-2 py-1 rounded hover:bg-blue-50 transition"
                          >
                            <Pencil className="w-3.5 h-3.5" />
                            Edit
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}



                <button
                  onClick={() => setStep(2)}
                  disabled={!selectedAddressId}
                  className="w-full mt-6 bg-black text-white py-3 rounded-lg font-semibold hover:bg-gray-800 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  Continue to Review
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}

            {/* Step 2: Review Order */}
            {step === 2 && (
              <div className="space-y-6">
                {/* Selected Address Summary */}
                <div className="bg-white rounded-xl border p-5">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-bold text-gray-900 flex items-center gap-2">
                      <MapPin className="w-4 h-4" />
                      Delivering to
                    </h3>
                    <button
                      onClick={() => setStep(1)}
                      className="text-sm text-blue-600 hover:text-blue-700"
                    >
                      Change
                    </button>
                  </div>
                  {selectedAddress && (
                    <p className="text-sm text-gray-600">
                      <span className="font-medium text-gray-900">{selectedAddress.full_name}</span>
                      {' \u2014 '}
                      {selectedAddress.address_line_1}, {selectedAddress.city},{' '}
                      {selectedAddress.state} {selectedAddress.postal_code}
                    </p>
                  )}
                </div>

                {/* Items */}
                <div className="bg-white rounded-xl border p-5">
                  <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <Package className="w-4 h-4" />
                    Items ({items.length})
                  </h3>
                  <div className="space-y-3">
                    {items.map((item) => {
                      const product = item.product || {};
                      return (
                        <div key={item.id || item.product_variant_id} className="flex gap-3">
                          <div className="w-14 h-16 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                            <img
                              src={
                                item.image_url ||
                                product.images?.[0]?.thumbnail_url ||
                                '/placeholder-product.jpg'
                              }
                              alt=""
                              className="w-full h-full object-cover"
                            />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 line-clamp-1">
                              {item.product_title_snapshot || product.title}
                            </p>
                            <p className="text-xs text-gray-500">
                              {item.size_snapshot || item.size} / {item.color_snapshot || item.color} {'\u00D7'} {item.quantity}
                            </p>
                          </div>
                          <p className="text-sm font-medium text-gray-900">
                            {formatPrice((item.unit_price || product.sale_price || product.base_price || 0) * item.quantity)}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <button
                  onClick={() => {
                    fetchOrderSummary();
                    setStep(3);
                  }}
                  className="w-full bg-black text-white py-3 rounded-lg font-semibold hover:bg-gray-800 transition flex items-center justify-center gap-2"
                >
                  Continue to Payment
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}

            {/* Step 3: Payment */}
            {step === 3 && (
              <div className="bg-white rounded-xl border p-6">
                <h2 className="font-bold text-gray-900 flex items-center gap-2 mb-5">
                  <CreditCard className="w-5 h-5" />
                  Payment Method
                </h2>

                <div className="p-4 border border-black rounded-lg bg-gray-50 ring-1 ring-black">
                  <p className="font-medium text-gray-900 text-sm">UPI (Pay via UPI ID or QR)</p>
                  <p className="text-xs text-gray-500 mt-1">Instant payment via any UPI app</p>
                </div>

                {/* UPI: Place Order first, then show UPI component */}
                {paymentMethod === 'upi' && !placedOrderId && (
                  <button
                    onClick={async () => {
                      setLoading(true);
                      try {
                        const res = await apiClient.post('/checkout/place-order', {
                          shipping_address_id: selectedAddressId,
                          billing_address_id: selectedAddressId,
                          coupon_code: coupon?.code || null,
                          payment_method: 'upi',
                          payment_gateway: 'razorpay',
                        });
                        setPlacedOrderId(res.data.order_id || res.data.id);
                      } catch (err) {
                        toast.error(err.response?.data?.detail || 'Failed to place order');
                      }
                      setLoading(false);
                    }}
                    disabled={loading}
                    className="w-full mt-4 bg-black text-white py-3.5 rounded-lg font-bold text-base hover:bg-gray-800 transition disabled:opacity-50"
                  >
                    {loading ? 'Placing Order...' : `Place Order \u2014 ${formatPrice(orderSummary?.grand_total || getSubtotal())}`}
                  </button>
                )}

                {paymentMethod === 'upi' && placedOrderId && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
                    <UpiPayment
                      orderId={placedOrderId}
                      onSuccess={() => {
                        clearCart(true);
                        navigate(`/orders/${placedOrderId}?new=true`);
                      }}
                      onFailure={(msg) => toast.error(msg || 'UPI payment failed')}
                    />
                  </div>
                )}


              </div>
            )}
          </div>

          {/* Right: Summary Sidebar */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl border p-5 sticky top-24">
              <h3 className="font-bold text-gray-900 mb-4">Price Details</h3>

              {summaryLoading ? (
                <div className="animate-pulse space-y-3">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="h-4 bg-gray-100 rounded w-full" />
                  ))}
                </div>
              ) : orderSummary ? (
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between text-gray-600">
                    <span>Subtotal</span>
                    <span>{formatPrice(orderSummary.subtotal)}</span>
                  </div>
                  {orderSummary.cgst_amount > 0 && (
                    <div className="flex justify-between text-gray-600">
                      <span>CGST</span>
                      <span>{formatPrice(orderSummary.cgst_amount)}</span>
                    </div>
                  )}
                  {orderSummary.sgst_amount > 0 && (
                    <div className="flex justify-between text-gray-600">
                      <span>SGST</span>
                      <span>{formatPrice(orderSummary.sgst_amount)}</span>
                    </div>
                  )}
                  {orderSummary.igst_amount > 0 && (
                    <div className="flex justify-between text-gray-600">
                      <span>IGST</span>
                      <span>{formatPrice(orderSummary.igst_amount)}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-gray-600">
                    <span>Shipping</span>
                    <span className={!orderSummary.shipping_fee ? 'text-green-600 font-medium' : ''}>
                      {orderSummary.shipping_fee ? formatPrice(orderSummary.shipping_fee) : 'FREE'}
                    </span>
                  </div>
                  {orderSummary.discount_amount > 0 && (
                    <div className="flex justify-between text-green-600">
                      <span>Discount</span>
                      <span>-{formatPrice(orderSummary.discount_amount)}</span>
                    </div>
                  )}
                  <hr />
                  <div className="flex justify-between font-bold text-base text-gray-900">
                    <span>Total</span>
                    <span>{formatPrice(orderSummary.grand_total)}</span>
                  </div>
                  {orderSummary.supply_type && (
                    <p className="text-xs text-gray-400">
                      Supply: {orderSummary.supply_type === 'intra_state' ? 'Intra-state (CGST+SGST)' : 'Inter-state (IGST)'}
                    </p>
                  )}
                </div>
              ) : (
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between text-gray-600">
                    <span>Subtotal</span>
                    <span>{formatPrice(getSubtotal())}</span>
                  </div>
                  {couponDiscount > 0 && (
                    <div className="flex justify-between text-green-600">
                      <span>Discount</span>
                      <span>-{formatPrice(couponDiscount)}</span>
                    </div>
                  )}
                  <hr />
                  <div className="flex justify-between font-bold text-gray-900">
                    <span>Estimated Total</span>
                    <span>{formatPrice(getSubtotal() - couponDiscount)}</span>
                  </div>
                  <p className="text-xs text-gray-400">Tax calculated after selecting address.</p>
                </div>
              )}

              {/* Trust */}
              <div className="mt-5 pt-4 border-t space-y-2">
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Shield className="w-3.5 h-3.5 text-green-500" />
                  100% Secure Payments
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Truck className="w-3.5 h-3.5 text-blue-500" />
                  {shippingConfig.free_shipping_threshold > 0
                    ? `Free shipping on ${'\u20B9'}${Number(shippingConfig.free_shipping_threshold).toLocaleString('en-IN')}+`
                    : 'Free shipping on all orders'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Address Modal - supports both Add and Edit */}
      {showAddressModal && (
        <AddressFormModal
          address={editingAddress}
          onClose={() => { setShowAddressModal(false); setEditingAddress(null); }}
          onSaved={handleAddressSaved}
        />
      )}
    </div>
  );
}