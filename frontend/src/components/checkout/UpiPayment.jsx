/**
 * UPI Payment Component - Phase 13G (Revised)
 *
 * Uses Razorpay Checkout.js in UPI-only mode.
 * Strategy 1: KEY_ID fetched from backend at payment time (never in frontend code/bundle/.env).
 *
 * Flow:
 *   1. POST /payments/upi/collect -> creates Razorpay order, returns razorpay_order_id
 *   2. GET  /payments/checkout-config -> returns { key_id } (authenticated only)
 *   3. Open Razorpay Checkout.js modal with UPI-only config
 *   4. On modal success -> POST /payments/razorpay/verify -> backend verifies HMAC signature
 *   5. On verification success -> onSuccess callback -> redirect to order confirmation
 *
 * Fallback: poll endpoint used if modal closes without explicit callback (mobile UPI app switch).
 *
 * File: frontend/src/components/checkout/UpiPayment.jsx
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { Loader2, CheckCircle, XCircle, Shield } from 'lucide-react';
import apiClient from '../../api/apiClient';
import toast from 'react-hot-toast';

const VPA_REGEX = /^[a-zA-Z0-9._-]+@[a-zA-Z]{2,}$/;

/**
 * Load Razorpay Checkout.js script dynamically.
 * Idempotent - will not load twice.
 */
function loadRazorpayScript() {
  return new Promise((resolve, reject) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }
    const existing = document.querySelector('script[src="https://checkout.razorpay.com/v1/checkout.js"]');
    if (existing) {
      existing.addEventListener('load', () => resolve(true));
      existing.addEventListener('error', () => reject(new Error('Razorpay script load failed')));
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    script.onload = () => resolve(true);
    script.onerror = () => reject(new Error('Razorpay script load failed'));
    document.body.appendChild(script);
  });
}

export default function UpiPayment({ orderId, onSuccess, onFailure }) {
  const [paymentMode, setPaymentMode] = useState('collect'); // collect | apps
  const [status, setStatus] = useState('idle'); // idle | loading | processing | success | failed
  const [errorMsg, setErrorMsg] = useState('');
  const [vpa, setVpa] = useState('');
  const [vpaError, setVpaError] = useState('');
  const [activeVpa, setActiveVpa] = useState('');
  const [processingMessage, setProcessingMessage] = useState(
    'Complete the payment in your UPI app if prompted.'
  );
  const pollRef = useRef(null);
  const pollCountRef = useRef(0);
  const statusRef = useRef('idle');

  // Keep statusRef in sync for use inside Razorpay callbacks
  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  /**
   * Fallback polling - used when Razorpay modal closes without
   * explicit success/failure callback (e.g. user switches to UPI app).
   * Polls for up to 5 minutes (100 polls x 3s).
   */
  const startFallbackPoll = useCallback(() => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollCountRef.current = 0;
    pollRef.current = setInterval(async () => {
      pollCountRef.current += 1;
      if (pollCountRef.current > 100) {
        clearInterval(pollRef.current);
        pollRef.current = null;
        setStatus('failed');
        setErrorMsg('Payment confirmation timed out. Check your order history.');
        onFailure?.('Payment timed out');
        return;
      }
      try {
        const res = await apiClient.get('/payments/' + orderId + '/upi-poll');
        const { payment_status } = res.data;
        if (payment_status === 'paid') {
          clearInterval(pollRef.current);
          pollRef.current = null;
          setStatus('success');
          toast.success('Payment successful!');
          onSuccess?.(res.data);
        } else if (payment_status === 'failed') {
          clearInterval(pollRef.current);
          pollRef.current = null;
          setStatus('failed');
          setErrorMsg('Payment failed. Please retry.');
          onFailure?.('Payment failed');
        }
      } catch (e) {
        // Silent - continue polling
      }
    }, 3000);
  }, [orderId, onSuccess, onFailure]);

  const validateVpa = useCallback((value) => {
    const trimmed = value.trim();
    if (!trimmed) {
      setVpaError('UPI ID is required');
      return false;
    }
    if (trimmed.length < 4 || trimmed.length > 50) {
      setVpaError('Invalid UPI ID');
      return false;
    }
    if (!VPA_REGEX.test(trimmed)) {
      setVpaError('Invalid UPI ID');
      return false;
    }
    setVpaError('');
    return true;
  }, []);

  const handleCollectPayment = async () => {
    if (!validateVpa(vpa)) {
      return;
    }

    setStatus('loading');
    setErrorMsg('');

    try {
      await apiClient.post('/payments/upi/collect', {
        order_id: orderId,
        vpa: vpa.trim(),
      });

      setActiveVpa(vpa.trim());
      setProcessingMessage('Approve the collect request in your UPI app.');
      setStatus('processing');
      startFallbackPoll();
    } catch (err) {
      setStatus('failed');
      const msg = err.message || 'Payment initiation failed';
      setErrorMsg(msg);
      toast.error(msg);
    }
  };

  /**
   * Main payment handler:
   * 1. Create Razorpay order via backend
   * 2. Fetch KEY_ID from backend (Strategy 1)
   * 3. Open Checkout.js modal in UPI-only mode
   * 4. On success -> verify signature via backend
   */
  const handlePayment = async () => {
    setStatus('loading');
    setErrorMsg('');

    try {
      // Step 1: Load Razorpay Checkout.js script
      await loadRazorpayScript();

      // Step 2: Create Razorpay order via backend (reuses existing endpoint)
      const collectRes = await apiClient.post('/payments/upi/collect', {
        order_id: orderId,
        vpa: 'checkout@razorpay',
      });
      const razorpayOrderId = collectRes.data.razorpay_order_id;

      if (!razorpayOrderId) {
        throw new Error('Failed to create payment order');
      }

      // Step 3: Fetch KEY_ID from backend (Strategy 1)
      const configRes = await apiClient.get('/payments/checkout-config');
      const keyId = configRes.data.key_id;

      if (!keyId) {
        throw new Error('Payment gateway configuration unavailable');
      }

      // Step 4: Open Razorpay Checkout.js modal - UPI only
      setStatus('processing');
      setActiveVpa('');
      setProcessingMessage('Complete the payment in your UPI app or scan the QR in the Razorpay window.');

      const options = {
        key: keyId,
        order_id: razorpayOrderId,
        method: 'upi',
        handler: async function (response) {
          // Step 5: Verify signature on backend
          try {
            const verifyRes = await apiClient.post('/payments/razorpay/verify', {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
              order_id: orderId,
            });

            if (verifyRes.data.verified || verifyRes.data.status === 'success') {
              if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
              setStatus('success');
              toast.success('Payment successful!');
              onSuccess?.(verifyRes.data);
            } else {
              setStatus('failed');
              setErrorMsg('Payment verification failed. Contact support if amount was debited.');
              onFailure?.('Verification failed');
            }
          } catch (verifyErr) {
            console.error('Verify API error, falling back to poll:', verifyErr);
            setStatus('processing');
            startFallbackPoll();
          }
        },
        modal: {
          ondismiss: function () {
            if (statusRef.current !== 'success') {
              setStatus('processing');
              startFallbackPoll();
            }
          },
          confirm_close: true,
          escape: false,
        },
        config: {
          display: {
            blocks: {
              upi: {
                name: 'Pay via UPI',
                instruments: [
                  { method: 'upi' },
                ],
              },
            },
            sequence: ['block.upi'],
            preferences: {
              show_default_blocks: false,
            },
          },
        },
        theme: {
          color: '#000000',
        },
      };

      const rzp = new window.Razorpay(options);

      rzp.on('payment.failed', function (response) {
        if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
        setStatus('failed');
        const reason = response.error?.description || 'Payment failed';
        setErrorMsg(reason);
        onFailure?.(reason);
      });

      rzp.open();

    } catch (err) {
      setStatus('failed');
      const msg = err.response?.data?.detail || err.message || 'Payment initiation failed';
      setErrorMsg(msg);
      toast.error(msg);
    }
  };

  const handleRetry = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
    setStatus('idle');
    setErrorMsg('');
  };

  // -- Success State --
  if (status === 'success') {
    return (
      <div className="text-center py-8 space-y-3">
        <CheckCircle className="w-16 h-16 text-green-500 mx-auto" />
        <p className="text-lg font-bold text-green-700">Payment Successful!</p>
        <p className="text-sm text-gray-500">Redirecting to your order...</p>
      </div>
    );
  }

  // -- Failed State --
  if (status === 'failed') {
    return (
      <div className="text-center py-8 space-y-4">
        <XCircle className="w-16 h-16 text-red-500 mx-auto" />
        <p className="text-lg font-bold text-red-700">Payment Failed</p>
        {errorMsg && <p className="text-sm text-gray-500">{errorMsg}</p>}
        <button
          onClick={handleRetry}
          className="px-6 py-2.5 bg-black text-white rounded-lg text-sm font-medium hover:bg-gray-800 transition"
        >
          Retry Payment
        </button>
      </div>
    );
  }

  // -- Processing State (waiting for UPI app / fallback polling) --
  if (status === 'processing') {
    return (
      <div className="text-center py-8 space-y-4">
        <Loader2 className="w-12 h-12 text-gray-400 mx-auto animate-spin" />
        <p className="text-base font-semibold text-gray-700">
          Waiting for payment confirmation...
        </p>
        <p className="text-sm text-gray-500">
          {processingMessage}
        </p>
        {activeVpa && (
          <p className="text-sm font-medium text-gray-700">{activeVpa}</p>
        )}
        <button
          onClick={() => {
            if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
            setStatus('failed');
            setErrorMsg('Payment cancelled');
            onFailure?.('Payment cancelled by user');
          }}
          className="text-sm text-gray-400 hover:text-gray-600 underline"
        >
          Cancel
        </button>
      </div>
    );
  }

  // -- Idle / Loading State --
  return (
    <div className="space-y-4">
      <div className="flex gap-2 rounded-xl bg-white p-1 border">
        <button
          type="button"
          onClick={() => setPaymentMode('collect')}
          className={`flex-1 rounded-lg px-4 py-2.5 text-sm font-medium transition ${
            paymentMode === 'collect'
              ? 'bg-black text-white'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          Enter UPI ID
        </button>
        <button
          type="button"
          onClick={() => setPaymentMode('apps')}
          className={`flex-1 rounded-lg px-4 py-2.5 text-sm font-medium transition ${
            paymentMode === 'apps'
              ? 'bg-black text-white'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          UPI Apps / Scan QR
        </button>
      </div>

      {paymentMode === 'collect' ? (
        <div className="space-y-3">
          <div>
            <label htmlFor="upi-vpa" className="block text-sm font-medium text-gray-700 mb-1.5">
              UPI ID
            </label>
            <input
              id="upi-vpa"
              type="text"
              value={vpa}
              onChange={(e) => {
                setVpa(e.target.value);
                if (vpaError) {
                  validateVpa(e.target.value);
                }
              }}
              onBlur={() => {
                if (vpa) {
                  validateVpa(vpa);
                }
              }}
              placeholder="yourname@paytm"
              className={`w-full rounded-lg border px-4 py-3 text-sm outline-none transition ${
                vpaError ? 'border-red-300 bg-red-50' : 'border-gray-300 focus:border-black'
              }`}
              aria-invalid={!!vpaError}
              aria-describedby={vpaError ? 'upi-vpa-error' : 'upi-vpa-help'}
            />
            {vpaError ? (
              <p id="upi-vpa-error" className="mt-1.5 text-sm text-red-600">
                {vpaError}
              </p>
            ) : (
              <p id="upi-vpa-help" className="mt-1.5 text-xs text-gray-500">
                In Razorpay test mode you can still use test VPAs like <span className="font-medium">success@razorpay</span>.
              </p>
            )}
          </div>

          <button
            onClick={handleCollectPayment}
            disabled={status === 'loading'}
            className="w-full bg-black text-white py-3 rounded-lg font-semibold text-sm hover:bg-gray-800 transition disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {status === 'loading' ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Initiating Payment...
              </>
            ) : (
              'Pay via UPI ID'
            )}
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-gray-600">
            Open Razorpay Checkout to pay with any supported UPI app or scan the QR code.
          </p>
          <button
            onClick={handlePayment}
            disabled={status === 'loading'}
            className="w-full bg-black text-white py-3 rounded-lg font-semibold text-sm hover:bg-gray-800 transition disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {status === 'loading' ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Initiating Payment...
              </>
            ) : (
              'Pay via UPI Apps / QR'
            )}
          </button>
        </div>
      )}

      <div className="flex items-center justify-center gap-2 text-xs text-gray-400">
        <Shield className="w-3.5 h-3.5" />
        <span>Secured by Razorpay. Your UPI ID is never stored.</span>
      </div>
    </div>
  );
}
