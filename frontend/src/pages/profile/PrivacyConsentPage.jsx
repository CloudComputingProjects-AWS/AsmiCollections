/**
 * PrivacyConsentPage — Phase F5 (Screen #12)
 * Manage marketing consents, request data export, account deletion
 */
import { useState, useEffect } from 'react';
import { ArrowLeft, Shield, Mail, MessageSquare, Download, Trash2, AlertTriangle } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../../api/apiClient';
import useAuthStore from '../../stores/authStore';

export default function PrivacyConsentPage() {
  const { logout } = useAuthStore();
  const navigate = useNavigate();
  const [consents, setConsents] = useState({ marketing_email: false, marketing_sms: false });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [deleteModal, setDeleteModal] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [msg, setMsg] = useState({ type: '', text: '' });

  const flash = (type, text) => {
    setMsg({ type, text });
    setTimeout(() => setMsg({ type: '', text: '' }), 5000);
  };

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get('/user/consents');
        const data = res.data?.consents || res.data || [];
        const email = data.find((c) => c.consent_type === 'marketing_email');
        const sms = data.find((c) => c.consent_type === 'marketing_sms');
        setConsents({
          marketing_email: email?.granted || false,
          marketing_sms: sms?.granted || false,
        });
      } catch { /* empty */ }
      setLoading(false);
    })();
  }, []);

  const handleConsentSave = async () => {
    setSaving(true);
    try {
      await api.put('/user/consents', consents);
      flash('success', 'Consent preferences updated');
    } catch (err) {
      flash('error', err.response?.data?.detail || 'Failed to update consents');
    }
    setSaving(false);
  };

  const handleDataExport = async () => {
    setExporting(true);
    try {
      const res = await api.get('/user/data-export', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = 'my-data-export.json';
      a.click();
      window.URL.revokeObjectURL(url);
      flash('success', 'Data exported successfully');
    } catch {
      flash('error', 'Failed to export data. Please try again.');
    }
    setExporting(false);
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirm !== 'DELETE') return;
    setDeleting(true);
    try {
      await api.post('/user/delete-account');
      flash('success', 'Account deletion requested. 30-day grace period started.');
      setDeleteModal(false);
      setTimeout(async () => {
        await logout();
        navigate('/');
      }, 3000);
    } catch (err) {
      flash('error', err.response?.data?.detail || 'Failed to request deletion');
    }
    setDeleting(false);
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-10">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-100 rounded w-48" />
          <div className="h-32 bg-gray-100 rounded-xl" />
          <div className="h-32 bg-gray-100 rounded-xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <Link to="/dashboard" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-black mb-6 transition">
        <ArrowLeft size={16} /> Back to Dashboard
      </Link>

      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
          <Shield size={20} className="text-gray-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Privacy & Consent</h1>
          <p className="text-sm text-gray-500">Manage your communication preferences and data</p>
        </div>
      </div>

      {msg.text && (
        <div className={`mb-6 px-4 py-3 rounded-lg text-sm font-medium ${
          msg.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200'
            : 'bg-red-50 text-red-700 border border-red-200'
        }`}>{msg.text}</div>
      )}

      {/* Communication Preferences */}
      <div className="border rounded-xl p-6 mb-6">
        <h2 className="font-semibold text-gray-900 mb-4">Communication Preferences</h2>
        <div className="space-y-4">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={consents.marketing_email}
              onChange={(e) => setConsents({ ...consents, marketing_email: e.target.checked })}
              className="accent-black w-4 h-4 mt-0.5"
            />
            <div>
              <div className="flex items-center gap-2">
                <Mail size={16} className="text-gray-500" />
                <span className="text-sm font-medium text-gray-900">Marketing Emails</span>
              </div>
              <p className="text-xs text-gray-500 mt-0.5">Receive emails about offers, new arrivals, and promotions</p>
            </div>
          </label>

          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={consents.marketing_sms}
              onChange={(e) => setConsents({ ...consents, marketing_sms: e.target.checked })}
              className="accent-black w-4 h-4 mt-0.5"
            />
            <div>
              <div className="flex items-center gap-2">
                <MessageSquare size={16} className="text-gray-500" />
                <span className="text-sm font-medium text-gray-900">SMS Updates</span>
              </div>
              <p className="text-xs text-gray-500 mt-0.5">Receive SMS about orders and promotions</p>
            </div>
          </label>
        </div>

        <button
          onClick={handleConsentSave}
          disabled={saving}
          className="mt-5 bg-black text-white px-5 py-2.5 rounded-lg font-medium text-sm hover:bg-gray-800 transition disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Preferences'}
        </button>
      </div>

      {/* Data Export */}
      <div className="border rounded-xl p-6 mb-6">
        <h2 className="font-semibold text-gray-900 mb-2">Export Your Data</h2>
        <p className="text-sm text-gray-500 mb-4">
          Download a copy of your personal data including profile, orders, and addresses.
          This is your right under DPDP Act 2023 and GDPR.
        </p>
        <button
          onClick={handleDataExport}
          disabled={exporting}
          className="flex items-center gap-2 border border-gray-300 px-5 py-2.5 rounded-lg font-medium text-sm hover:bg-gray-50 transition disabled:opacity-50"
        >
          <Download size={16} /> {exporting ? 'Exporting...' : 'Download My Data'}
        </button>
      </div>

      {/* Delete Account */}
      <div className="border border-red-200 bg-red-50/50 rounded-xl p-6">
        <h2 className="font-semibold text-red-700 mb-2">Delete Account</h2>
        <p className="text-sm text-gray-600 mb-4">
          Permanently delete your account and personal data after a 30-day grace period.
          Active orders will be fulfilled first. This cannot be undone.
        </p>
        <button
          onClick={() => setDeleteModal(true)}
          className="flex items-center gap-2 bg-red-600 text-white px-5 py-2.5 rounded-lg font-medium text-sm hover:bg-red-700 transition"
        >
          <Trash2 size={16} /> Request Account Deletion
        </button>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                <AlertTriangle size={20} className="text-red-600" />
              </div>
              <h2 className="font-bold text-lg text-gray-900">Delete Your Account?</h2>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              This will permanently delete your account after 30 days.
              Your orders, invoices, and payment records will be retained for legal compliance.
              You can cancel the deletion during the grace period.
            </p>
            <p className="text-sm font-medium text-gray-700 mb-2">Type <strong>DELETE</strong> to confirm:</p>
            <input
              type="text"
              value={deleteConfirm}
              onChange={(e) => setDeleteConfirm(e.target.value)}
              placeholder="DELETE"
              className="w-full border rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-red-500 outline-none font-mono mb-4"
            />
            <div className="flex gap-3">
              <button onClick={() => { setDeleteModal(false); setDeleteConfirm(''); }}
                className="flex-1 border px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-gray-50 transition">
                Cancel
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={deleteConfirm !== 'DELETE' || deleting}
                className="flex-1 bg-red-600 text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-red-700 transition disabled:opacity-50"
              >
                {deleting ? 'Processing...' : 'Delete Account'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
