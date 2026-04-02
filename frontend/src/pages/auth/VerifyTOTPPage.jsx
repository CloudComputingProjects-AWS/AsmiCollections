import { useEffect, useMemo, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import useAuthStore, { ADMIN_ROLES, ROLE_DEFAULT_ROUTE } from '../../stores/authStore';

export default function VerifyTOTPPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const completeTwoFactorLogin = useAuthStore((s) => s.completeTwoFactorLogin);
  const user = useAuthStore((s) => s.user);

  const loginState = location.state ?? {};
  const userId = loginState.userId ?? '';
  const email = loginState.email ?? '';
  const next = loginState.next ?? null;

  const [code, setCode] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const maskedEmail = useMemo(() => {
    if (!email || !email.includes('@')) return '';
    const [local, domain] = email.split('@');
    if (local.length <= 2) return `${local[0] ?? ''}*@${domain}`;
    return `${local.slice(0, 2)}${'*'.repeat(Math.max(local.length - 2, 1))}@${domain}`;
  }, [email]);

  useEffect(() => {
    if (!userId) {
      navigate('/login', { replace: true });
    }
  }, [navigate, userId]);

  useEffect(() => {
    if (user?.role) {
      const dest = (ADMIN_ROLES.includes(user.role) && !user.totp_enabled)
        ? '/profile?tab=2fa'
        : (next ?? ROLE_DEFAULT_ROUTE[user.role] ?? '/');
      navigate(dest, { replace: true });
    }
  }, [navigate, next, user]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (code.length !== 6) {
      setErrorMsg('Enter the 6-digit code from your authenticator app');
      return;
    }

    setSubmitting(true);
    setErrorMsg('');

    try {
      const profile = await completeTwoFactorLogin(userId, code);
      const dest = (ADMIN_ROLES.includes(profile?.role) && !profile?.totp_enabled)
        ? '/profile?tab=2fa'
        : (next ?? ROLE_DEFAULT_ROUTE[profile?.role] ?? '/admin/dashboard');
      navigate(dest, { replace: true });
    } catch (err) {
      const msg = err?.response?.data?.detail ?? err?.message;
      setErrorMsg(typeof msg === 'string' ? msg : 'Invalid authentication code');
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-gray-50 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">
              Two-Factor Verification
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Enter the 6-digit code from your authenticator app
            </p>
            {maskedEmail && (
              <p className="text-xs text-gray-400 mt-2">
                Signing in as {maskedEmail}
              </p>
            )}
          </div>

          {errorMsg && (
            <div
              className="mb-5 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex gap-2 items-start"
              role="alert"
            >
              <svg className="w-4 h-4 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
              </svg>
              {errorMsg}
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            <div>
              <label htmlFor="totp_code" className="block text-sm font-medium text-gray-700 mb-1.5">
                Authentication code
              </label>
              <input
                id="totp_code"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000"
                disabled={submitting}
                className="w-full border border-gray-300 rounded-lg px-3.5 py-2.5 text-center tracking-[0.4em] text-lg text-gray-900 placeholder-gray-400 outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:bg-gray-50 transition"
              />
            </div>

            <button
              type="submit"
              disabled={submitting || code.length !== 6}
              className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-sm font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {submitting ? (
                <>
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  Verifying
                </>
              ) : 'Verify code'}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            Need to use a different account?{' '}
            <Link to="/login" className="text-blue-600 hover:text-blue-700 font-medium">
              Back to login
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
