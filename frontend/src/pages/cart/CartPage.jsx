/**
 * CartPage -- Shopping cart with quantities, coupon, subtotal, stock check.
 * Field mapping: all item fields from backend CartItemResponse schema (cart_coupon.py)
 */
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShoppingBag, Minus, Plus, X, Tag, Truck, Shield, ArrowLeft, Trash2, AlertTriangle } from 'lucide-react';
import useCartStore from '../../stores/cartStore';
import useAuthStore from '../../stores/authStore';
import toast from 'react-hot-toast';
import apiClient from '../../api/apiClient';

export default function CartPage() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const {
    items, loading, error, coupon, couponDiscount,
    fetchCart, updateQuantity, removeItem, clearCart,
    applyCoupon, removeCoupon, getSubtotal, clearError,
  } = useCartStore();
  const [couponCode, setCouponCode] = useState('');
  const [couponLoading, setCouponLoading] = useState(false);
  const isAuth = !!user;

  useEffect(() => {
    if (isAuth) fetchCart();
  }, [isAuth]);

  useEffect(() => {
    if (error) {
      toast.error(error);
      clearError();
    }
  }, [error]);

  const subtotal = getSubtotal();
  // Shipping config from store_settings (admin-configurable via API)
  const [shippingFee, setShippingFee] = useState(0);
  const [shippingThreshold, setShippingThreshold] = useState(0);
  const [shippingLoaded, setShippingLoaded] = useState(false);
  useEffect(() => {
    apiClient.get('/catalog/shipping-config')
      .then(res => {
        setShippingFee(Number(res.data.shipping_fee));
        setShippingThreshold(Number(res.data.free_shipping_threshold));
        setShippingLoaded(true);
      })
      .catch(() => {
        setShippingLoaded(true);
      });
  }, []);
  const shipping = shippingLoaded && shippingThreshold > 0 && subtotal >= shippingThreshold ? 0 : shippingFee;
  const discount = couponDiscount || 0;
  const total = subtotal + shipping - discount;

  const handleQty = (variantId, currentQty, delta) => {
    const newQty = currentQty + delta;
    if (newQty < 1) return;
    if (newQty > 10) {
      toast.error('Maximum 10 per item');
      return;
    }
    updateQuantity(variantId, newQty, isAuth);
  };

  const handleApplyCoupon = async () => {
    if (!couponCode.trim()) return;
    setCouponLoading(true);
    const result = await applyCoupon(couponCode.trim());
    setCouponLoading(false);
    if (result.success) {
      toast.success(`Coupon applied! You save \u20B9${result.discount}`);
    } else {
      toast.error(result.error);
    }
  };

  const handleCheckout = () => {
    if (!isAuth) {
      navigate('/login?next=/checkout');
      return;
    }
    if (items.length === 0) {
      toast.error('Cart is empty');
      return;
    }
    navigate('/checkout');
  };

  const formatPrice = (price) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(price || 0);

  if (loading) {
    return (
      <div className="bg-gray-50 pt-8 pb-12">
        <div className="max-w-6xl mx-auto px-4">
          <div className="animate-pulse space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-xl h-28 w-full" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-50 pb-12">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 rounded-lg" aria-label="Go back">
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Shopping Cart</h1>
                <p className="text-sm text-gray-500 mt-1">
                  {items.length} {items.length === 1 ? 'item' : 'items'}
                </p>
              </div>
            </div>
            {items.length > 0 && (
              <button
                onClick={() => clearCart(isAuth)}
                className="text-sm text-red-600 hover:text-red-700 flex items-center gap-1"
              >
                <Trash2 className="w-4 h-4" />
                Clear Cart
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {items.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-2xl border">
            <ShoppingBag className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-700 mb-2">Your cart is empty</h2>
            <p className="text-gray-500 mb-6">Add items to get started.</p>
            <Link
              to="/shop"
              className="inline-flex items-center gap-2 bg-black text-white px-6 py-3 rounded-lg hover:bg-gray-800 transition"
            >
              Continue Shopping
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Cart Items */}
            <div className="lg:col-span-2 space-y-4">
              {items.map((item) => {
                const lowStock = item.stock_quantity != null && item.stock_quantity > 0 && item.stock_quantity <= 5;

                return (
                  <div
                    key={item.variant_id}
                    className="bg-white rounded-xl border p-4 flex gap-4 hover:shadow-sm transition"
                  >
                    {/* Image */}
                    <Link
                      to={item.product_slug ? `/products/${item.product_slug}` : '#'}
                      className="w-24 h-28 sm:w-28 sm:h-32 flex-shrink-0 rounded-lg overflow-hidden bg-gray-100"
                    >
                      {item.image_url ? (
                        <img
                          src={item.image_url}
                          alt={item.product_title || ''}
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <ShoppingBag className="w-8 h-8 text-gray-300" />
                        </div>
                      )}
                    </Link>

                    {/* Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-start">
                        <div>
                          {item.brand && (
                            <p className="text-xs text-gray-400 uppercase tracking-wider">
                              {item.brand}
                            </p>
                          )}
                          <h3 className="font-medium text-gray-900 text-sm mt-0.5 line-clamp-2">
                            {item.product_title}
                          </h3>
                          <div className="flex flex-wrap gap-2 mt-1.5">
                            {item.size && (
                              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                                Size: {item.size}
                              </span>
                            )}
                            {item.color && (
                              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                                Color: {item.color}
                              </span>
                            )}
                          </div>
                        </div>
                        <button
                          onClick={() => removeItem(item.variant_id, isAuth)}
                          className="p-1.5 hover:bg-red-50 rounded-lg text-gray-400 hover:text-red-500 transition"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>

                      {/* Low stock warning */}
                      {lowStock && (
                        <div className="flex items-center gap-1 mt-2 text-amber-600">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          <span className="text-xs font-medium">Only {item.stock_quantity} left</span>
                        </div>
                      )}

                      {/* Price + Quantity */}
                      <div className="flex items-center justify-between mt-3">
                        <div className="flex items-center border rounded-lg">
                          <button
                            onClick={() => handleQty(item.variant_id, item.quantity, -1)}
                            disabled={item.quantity <= 1}
                            className="p-2 hover:bg-gray-50 disabled:opacity-30 transition"
                          >
                            <Minus className="w-3.5 h-3.5" />
                          </button>
                          <span className="w-10 text-center text-sm font-medium">
                            {item.quantity}
                          </span>
                          <button
                            onClick={() => handleQty(item.variant_id, item.quantity, 1)}
                            disabled={item.stock_quantity != null && item.quantity >= Math.min(10, item.stock_quantity)}
                            className="p-2 hover:bg-gray-50 disabled:opacity-30 transition"
                          >
                            <Plus className="w-3.5 h-3.5" />
                          </button>
                        </div>
                        <p className="font-bold text-gray-900">
                          {formatPrice(item.line_total != null ? item.line_total : (item.unit_price || 0) * item.quantity)}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Order Summary */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-xl border p-6 sticky top-24 space-y-5">
                <h2 className="font-bold text-lg text-gray-900">Order Summary</h2>

                {/* Coupon */}
                {coupon ? (
                  <div className="flex items-center justify-between bg-green-50 border border-green-200 rounded-lg px-3 py-2">
                    <div className="flex items-center gap-2">
                      <Tag className="w-4 h-4 text-green-600" />
                      <span className="text-sm font-medium text-green-700">{coupon.code}</span>
                    </div>
                    <button
                      onClick={removeCoupon}
                      className="text-xs text-green-600 hover:text-green-800"
                    >
                      Remove
                    </button>
                  </div>
                ) : (
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={couponCode}
                      onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                      placeholder="Coupon code"
                      className="flex-1 border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-black focus:border-transparent outline-none"
                      onKeyDown={(e) => e.key === 'Enter' && handleApplyCoupon()}
                    />
                    <button
                      onClick={handleApplyCoupon}
                      disabled={couponLoading}
                      className="bg-gray-100 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg hover:bg-gray-200 transition disabled:opacity-50"
                    >
                      Apply
                    </button>
                  </div>
                )}

                {/* Breakdown */}
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between text-gray-600">
                    <span>Subtotal ({items.length} items)</span>
                    <span>{formatPrice(subtotal)}</span>
                  </div>
                  <div className="flex justify-between text-gray-600">
                    <span className="flex items-center gap-1">
                      <Truck className="w-3.5 h-3.5" />
                      Shipping
                    </span>
                    <span className={shipping === 0 ? 'text-green-600 font-medium' : ''}>
                      {shipping === 0 ? 'FREE' : formatPrice(shipping)}
                    </span>
                  </div>
                  {discount > 0 && (
                    <div className="flex justify-between text-green-600">
                      <span>Discount</span>
                      <span>-{formatPrice(discount)}</span>
                    </div>
                  )}
                  {shipping > 0 && shippingThreshold > 0 && (
                    <p className="text-xs text-gray-400">
                      {`Free shipping on orders above \u20B9${shippingThreshold.toLocaleString('en-IN')}`}
                    </p>
                  )}
                  <hr />
                  <div className="flex justify-between text-base font-bold text-gray-900">
                    <span>Total</span>
                    <span>{formatPrice(total)}</span>
                  </div>
                  <p className="text-xs text-gray-400">Tax included. Calculated at checkout.</p>
                </div>

                {/* Checkout Button */}
                <button
                  onClick={handleCheckout}
                  className="w-full bg-black text-white py-3.5 rounded-lg font-semibold hover:bg-gray-800 transition flex items-center justify-center gap-2"
                >
                  {isAuth ? 'Proceed to Checkout' : 'Login to Checkout'}
                </button>

                {/* Trust badges */}
                <div className="flex items-center justify-center gap-4 pt-2 text-gray-400">
                  <div className="flex items-center gap-1 text-xs">
                    <Shield className="w-3.5 h-3.5" />
                    Secure
                  </div>
                  <div className="flex items-center gap-1 text-xs">
                    <Truck className="w-3.5 h-3.5" />
                    Fast Delivery
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
