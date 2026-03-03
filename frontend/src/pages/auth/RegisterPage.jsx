import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, User } from 'lucide-react';
import useAuthStore from '@/stores/authStore';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';

const COUNTRY_CODES = [
  { code: '+91', label: '+91 (India)' },
  { code: '+1', label: '+1 (USA/Canada)' },
  { code: '+44', label: '+44 (UK)' },
  { code: '+61', label: '+61 (Australia)' },
  { code: '+971', label: '+971 (UAE)' },
  { code: '+65', label: '+65 (Singapore)' },
  { code: '+60', label: '+60 (Malaysia)' },
  { code: '+880', label: '+880 (Bangladesh)' },
  { code: '+977', label: '+977 (Nepal)' },
  { code: '+94', label: '+94 (Sri Lanka)' },
  { code: '+49', label: '+49 (Germany)' },
  { code: '+33', label: '+33 (France)' },
  { code: '+81', label: '+81 (Japan)' },
  { code: '+86', label: '+86 (China)' },
  { code: '+82', label: '+82 (South Korea)' },
];

export default function RegisterPage() {
  const [form, setForm] = useState({
    email: '', password: '', confirm_password: '',
    first_name: '', last_name: '', phone: '',
    country_code: '+91',
    consent_terms: false, consent_privacy: false,
    consent_marketing_email: false, consent_marketing_sms: false,
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const register = useAuthStore((s) => s.register);
  const navigate = useNavigate();

  const set = (key) => (e) => {
    const val = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setForm({ ...form, [key]: val });
  };

  const validate = () => {
    const e = {};
    if (!form.first_name.trim()) e.first_name = 'First name is required';
    if (!form.email) e.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = 'Invalid email';
    if (!form.password) e.password = 'Password is required';
    else if (form.password.length < 8) e.password = 'Minimum 8 characters';
    if (form.password !== form.confirm_password) e.confirm_password = 'Passwords do not match';
    if (!form.consent_terms) e.consent_terms = 'You must accept the Terms of Service';
    if (!form.consent_privacy) e.consent_privacy = 'You must accept the Privacy Policy';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');
    if (!validate()) return;
    setLoading(true);
    try {
      await register({
        email: form.email,
        password: form.password,
        first_name: form.first_name,
        last_name: form.last_name,
        phone: form.phone || undefined,
        country_code: form.country_code,
        terms_accepted: form.consent_terms,
        privacy_accepted: form.consent_privacy,
        marketing_email: form.consent_marketing_email,
        marketing_sms: form.consent_marketing_sms,
      });
      setSuccessMsg('Account created! Please verify your email.');
      setTimeout(() => {
        navigate('/verify-otp', { state: { email: form.email } });
      }, 1500);
    } catch (err) {
      setErrorMsg(err.response?.data?.detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <h1 className="font-display text-2xl text-center mb-6">Create Account</h1>

      {errorMsg && (
        <div
          className="mb-5 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex gap-2 items-start"
          role="alert"
        >
          <svg className="w-4 h-4 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd"/>
          </svg>
          {errorMsg}
        </div>
      )}

      {successMsg && (
        <div
          className="mb-5 px-4 py-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm flex gap-2 items-center"
          role="status"
        >
          <svg className="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
          </svg>
          {successMsg}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <Input label="First Name" icon={User} placeholder="John"
            value={form.first_name} onChange={set('first_name')} error={errors.first_name} />
          <Input label="Last Name" placeholder="Doe"
            value={form.last_name} onChange={set('last_name')} />
        </div>
        <Input label="Email" type="email" icon={Mail} placeholder="you@example.com"
          value={form.email} onChange={set('email')} error={errors.email} />

        {/* Phone with country code dropdown */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Phone (optional)
          </label>
          <div className="flex gap-2">
            <select
              value={form.country_code}
              onChange={set('country_code')}
              className="w-[140px] shrink-0 border border-gray-300 rounded-lg px-2 py-2.5 text-sm text-gray-900 bg-white outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
              aria-label="Country code"
            >
              {COUNTRY_CODES.map((cc) => (
                <option key={cc.code} value={cc.code}>{cc.label}</option>
              ))}
            </select>
            <input
              type="tel"
              value={form.phone}
              onChange={set('phone')}
              placeholder="9876543210"
              className="flex-1 border border-gray-300 rounded-lg px-3.5 py-2.5 text-sm text-gray-900 placeholder-gray-400 outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
              aria-label="Phone number"
            />
          </div>
        </div>

        <Input label="Password" type="password" icon={Lock} placeholder="Min. 8 characters"
          value={form.password} onChange={set('password')} error={errors.password} />
        <Input label="Confirm Password" type="password" icon={Lock} placeholder="Repeat password"
          value={form.confirm_password} onChange={set('confirm_password')} error={errors.confirm_password} />

        {/* Consent checkboxes */}
        <div className="space-y-2 pt-2">
          <Checkbox checked={form.consent_terms} onChange={set('consent_terms')} error={errors.consent_terms}>
            I agree to the <Link to="/terms" className="text-brand-600 underline">Terms of Service</Link> and{' '}
            <Link to="/privacy-policy" className="text-brand-600 underline">Privacy Policy</Link> *
          </Checkbox>
          <Checkbox checked={form.consent_privacy} onChange={set('consent_privacy')} error={errors.consent_privacy}>
            I consent to the processing of my personal data *
          </Checkbox>
          <Checkbox checked={form.consent_marketing_email} onChange={set('consent_marketing_email')}>
            Send me emails about offers and new arrivals
          </Checkbox>
          <Checkbox checked={form.consent_marketing_sms} onChange={set('consent_marketing_sms')}>
            Send me SMS updates about orders and promotions
          </Checkbox>
        </div>

        <Button type="submit" loading={loading} className="w-full">
          Create Account
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-ink-muted">
        Already have an account?{' '}
        <Link to="/login" className="text-brand-600 hover:text-brand-700 font-medium">Sign in</Link>
      </p>
    </>
  );
}

function Checkbox({ children, checked, onChange, error }) {
  return (
    <div>
      <label className="flex items-start gap-2 text-sm text-ink-muted cursor-pointer">
        <input type="checkbox" checked={checked} onChange={onChange}
          className="mt-0.5 rounded border-ink-faint/30 text-brand-600 focus:ring-brand-500" />
        <span>{children}</span>
      </label>
      {error && <p className="text-xs text-error ml-6 mt-0.5">{error}</p>}
    </div>
  );
}
