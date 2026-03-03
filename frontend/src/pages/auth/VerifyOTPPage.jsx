import { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';
import toast from 'react-hot-toast';
import Button from '@/components/common/Button';
import apiClient from '@/api/apiClient';

export default function VerifyOTPPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const email = location.state?.email || '';

  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [countdown, setCountdown] = useState(60);
  const [canResend, setCanResend] = useState(false);
  const inputRefs = useRef([]);

  // Redirect if no email in state
  useEffect(() => {
    if (!email) {
      navigate('/register');
    }
  }, [email, navigate]);

  // Countdown timer for resend
  useEffect(() => {
    if (countdown <= 0) {
      setCanResend(true);
      return;
    }
    const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
    return () => clearTimeout(timer);
  }, [countdown]);

  const handleChange = (index, value) => {
    // Only allow digits
    if (value && !/^\d$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    // Handle backspace - move to previous input
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (pasted.length === 6) {
      const newOtp = pasted.split('');
      setOtp(newOtp);
      inputRefs.current[5]?.focus();
    }
  };

  const handleVerify = async () => {
    const otpString = otp.join('');
    if (otpString.length !== 6) {
      toast.error('Please enter all 6 digits');
      return;
    }

    setLoading(true);
    try {
      await apiClient.post('/auth/verify-email', {
        email: email,
        otp: otpString,
      });
      toast.success('Email verified successfully!');
      navigate('/login', { state: { verified: true } });
    } catch (err) {
      const msg = err.response?.data?.detail || 'Verification failed. Please try again.';
      toast.error(msg);
      // Clear OTP on failure
      setOtp(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResendLoading(true);
    try {
      await apiClient.post('/auth/resend-otp', { email });
      toast.success('New OTP sent to your email');
      setCountdown(60);
      setCanResend(false);
      setOtp(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to resend OTP';
      toast.error(msg);
    } finally {
      setResendLoading(false);
    }
  };

  if (!email) return null;

  return (
    <>
      <div className="text-center mb-6">
        <div className="mx-auto w-14 h-14 rounded-full bg-green-50 flex items-center justify-center mb-4">
          <ShieldCheck className="w-7 h-7 text-green-600" />
        </div>
        <h1 className="font-display text-2xl mb-2">Verify Your Email</h1>
        <p className="text-sm text-ink-muted">
          We sent a 6-digit code to<br />
          <span className="font-medium text-ink-base">{email}</span>
        </p>
      </div>

      {/* OTP Input */}
      <div className="flex justify-center gap-2 mb-6" onPaste={handlePaste}>
        {otp.map((digit, index) => (
          <input
            key={index}
            ref={(el) => (inputRefs.current[index] = el)}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={digit}
            onChange={(e) => handleChange(index, e.target.value)}
            onKeyDown={(e) => handleKeyDown(index, e)}
            className="w-12 h-14 text-center text-xl font-bold border-2 border-ink-faint/30 rounded-lg
                       focus:border-brand-600 focus:ring-2 focus:ring-brand-500/20 outline-none
                       transition-colors"
            aria-label={`OTP digit ${index + 1}`}
          />
        ))}
      </div>

      <Button
        onClick={handleVerify}
        loading={loading}
        className="w-full mb-4"
        disabled={otp.join('').length !== 6}
      >
        Verify Email
      </Button>

      {/* Resend */}
      <div className="text-center text-sm">
        {canResend ? (
          <button
            onClick={handleResend}
            disabled={resendLoading}
            className="text-brand-600 hover:text-brand-700 font-medium disabled:opacity-50"
          >
            {resendLoading ? 'Sending...' : 'Resend OTP'}
          </button>
        ) : (
          <p className="text-ink-muted">
            Resend code in <span className="font-medium text-ink-base">{countdown}s</span>
          </p>
        )}
      </div>

      <p className="mt-6 text-center text-sm text-ink-muted">
        Wrong email?{' '}
        <Link to="/register" className="text-brand-600 hover:text-brand-700 font-medium">
          Go back
        </Link>
      </p>
    </>
  );
}
