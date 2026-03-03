/**
 * Privacy & Consent — Phase F5 (Screen #12)
 * Manage marketing consents, request data export, account deletion
 */
import { useState, useEffect } from 'react';
import { Shield, Download, Trash2, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import apiClient from '../../api/apiClient';

export default function PrivacyConsentPage() {
  const [consents, setConsents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deletionStatus, setDeletionStatus] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteReason, setDeleteReason] = useState('');
  const [exporting, setExporting] = useState(false);

  const fetchConsents = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/api/v1/user/consents');
      setConsents(res.data?.consents || res.data || []);
    } catch { /* may not be implemented yet */ }
    finally { setLoading(false); }
  };

  const checkDeletion = async () => {
    try {
      const res = await apiClient.get('/api/v1/user/deletion-status');
      setDeletionStatus(res.data);
    } catch { /* no pending deletion */ }
  };

  useEffect(() => { fetchConsents(); checkDeletion(); }, []);

  const toggleConsent = async (type, granted) => {
    try {
      await apiClient.put('/api/v1/user/consents', { consent_type: type, granted });
      toast.success(`${type.replace(/_/g, ' ')} consent ${granted ? 'granted' : 'revoked'}`);
      fetchConsents();
    } catch (err) { toast.error(err.response?.data?.detail || 'Update failed'); }
  };

  const requestExport = async () => {
    setExporting(true);
    try {
      const res = await apiClient.get('/api/v1/user/data-export', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a'); a.href = url; a.download = 'my-data-export.json'; a.click();
      window.URL.revokeObjectURL(url);
      toast.success('Data exported');
    } catch { toast.error('Export failed'); }
    finally { setExporting(false); }
  };

  const requestDeletion = async () => {
    try {
      await apiClient.post('/api/v1/user/delete-account', { reason: deleteReason });
      toast.success('Account deletion requested. You have 30 days to cancel.');
      setShowDeleteModal(false);
      checkDeletion();
    } catch (err) { toast.error(err.response?.data?.detail || 'Request failed'); }
  };

  const cancelDeletion = async () => {
    try {
      await apiClient.post('/api/v1/user/cancel-deletion');
      toast.success('Deletion cancelled');
      setDeletionStatus(null);
    } catch (err) { toast.error(err.response?.data?.detail || 'Cancel failed'); }
  };

  const marketingConsents = consents.filter((c) => ['marketing_email', 'marketing_sms'].includes(c.consent_type));
  const requiredConsents = consents.filter((c) => ['terms_of_service', 'privacy_policy', 'data_processing'].includes(c.consent_type));

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <h1 className="text-2xl font-bold flex items-center gap-2"><Shield className="w-6 h-6 text-brand-600" /> Privacy & Consent</h1>

      {/* Required Consents (read-only) */}
      {requiredConsents.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 space-y-4">
          <h2 className="text-lg font-semibold">Required Consents</h2>
          {requiredConsents.map((c) => (
            <div key={c.id || c.consent_type} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
              <div>
                <p className="text-sm font-medium capitalize">{c.consent_type.replace(/_/g, ' ')}</p>
                {c.version && <p className="text-xs text-gray-400">Version {c.version}</p>}
              </div>
              <div className="flex items-center gap-1.5">
                {c.granted ? <CheckCircle className="w-4 h-4 text-emerald-500" /> : <XCircle className="w-4 h-4 text-red-500" />}
                <span className="text-xs text-gray-500">{c.granted ? 'Accepted' : 'Not accepted'}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Marketing Consents (toggleable) */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 space-y-4">
        <h2 className="text-lg font-semibold">Communication Preferences</h2>
        <p className="text-sm text-gray-500">Control how we communicate with you about offers and updates.</p>

        <div className="space-y-4">
          <div className="flex items-center justify-between py-3">
            <div>
              <p className="text-sm font-medium">Marketing Emails</p>
              <p className="text-xs text-gray-500">Receive offers, new arrivals, and seasonal promotions</p>
            </div>
            <button onClick={() => {
              const current = marketingConsents.find((c) => c.consent_type === 'marketing_email');
              toggleConsent('marketing_email', !(current?.granted));
            }} className={`relative w-11 h-6 rounded-full transition-colors ${marketingConsents.find((c) => c.consent_type === 'marketing_email')?.granted ? 'bg-brand-600' : 'bg-gray-300'}`}>
              <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${marketingConsents.find((c) => c.consent_type === 'marketing_email')?.granted ? 'translate-x-5' : ''}`} />
            </button>
          </div>

          <div className="flex items-center justify-between py-3 border-t border-gray-50">
            <div>
              <p className="text-sm font-medium">SMS Updates</p>
              <p className="text-xs text-gray-500">Order updates and promotional messages via SMS</p>
            </div>
            <button onClick={() => {
              const current = marketingConsents.find((c) => c.consent_type === 'marketing_sms');
              toggleConsent('marketing_sms', !(current?.granted));
            }} className={`relative w-11 h-6 rounded-full transition-colors ${marketingConsents.find((c) => c.consent_type === 'marketing_sms')?.granted ? 'bg-brand-600' : 'bg-gray-300'}`}>
              <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${marketingConsents.find((c) => c.consent_type === 'marketing_sms')?.granted ? 'translate-x-5' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Data Export */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 space-y-3">
        <h2 className="text-lg font-semibold">Your Data</h2>
        <p className="text-sm text-gray-500">Download a copy of your personal data as required by DPDP Act / GDPR.</p>
        <button onClick={requestExport} disabled={exporting}
          className="flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50 transition-colors">
          <Download className="w-4 h-4" /> {exporting ? 'Preparing...' : 'Export My Data'}
        </button>
      </div>

      {/* Account Deletion */}
      <div className="bg-white rounded-xl border border-red-100 shadow-sm p-6 space-y-3">
        <h2 className="text-lg font-semibold text-red-700 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" /> Delete Account
        </h2>

        {deletionStatus?.status === 'grace_period' ? (
          <div className="space-y-3">
            <div className="p-4 bg-red-50 rounded-lg">
              <p className="text-sm text-red-700 font-medium">Account deletion is pending</p>
              <p className="text-xs text-red-600 mt-1">
                Your account will be permanently deleted on {new Date(deletionStatus.grace_ends_at).toLocaleDateString()}.
                All personal data will be anonymized.
              </p>
            </div>
            <button onClick={cancelDeletion}
              className="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm hover:bg-gray-800 transition-colors">
              Cancel Deletion
            </button>
          </div>
        ) : (
          <>
            <p className="text-sm text-gray-500">
              This will permanently delete your account after a 30-day grace period.
              Active orders will be fulfilled first. Invoices and payment records are retained as required by law.
            </p>
            <button onClick={() => setShowDeleteModal(true)}
              className="flex items-center gap-2 px-4 py-2 border border-red-200 text-red-700 rounded-lg text-sm hover:bg-red-50 transition-colors">
              <Trash2 className="w-4 h-4" /> Request Account Deletion
            </button>
          </>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 space-y-4">
            <div className="text-center">
              <AlertTriangle className="mx-auto w-12 h-12 text-red-500 mb-2" />
              <h3 className="text-lg font-bold">Delete Your Account?</h3>
              <p className="text-sm text-gray-500 mt-2">
                This action cannot be undone after the 30-day grace period.
                Your personal data will be permanently anonymized.
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Reason (optional)</label>
              <textarea rows={2} value={deleteReason} onChange={(e) => setDeleteReason(e.target.value)}
                placeholder="Help us improve — why are you leaving?"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-red-500" />
            </div>
            <div className="flex gap-3">
              <button onClick={requestDeletion} className="flex-1 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium">
                Yes, Delete My Account
              </button>
              <button onClick={() => setShowDeleteModal(false)} className="flex-1 py-2.5 border border-gray-200 rounded-lg text-sm hover:bg-gray-50">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
