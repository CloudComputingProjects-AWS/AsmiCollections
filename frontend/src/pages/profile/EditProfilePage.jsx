/**
 * EditProfilePage â€” Phase F5 (Screen #10)
 * Name, email, phone, change password
 */
import { useState, useEffect } from 'react';
import { User, Mail, Phone, Lock, Save, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import useAuthStore from '../../stores/authStore';
import api from '../../api/apiClient';

export default function EditProfilePage() {
  const { user, init } = useAuthStore();
  const [tab, setTab] = useState('profile'); // 'profile' | 'password'
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState({ type: '', text: '' });

  // Profile form
  const [profile, setProfile] = useState({
    first_name: '', last_name: '', phone: '', country_code: '+91',
  });

  // Password form
  const [pw, setPw] = useState({
    current_password: '', new_password: '', confirm_password: '',
  });

  useEffect(() => {
    if (user) {
      setProfile({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        phone: user.phone || '',
        country_code: user.country_code || '+91',
      });
    }
  }, [user]);

  const flash = (type, text) => {
    setMsg({ type, text });
    setTimeout(() => setMsg({ type: '', text: '' }), 4000);
  };

  const handleProfileSave = async (e) => {
    e.preventDefault();
    if (!profile.first_name.trim()) return flash('error', 'First name is required');
    setLoading(true);
    try {
      await api.put('/user/profile', profile);
      await init(); // refresh user in store
      flash('success', 'Profile updated successfully');
    } catch (err) {
      flash('error', err.response?.data?.detail || 'Failed to update profile');
    }
    setLoading(false);
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    if (pw.new_password.length < 8) return flash('error', 'Password must be at least 8 characters');
    if (pw.new_password !== pw.confirm_password) return flash('error', 'Passwords do not match');
    setLoading(true);
    try {
      await api.put('/user/change-password', {
        current_password: pw.current_password,
        new_password: pw.new_password,
      });
      setPw({ current_password: '', new_password: '', confirm_password: '' });
      flash('success', 'Password changed. Please login again.');
    } catch (err) {
      flash('error', err.response?.data?.detail || 'Failed to change password');
    }
    setLoading(false);
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      {/* Back link */}
      <Link to={['admin', 'product_manager', 'order_manager', 'finance_manager'].includes(user?.role) ? '/admin/dashboard' : '/dashboard'} className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-black mb-6 transition">
        <ArrowLeft size={16} /> Back to Dashboard
      </Link>

      <h1 className="text-2xl font-bold text-gray-900 mb-6">My Profile</h1>

      {/* Flash message */}
      {msg.text && (
        <div className={`mb-4 px-4 py-3 rounded-lg text-sm font-medium ${
          msg.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200'
            : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {msg.text}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-8 border-b">
        {[
          { id: 'profile', label: 'Personal Info', icon: User },
          { id: 'password', label: 'Change Password', icon: Lock },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition ${
              tab === t.id
                ? 'border-black text-black'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <t.icon size={16} /> {t.label}
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {tab === 'profile' && (
        <form onSubmit={handleProfileSave} className="space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-1">First Name *</label>
              <div className="relative">
                <User size={16} className="absolute left-3 top-3 text-gray-400" />
                <input
                  id="first_name"
                  type="text"
                  value={profile.first_name}
                  onChange={(e) => setProfile({ ...profile, first_name: e.target.value })}
                  className="w-full border rounded-lg pl-10 pr-3 py-2.5 text-sm focus:ring-2 focus:ring-black focus:border-transparent outline-none"
                  required
                />
              </div>
            </div>
            <div>
              <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
              <input
                id="last_name"
                type="text"
                value={profile.last_name}
                onChange={(e) => setProfile({ ...profile, last_name: e.target.value })}
                className="w-full border rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-black focus:border-transparent outline-none"
              />
            </div>
          </div>

          <div>
            <label htmlFor="email_field" className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <div className="relative">
              <Mail size={16} className="absolute left-3 top-3 text-gray-400" />
              <input
                id="email_field"
                type="email"
                value={user?.email || ''}
                disabled
                className="w-full border rounded-lg pl-10 pr-3 py-2.5 text-sm bg-gray-50 text-gray-500 cursor-not-allowed"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">Email cannot be changed</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
            <div className="flex gap-2">
              <select
                aria-label="Country code"
                value={profile.country_code}
                onChange={(e) => setProfile({ ...profile, country_code: e.target.value })}
                className="border rounded-lg px-2 py-2.5 text-sm w-20 focus:ring-2 focus:ring-black outline-none"
              >
                <option value="+91">+91</option>
                <option value="+1">+1</option>
                <option value="+44">+44</option>
              </select>
              <div className="relative flex-1">
                <Phone size={16} className="absolute left-3 top-3 text-gray-400" />
                <input
                  type="tel"
                  value={profile.phone}
                  onChange={(e) => setProfile({ ...profile, phone: e.target.value.replace(/\D/g, '').slice(0, 10) })}
                  placeholder="9876543210"
                  className="w-full border rounded-lg pl-10 pr-3 py-2.5 text-sm focus:ring-2 focus:ring-black focus:border-transparent outline-none"
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 bg-black text-white px-6 py-2.5 rounded-lg font-medium text-sm hover:bg-gray-800 transition disabled:opacity-50"
          >
            <Save size={16} /> {loading ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      )}

      {/* Password Tab */}
      {tab === 'password' && (
        <form onSubmit={handlePasswordChange} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Current Password *</label>
            <input
              type="password"
              value={pw.current_password}
              onChange={(e) => setPw({ ...pw, current_password: e.target.value })}
              className="w-full border rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-black focus:border-transparent outline-none"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">New Password *</label>
            <input
              type="password"
              value={pw.new_password}
              onChange={(e) => setPw({ ...pw, new_password: e.target.value })}
              className="w-full border rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-black focus:border-transparent outline-none"
              required
              minLength={8}
            />
            <p className="text-xs text-gray-500 mt-1">Minimum 8 characters</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Confirm New Password *</label>
            <input
              type="password"
              value={pw.confirm_password}
              onChange={(e) => setPw({ ...pw, confirm_password: e.target.value })}
              className="w-full border rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-black focus:border-transparent outline-none"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 bg-black text-white px-6 py-2.5 rounded-lg font-medium text-sm hover:bg-gray-800 transition disabled:opacity-50"
          >
            <Lock size={16} /> {loading ? 'Changing...' : 'Change Password'}
          </button>
        </form>
      )}
    </div>
  );
}
