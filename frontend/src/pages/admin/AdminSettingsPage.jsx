/**
 * AdminSettingsPage.jsx - Phase 13H + Shipping Config + Seller Config
 * Admin Store Settings:
 *  1. Seller / Business Configuration (name, GSTIN, address, state, state code)
 *  2. Shipping Configuration (fee + free shipping threshold)
 *  3. Payment Configuration (Merchant UPI VPA)
 *  4. UPI VPA Change Audit Trail
 */

import { useState, useEffect } from 'react';
import { useSettingsStore } from '../../stores/adminStores';
import useAuthStore from '../../stores/authStore';
import apiClient from '../../api/apiClient';
import toast from 'react-hot-toast';

const VPA_REGEX = /^[a-zA-Z0-9._-]+@[a-zA-Z]{2,}$/;
const GSTIN_REGEX = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/;

const INDIAN_STATES = [
  { code: '01', name: 'Jammu & Kashmir' },
  { code: '02', name: 'Himachal Pradesh' },
  { code: '03', name: 'Punjab' },
  { code: '04', name: 'Chandigarh' },
  { code: '05', name: 'Uttarakhand' },
  { code: '06', name: 'Haryana' },
  { code: '07', name: 'Delhi' },
  { code: '08', name: 'Rajasthan' },
  { code: '09', name: 'Uttar Pradesh' },
  { code: '10', name: 'Bihar' },
  { code: '11', name: 'Sikkim' },
  { code: '12', name: 'Arunachal Pradesh' },
  { code: '13', name: 'Nagaland' },
  { code: '14', name: 'Manipur' },
  { code: '15', name: 'Mizoram' },
  { code: '16', name: 'Tripura' },
  { code: '17', name: 'Meghalaya' },
  { code: '18', name: 'Assam' },
  { code: '19', name: 'West Bengal' },
  { code: '20', name: 'Jharkhand' },
  { code: '21', name: 'Odisha' },
  { code: '22', name: 'Chhattisgarh' },
  { code: '23', name: 'Madhya Pradesh' },
  { code: '24', name: 'Gujarat' },
  { code: '26', name: 'Dadra & Nagar Haveli and Daman & Diu' },
  { code: '27', name: 'Maharashtra' },
  { code: '28', name: 'Andhra Pradesh (Old)' },
  { code: '29', name: 'Karnataka' },
  { code: '30', name: 'Goa' },
  { code: '31', name: 'Lakshadweep' },
  { code: '32', name: 'Kerala' },
  { code: '33', name: 'Tamil Nadu' },
  { code: '34', name: 'Puducherry' },
  { code: '35', name: 'Andaman & Nicobar Islands' },
  { code: '36', name: 'Telangana' },
  { code: '37', name: 'Andhra Pradesh' },
  { code: '38', name: 'Ladakh' },
];

export default function AdminSettingsPage() {
  const { upiConfig, upiAudit, loading, error, fetchUpiConfig, updateUpiConfig, fetchUpiAudit } =
    useSettingsStore();
  const user = useAuthStore((s) => s.user);

  const [newVpa, setNewVpa] = useState('');
  const [vpaError, setVpaError] = useState('');
  const [showConfirm, setShowConfirm] = useState(false);
  const [updating, setUpdating] = useState(false);

  // Shipping config state
  const [shippingFee, setShippingFee] = useState('');
  const [shippingThreshold, setShippingThreshold] = useState('');
  const [shippingLoading, setShippingLoading] = useState(false);
  const [shippingError, setShippingError] = useState('');
  const [shippingFetching, setShippingFetching] = useState(true);

  // Seller config state
  const [sellerName, setSellerName] = useState('');
  const [sellerGstin, setSellerGstin] = useState('');
  const [sellerAddress, setSellerAddress] = useState('');
  const [sellerState, setSellerState] = useState('');
  const [sellerStateCode, setSellerStateCode] = useState('');
  const [sellerLoading, setSellerLoading] = useState(false);
  const [sellerError, setSellerError] = useState('');
  const [sellerFetching, setSellerFetching] = useState(true);

  useEffect(() => {
    fetchUpiConfig();
    fetchUpiAudit();
  }, [fetchUpiConfig, fetchUpiAudit]);

  // Fetch current shipping config on mount
  useEffect(() => {
    const fetchShipping = async () => {
      try {
        const res = await fetch('/api/v1/catalog/shipping-config');
        if (res.ok) {
          const data = await res.json();
          setShippingFee(String(data.shipping_fee ?? ''));
          setShippingThreshold(String(data.free_shipping_threshold ?? ''));
        }
      } catch {
        // Silent fail - fields stay empty, user can still set values
      } finally {
        setShippingFetching(false);
      }
    };
    fetchShipping();
  }, []);

  // Fetch current seller config on mount
  useEffect(() => {
    const fetchSeller = async () => {
      try {
        const res = await apiClient.get('/admin/settings/seller');
        const data = res.data;
        setSellerName(data.seller_name ?? '');
        setSellerGstin(data.seller_gstin ?? '');
        setSellerAddress(data.seller_address ?? '');
        setSellerState(data.seller_state ?? '');
        setSellerStateCode(data.seller_state_code ?? '');
      } catch {
        // Silent fail - fields stay empty
      } finally {
        setSellerFetching(false);
      }
    };
    fetchSeller();
  }, []);

  // Check admin role
  const isAdmin = user?.role === 'admin';

  // Auto-sync state code when state dropdown changes
  const handleSellerStateChange = (e) => {
    const selectedName = e.target.value;
    setSellerState(selectedName);
    const match = INDIAN_STATES.find((s) => s.name === selectedName);
    if (match) {
      setSellerStateCode(match.code);
    }
  };

  const validateVpa = (value) => {
    if (!value || !value.trim()) {
      setVpaError('UPI VPA is required');
      return false;
    }
    if (value.length < 4 || value.length > 50) {
      setVpaError('VPA must be between 4 and 50 characters');
      return false;
    }
    if (!VPA_REGEX.test(value.trim())) {
      setVpaError('Invalid format. Expected: username@bankhandle (e.g., ashmistore@razorpay)');
      return false;
    }
    if (upiConfig?.merchant_upi_vpa && value.trim() === upiConfig.merchant_upi_vpa) {
      setVpaError('New VPA is the same as the current one');
      return false;
    }
    setVpaError('');
    return true;
  };

  const handleSubmitClick = () => {
    if (!validateVpa(newVpa)) return;
    setShowConfirm(true);
  };

  const handleConfirmUpdate = async () => {
    setShowConfirm(false);
    setUpdating(true);
    try {
      const result = await updateUpiConfig(newVpa.trim());
      toast.success(result.message || 'Merchant UPI VPA updated successfully');
      setNewVpa('');
      setVpaError('');
      fetchUpiConfig();
      fetchUpiAudit();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to update UPI VPA';
      toast.error(msg);
    } finally {
      setUpdating(false);
    }
  };

  const handleShippingUpdate = async () => {
    setShippingError('');
    const fee = parseFloat(shippingFee);
    const threshold = parseFloat(shippingThreshold);
    if (isNaN(fee) || fee < 0) {
      setShippingError('Shipping fee must be a non-negative number');
      return;
    }
    if (isNaN(threshold) || threshold < 0) {
      setShippingError('Free shipping threshold must be a non-negative number');
      return;
    }
    setShippingLoading(true);
    try {
      const res = await fetch('/api/v1/admin/settings/shipping', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ shipping_fee: fee, free_shipping_threshold: threshold }),
      });
      if (res.ok) {
        toast.success('Shipping configuration updated');
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed to update shipping config');
      }
    } catch {
      toast.error('Network error');
    } finally {
      setShippingLoading(false);
    }
  };

  const handleSellerUpdate = async () => {
    setSellerError('');
    // Validate
    if (!sellerName.trim()) {
      setSellerError('Seller name is required');
      return;
    }
    if (!sellerGstin.trim()) {
      setSellerError('Seller GSTIN is required');
      return;
    }
    if (sellerGstin.trim().length !== 15) {
      setSellerError('GSTIN must be exactly 15 characters');
      return;
    }
    if (!GSTIN_REGEX.test(sellerGstin.trim())) {
      setSellerError('Invalid GSTIN format. Expected: 22AAAAA0000A1Z5');
      return;
    }
    if (!sellerAddress.trim()) {
      setSellerError('Seller address is required');
      return;
    }
    if (!sellerState.trim()) {
      setSellerError('Seller state is required');
      return;
    }
    if (!sellerStateCode.trim()) {
      setSellerError('Seller state code is required');
      return;
    }
    setSellerLoading(true);
    try {
      const res = await apiClient.put('/admin/settings/seller', {
        seller_name: sellerName.trim(),
        seller_gstin: sellerGstin.trim(),
        seller_address: sellerAddress.trim(),
        seller_state: sellerState.trim(),
        seller_state_code: sellerStateCode.trim(),
      });
      toast.success(res.data?.message || 'Seller configuration updated');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to update seller config';
      toast.error(msg);
    } finally {
      setSellerLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '\u2014';
    try {
      return new Date(dateStr).toLocaleString('en-IN', {
        dateStyle: 'medium',
        timeStyle: 'short',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="space-y-8 max-w-4xl">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
      </div>

      {/* ───── Seller / Business Configuration ───── */}
      <section
        className="bg-white rounded-lg border border-gray-200 overflow-hidden"
        aria-labelledby="seller-config-heading"
      >
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <h2 id="seller-config-heading" className="text-lg font-semibold text-gray-900">
            Seller / Business Configuration
          </h2>
          <p className="text-sm text-gray-500 mt-0.5">
            Originating state, GSTIN, and address used on invoices and for GST tax calculation
          </p>
        </div>

        <div className="p-6 space-y-5">
          {sellerFetching ? (
            <div className="space-y-3">
              <div className="h-10 w-full bg-gray-100 rounded animate-pulse" />
              <div className="h-10 w-full bg-gray-100 rounded animate-pulse" />
              <div className="h-20 w-full bg-gray-100 rounded animate-pulse" />
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {/* Seller Name */}
                <div>
                  <label
                    htmlFor="seller-name"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Seller Name
                  </label>
                  <input
                    id="seller-name"
                    type="text"
                    value={sellerName}
                    onChange={(e) => setSellerName(e.target.value)}
                    placeholder="e.g., YourStore Pvt Ltd"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    aria-label="Seller business name"
                    disabled={sellerLoading || !isAdmin}
                    maxLength={100}
                  />
                </div>

                {/* Seller GSTIN */}
                <div>
                  <label
                    htmlFor="seller-gstin"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Seller GSTIN
                  </label>
                  <input
                    id="seller-gstin"
                    type="text"
                    value={sellerGstin}
                    onChange={(e) => setSellerGstin(e.target.value.toUpperCase())}
                    placeholder="e.g., 19AAACR0000A1Z5"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono
                      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    aria-label="Seller GSTIN number"
                    disabled={sellerLoading || !isAdmin}
                    maxLength={15}
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    15-character GST Identification Number
                  </p>
                </div>
              </div>

              {/* Seller Address */}
              <div>
                <label
                  htmlFor="seller-address"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Seller Address
                </label>
                <textarea
                  id="seller-address"
                  value={sellerAddress}
                  onChange={(e) => setSellerAddress(e.target.value)}
                  placeholder="e.g., 123 Commerce Street, Kolkata, West Bengal 700001"
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  aria-label="Seller business address"
                  disabled={sellerLoading || !isAdmin}
                  maxLength={300}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {/* Seller State (dropdown) */}
                <div>
                  <label
                    htmlFor="seller-state"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Seller State
                  </label>
                  <select
                    id="seller-state"
                    value={sellerState}
                    onChange={handleSellerStateChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    aria-label="Seller originating state"
                    disabled={sellerLoading || !isAdmin}
                  >
                    <option value="">Select state...</option>
                    {INDIAN_STATES.map((s) => (
                      <option key={s.code} value={s.name}>
                        {s.name} ({s.code})
                      </option>
                    ))}
                  </select>
                  <p className="mt-1 text-xs text-gray-500">
                    Determines intra-state (CGST+SGST) vs inter-state (IGST) tax on orders
                  </p>
                </div>

                {/* Seller State Code (auto-filled, read-only) */}
                <div>
                  <label
                    htmlFor="seller-state-code"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    State Code
                  </label>
                  <input
                    id="seller-state-code"
                    type="text"
                    value={sellerStateCode}
                    readOnly
                    className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm bg-gray-50 font-mono
                      text-gray-600"
                    aria-label="Seller state code (auto-filled from state selection)"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Auto-filled from state selection
                  </p>
                </div>
              </div>

              {sellerError && (
                <div className="rounded-md bg-red-50 border border-red-200 p-3">
                  <p className="text-sm text-red-700" role="alert">{sellerError}</p>
                </div>
              )}

              {isAdmin && (
                <div>
                  <button
                    onClick={handleSellerUpdate}
                    disabled={sellerLoading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium
                      hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                      disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    aria-label="Save seller configuration"
                  >
                    {sellerLoading ? (
                      <span className="flex items-center gap-2">
                        <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.4 0 0 5.4 0 12h4z" />
                        </svg>
                        Saving...
                      </span>
                    ) : (
                      'Save Seller Config'
                    )}
                  </button>
                </div>
              )}

              {!isAdmin && (
                <div className="rounded-md bg-amber-50 border border-amber-200 p-3">
                  <p className="text-sm text-amber-700">
                    Only admin can modify seller configuration.
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </section>

      {/* ───── Shipping Configuration ───── */}
      <section
        className="bg-white rounded-lg border border-gray-200 overflow-hidden"
        aria-labelledby="shipping-config-heading"
      >
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <h2 id="shipping-config-heading" className="text-lg font-semibold text-gray-900">
            Shipping Configuration
          </h2>
          <p className="text-sm text-gray-500 mt-0.5">
            Standard shipping fee and free shipping threshold for all orders
          </p>
        </div>

        <div className="p-6 space-y-5">
          {shippingFetching ? (
            <div className="flex gap-6">
              <div className="h-10 w-48 bg-gray-100 rounded animate-pulse" />
              <div className="h-10 w-48 bg-gray-100 rounded animate-pulse" />
            </div>
          ) : (
            <>
              <div className="flex flex-wrap items-start gap-6">
                <div className="flex-1 min-w-[200px] max-w-xs">
                  <label
                    htmlFor="shipping-fee"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Shipping Fee (&#8377;)
                  </label>
                  <input
                    id="shipping-fee"
                    type="number"
                    min="0"
                    step="0.01"
                    value={shippingFee}
                    onChange={(e) => setShippingFee(e.target.value)}
                    placeholder="e.g., 79"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    aria-label="Shipping fee amount in rupees"
                    disabled={shippingLoading || !isAdmin}
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Charged on orders below the free shipping threshold
                  </p>
                </div>

                <div className="flex-1 min-w-[200px] max-w-xs">
                  <label
                    htmlFor="shipping-threshold"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Free Shipping Above (&#8377;)
                  </label>
                  <input
                    id="shipping-threshold"
                    type="number"
                    min="0"
                    step="0.01"
                    value={shippingThreshold}
                    onChange={(e) => setShippingThreshold(e.target.value)}
                    placeholder="e.g., 999"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    aria-label="Minimum order amount for free shipping in rupees"
                    disabled={shippingLoading || !isAdmin}
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Orders above this amount get free shipping
                  </p>
                </div>
              </div>

              {shippingError && (
                <div className="rounded-md bg-red-50 border border-red-200 p-3">
                  <p className="text-sm text-red-700" role="alert">{shippingError}</p>
                </div>
              )}

              {isAdmin && (
                <div>
                  <button
                    onClick={handleShippingUpdate}
                    disabled={shippingLoading || !shippingFee || !shippingThreshold}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium
                      hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                      disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    aria-label="Save shipping configuration"
                  >
                    {shippingLoading ? (
                      <span className="flex items-center gap-2">
                        <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.4 0 0 5.4 0 12h4z" />
                        </svg>
                        Saving...
                      </span>
                    ) : (
                      'Save Shipping Config'
                    )}
                  </button>
                </div>
              )}

              {!isAdmin && (
                <div className="rounded-md bg-amber-50 border border-amber-200 p-3">
                  <p className="text-sm text-amber-700">
                    Only admin can modify shipping configuration.
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </section>

      {/* ───── Payment Configuration ───── */}
      <section
        className="bg-white rounded-lg border border-gray-200 overflow-hidden"
        aria-labelledby="upi-config-heading"
      >
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <h2 id="upi-config-heading" className="text-lg font-semibold text-gray-900">
            Payment Configuration
          </h2>
          <p className="text-sm text-gray-500 mt-0.5">
            Merchant UPI Virtual Payment Address for customer payments
          </p>
        </div>

        <div className="p-6 space-y-6">
          {/* Current VPA Display */}
          <div className="flex items-start gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Current Merchant UPI VPA
              </label>
              {loading ? (
                <div className="h-10 w-64 bg-gray-100 rounded animate-pulse" />
              ) : (
                <div className="flex items-center gap-3">
                  <span
                    className={`text-lg font-mono px-3 py-1.5 rounded ${
                      upiConfig?.merchant_upi_vpa
                        ? 'bg-green-50 text-green-800 border border-green-200'
                        : 'bg-yellow-50 text-yellow-800 border border-yellow-200'
                    }`}
                  >
                    {upiConfig?.merchant_upi_vpa || 'Not configured'}
                  </span>
                  {upiConfig?.updated_at && (
                    <span className="text-xs text-gray-500">
                      Last updated: {formatDate(upiConfig.updated_at)}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>

          {error && (
            <div className="rounded-md bg-red-50 border border-red-200 p-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Update Form */}
          {isAdmin && (
            <div className="border-t border-gray-100 pt-6">
              <h3 className="text-sm font-semibold text-gray-800 mb-3">
                Update Merchant UPI VPA
              </h3>
              <div className="flex items-start gap-3">
                <div className="flex-1 max-w-md">
                  <input
                    type="text"
                    value={newVpa}
                    onChange={(e) => {
                      setNewVpa(e.target.value);
                      if (vpaError) validateVpa(e.target.value);
                    }}
                    onBlur={() => newVpa && validateVpa(newVpa)}
                    placeholder="e.g., ashmistore@razorpay"
                    className={`w-full px-3 py-2 border rounded-md font-mono text-sm
                      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                      ${vpaError ? 'border-red-300 bg-red-50' : 'border-gray-300'}`}
                    aria-label="New merchant UPI VPA"
                    aria-describedby={vpaError ? 'vpa-error' : undefined}
                    aria-invalid={!!vpaError}
                    maxLength={50}
                    disabled={updating}
                  />
                  {vpaError && (
                    <p id="vpa-error" className="mt-1 text-sm text-red-600" role="alert">
                      {vpaError}
                    </p>
                  )}
                  <p className="mt-1 text-xs text-gray-500">
                    Format: username@bankhandle &mdash; all future UPI payments will route to this address
                  </p>
                </div>
                <button
                  onClick={handleSubmitClick}
                  disabled={updating || !newVpa.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium
                    hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                    disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  aria-label="Update merchant UPI VPA"
                >
                  {updating ? (
                    <span className="flex items-center gap-2">
                      <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.4 0 0 5.4 0 12h4z" />
                      </svg>
                      Updating...
                    </span>
                  ) : (
                    'Update'
                  )}
                </button>
              </div>
            </div>
          )}

          {!isAdmin && (
            <div className="rounded-md bg-amber-50 border border-amber-200 p-3">
              <p className="text-sm text-amber-700">
                Only admin can modify payment configuration settings.
              </p>
            </div>
          )}
        </div>
      </section>

      {/* Confirmation Dialog */}
      {showConfirm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          role="dialog"
          aria-modal="true"
          aria-labelledby="confirm-title"
        >
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 overflow-hidden">
            <div className="px-6 py-4 bg-amber-50 border-b border-amber-200">
              <h3 id="confirm-title" className="text-lg font-semibold text-amber-900">
                Confirm UPI VPA Change
              </h3>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-sm text-gray-700">
                Changing the merchant UPI ID will route <strong>all future UPI payments</strong> to
                the new address. Existing completed payments are not affected.
              </p>
              <div className="bg-gray-50 rounded-md p-3 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Current:</span>
                  <span className="font-mono text-gray-700">
                    {upiConfig?.merchant_upi_vpa || '(not set)'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">New:</span>
                  <span className="font-mono text-blue-700 font-medium">{newVpa.trim()}</span>
                </div>
              </div>
            </div>
            <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 flex justify-end gap-3">
              <button
                onClick={() => setShowConfirm(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300
                  rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmUpdate}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md
                  hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Confirm Update
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ───── UPI VPA Audit Trail ───── */}
      <section
        className="bg-white rounded-lg border border-gray-200 overflow-hidden"
        aria-labelledby="audit-heading"
      >
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <h2 id="audit-heading" className="text-lg font-semibold text-gray-900">
            UPI VPA Change History
          </h2>
          <p className="text-sm text-gray-500 mt-0.5">Last 5 changes</p>
        </div>

        <div className="overflow-x-auto">
          {upiAudit.length === 0 ? (
            <div className="p-8 text-center text-gray-400 text-sm">
              No changes recorded yet
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Previous VPA
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wide">
                    &rarr;
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                    New VPA
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Changed By
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {upiAudit.map((entry) => (
                  <tr key={entry.id} className="hover:bg-gray-50/50">
                    <td className="px-6 py-3 text-gray-700 whitespace-nowrap">
                      {formatDate(entry.changed_at)}
                    </td>
                    <td className="px-6 py-3 font-mono text-gray-500">
                      {entry.old_value || '(not set)'}
                    </td>
                    <td className="px-6 py-3 text-center text-gray-300">&rarr;</td>
                    <td className="px-6 py-3 font-mono text-blue-700 font-medium">
                      {entry.new_value}
                    </td>
                    <td className="px-6 py-3 text-gray-500 whitespace-nowrap text-xs font-mono">
                      {entry.changed_by}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </div>
  );
}
