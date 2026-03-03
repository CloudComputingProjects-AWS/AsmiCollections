import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail } from 'lucide-react';
import toast from 'react-hot-toast';
import { authApi } from '@/api';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    try {
      await authApi.forgotPassword(email);
      setSent(true);
      toast.success('Reset link sent — check your email');
    } catch (err) {
      toast.error(err.message || 'Failed to send reset link');
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <div className="text-center space-y-4">
        <div className="mx-auto w-12 h-12 bg-success/10 rounded-full flex items-center justify-center">
          <Mail className="text-success" size={24} />
        </div>
        <h2 className="font-display text-xl">Check Your Email</h2>
        <p className="text-sm text-ink-muted">We sent a password reset link to <strong>{email}</strong></p>
        <Link to="/login" className="text-sm text-brand-600 font-medium hover:underline">
          Back to Sign In
        </Link>
      </div>
    );
  }

  return (
    <>
      <h1 className="font-display text-2xl text-center mb-2">Forgot Password</h1>
      <p className="text-sm text-ink-muted text-center mb-6">Enter your email and we'll send a reset link.</p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input label="Email" type="email" icon={Mail} placeholder="you@example.com"
          value={email} onChange={(e) => setEmail(e.target.value)} />
        <Button type="submit" loading={loading} className="w-full">Send Reset Link</Button>
      </form>
      <p className="mt-4 text-center text-sm text-ink-muted">
        <Link to="/login" className="text-brand-600 font-medium hover:underline">Back to Sign In</Link>
      </p>
    </>
  );
}
