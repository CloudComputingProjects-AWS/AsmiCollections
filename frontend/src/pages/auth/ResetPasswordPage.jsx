import { useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { Lock } from 'lucide-react';
import toast from 'react-hot-toast';
import { authApi } from '@/api';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';

export default function ResetPasswordPage() {
  const [params] = useSearchParams();
  const token = params.get('token');
  const navigate = useNavigate();
  const [form, setForm] = useState({ password: '', confirm: '' });
  const [loading, setLoading] = useState(false);

  if (!token) {
    return (
      <div className="text-center space-y-4">
        <h2 className="font-display text-xl text-error">Invalid Link</h2>
        <p className="text-sm text-ink-muted">This reset link is invalid or has expired.</p>
        <Link to="/forgot-password" className="text-sm text-brand-600 font-medium hover:underline">
          Request a new one
        </Link>
      </div>
    );
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.password.length < 8) return toast.error('Minimum 8 characters');
    if (form.password !== form.confirm) return toast.error('Passwords do not match');
    setLoading(true);
    try {
      await authApi.resetPassword({ token, new_password: form.password });
      toast.success('Password reset successfully');
      navigate('/login');
    } catch (err) {
      toast.error(err.message || 'Reset failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <h1 className="font-display text-2xl text-center mb-6">Set New Password</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input label="New Password" type="password" icon={Lock} placeholder="Min. 8 characters"
          value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        <Input label="Confirm Password" type="password" icon={Lock} placeholder="Repeat password"
          value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} />
        <Button type="submit" loading={loading} className="w-full">Reset Password</Button>
      </form>
    </>
  );
}
