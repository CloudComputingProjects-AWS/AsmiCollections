/**
 * ManageAddressesPage â€” Phase F5 (Screen #11)
 * Add/edit/delete home and office addresses
 */
import { useState, useEffect, useCallback } from 'react';
import { Plus, Pencil, Trash2, MapPin, ArrowLeft, Home, Building2, Map } from 'lucide-react';
import { Link } from 'react-router-dom';
import api from '../../api/apiClient';
import useAuthStore from '../../stores/authStore';

const INDIAN_STATES = [
  'Andhra Pradesh','Arunachal Pradesh','Assam','Bihar','Chhattisgarh',
  'Goa','Gujarat','Haryana','Himachal Pradesh','Jharkhand','Karnataka',
  'Kerala','Madhya Pradesh','Maharashtra','Manipur','Meghalaya','Mizoram',
  'Nagaland','Odisha','Punjab','Rajasthan','Sikkim','Tamil Nadu',
  'Telangana','Tripura','Uttar Pradesh','Uttarakhand','West Bengal',
  'Andaman and Nicobar','Chandigarh','Dadra and Nagar Haveli',
  'Daman and Diu','Delhi','Jammu and Kashmir','Ladakh','Lakshadweep','Puducherry',
];

const LABEL_ICONS = { home: Home, office: Building2, other: Map };

const EMPTY_FORM = {
  label: 'home', full_name: '', phone: '', address_line_1: '',
  address_line_2: '', city: '', state: '', postal_code: '',
  country: 'India', is_default: false,
};

export default function ManageAddressesPage() {
  const user = useAuthStore((s) => s.user);
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editAddr, setEditAddr] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState({ type: '', text: '' });

  const flash = (type, text) => {
    setMsg({ type, text });
    setTimeout(() => setMsg({ type: '', text: '' }), 4000);
  };

  const fetchAddresses = useCallback(async () => {
    try {
      const res = await api.get('/addresses');
      setAddresses(res.data?.addresses || res.data || []);
    } catch { /* empty */ }
    setLoading(false);
  }, []);

  useEffect(() => { fetchAddresses(); }, [fetchAddresses]);

  const openAdd = () => {
    setEditAddr(null);
    setForm(EMPTY_FORM);
    setModalOpen(true);
  };

  const openEdit = (addr) => {
    setEditAddr(addr);
    setForm({
      label: addr.label || 'home',
      full_name: addr.full_name || '',
      phone: addr.phone || '',
      address_line_1: addr.address_line_1 || '',
      address_line_2: addr.address_line_2 || '',
      city: addr.city || '',
      state: addr.state || '',
      postal_code: addr.postal_code || '',
      country: addr.country || 'India',
      is_default: addr.is_default || false,
    });
    setModalOpen(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    if (!form.full_name || !form.address_line_1 || !form.city || !form.state || !form.postal_code) {
      return flash('error', 'Please fill all required fields');
    }
    setSaving(true);
    try {
      if (editAddr) {
        await api.put(`/addresses/${editAddr.id}`, form);
        flash('success', 'Address updated');
      } else {
        await api.post('/addresses', form);
        flash('success', 'Address added');
      }
      setModalOpen(false);
      fetchAddresses();
    } catch (err) {
      flash('error', err.response?.data?.detail || 'Failed to save address');
    }
    setSaving(false);
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this address?')) return;
    try {
      await api.delete(`/addresses/${id}`);
      flash('success', 'Address deleted');
      fetchAddresses();
    } catch {
      flash('error', 'Failed to delete address');
    }
  };

  const handleSetDefault = async (id) => {
    try {
      await api.put(`/addresses/${id}`, { is_default: true });
      flash('success', 'Default address updated');
      fetchAddresses();
    } catch { /* empty */ }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <Link to={['admin', 'product_manager', 'order_manager', 'finance_manager'].includes(user?.role) ? '/admin/dashboard' : '/dashboard'} className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-black mb-6 transition">
        <ArrowLeft size={16} /> Back to Dashboard
      </Link>

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">My Addresses</h1>
        <button
          onClick={() => { if (addresses.length >= 2) { flash("error", "Maximum 2 addresses allowed"); return; } openAdd(); }}
          className="flex items-center gap-2 bg-black text-white px-4 py-2.5 rounded-lg font-medium text-sm hover:bg-gray-800 transition"
        >
          <Plus size={16} /> Add Address
        </button>
      </div>

      {msg.text && (
        <div className={`mb-4 px-4 py-3 rounded-lg text-sm font-medium ${
          msg.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200'
            : 'bg-red-50 text-red-700 border border-red-200'
        }`}>{msg.text}</div>
      )}

      {loading ? (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="animate-pulse bg-gray-100 rounded-xl h-32" />
          ))}
        </div>
      ) : addresses.length === 0 ? (
        <div className="text-center py-16 border-2 border-dashed rounded-xl">
          <MapPin size={40} className="mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500 mb-1">No addresses saved yet</p>
          <p className="text-sm text-gray-500">Add your home or office address for faster checkout</p>
        </div>
      ) : (
        <div className="space-y-4">
          {addresses.map((addr) => {
            const Icon = LABEL_ICONS[addr.label] || MapPin;
            return (
              <div key={addr.id} className={`border rounded-xl p-5 transition ${addr.is_default ? 'border-black bg-gray-50' : 'hover:border-gray-300'}`}>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
                      <Icon size={18} className="text-gray-600" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-gray-900">{addr.full_name}</span>
                        <span className="text-xs uppercase bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full font-medium">{addr.label}</span>
                        {addr.is_default && <span className="text-xs bg-black text-white px-2 py-0.5 rounded-full">Default</span>}
                      </div>
                      <p className="text-sm text-gray-600">{addr.address_line_1}</p>
                      {addr.address_line_2 && <p className="text-sm text-gray-600">{addr.address_line_2}</p>}
                      <p className="text-sm text-gray-600">{addr.city}, {addr.state} {addr.postal_code}</p>
                      {addr.phone && <p className="text-sm text-gray-500 mt-1">Phone: {addr.phone}</p>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {!addr.is_default && (
                      <button onClick={() => handleSetDefault(addr.id)} className="text-xs text-gray-500 hover:text-black underline">
                        Set Default
                      </button>
                    )}
                    <button onClick={() => openEdit(addr)} className="p-2 text-gray-400 hover:text-black transition" title="Edit">
                      <Pencil size={16} />
                    </button>
                    <button onClick={() => handleDelete(addr.id)} className="p-2 text-gray-400 hover:text-red-600 transition" title="Delete">
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto shadow-2xl">
            <div className="flex items-center justify-between p-5 border-b">
              <h2 className="font-bold text-lg">{editAddr ? 'Edit Address' : 'Add New Address'}</h2>
              <button onClick={() => setModalOpen(false)} className="text-gray-400 hover:text-black">âœ•</button>
            </div>
            <form onSubmit={handleSave} className="p-5 space-y-4">
              {/* Label */}
              <div className="flex gap-2">
                {['home', 'office', 'other'].map((l) => (
                  <button key={l} type="button" onClick={() => setForm({ ...form, label: l })}
                    className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition ${
                      form.label === l ? 'bg-black text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}>{l}</button>
                ))}
              </div>
              {/* Name + Phone */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
                  <input type="text" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-black outline-none" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                  <input type="tel" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value.replace(/\D/g, '').slice(0, 10) })}
                    className="w-full border rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-black outline-none" />
                </div>
              </div>
              {/* Address */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Address Line 1 *</label>
                <input type="text" value={form.address_line_1} onChange={(e) => setForm({ ...form, address_line_1: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-black outline-none" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Address Line 2</label>
                <input type="text" value={form.address_line_2} onChange={(e) => setForm({ ...form, address_line_2: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-black outline-none" />
              </div>
              {/* City + State + PIN */}
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">City *</label>
                  <input type="text" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-black outline-none" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">State *</label>
                  <select value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })}
                    className="w-full border rounded-lg px-2 py-2.5 text-sm focus:ring-2 focus:ring-black outline-none" required>
                    <option value="">Select</option>
                    {INDIAN_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">PIN Code *</label>
                  <input type="text" value={form.postal_code} maxLength={6}
                    onChange={(e) => setForm({ ...form, postal_code: e.target.value.replace(/\D/g, '').slice(0, 6) })}
                    className="w-full border rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-black outline-none font-mono" required />
                </div>
              </div>
              {/* Default */}
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={form.is_default} onChange={(e) => setForm({ ...form, is_default: e.target.checked })}
                  className="accent-black w-4 h-4" />
                <span className="text-sm text-gray-700">Set as default address</span>
              </label>
              <button type="submit" disabled={saving}
                className="w-full bg-black text-white py-3 rounded-lg font-semibold hover:bg-gray-800 transition disabled:opacity-50">
                {saving ? 'Saving...' : editAddr ? 'Update Address' : 'Save Address'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
