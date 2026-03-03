/**
 * Coupon Manager — Phase F4 (Screen #27)
 */
import { useEffect, useState } from 'react';
import { useCouponStore } from '../../stores/adminStores';
import { DataTable, PageHeader, Modal, ConfirmDialog, StatusBadge } from '../../components/admin/AdminUI';

export default function CouponManager() {
  const { coupons, loading, fetchCoupons, createCoupon, updateCoupon, deleteCoupon } = useCouponStore();
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const initForm = { code: '', description: '', type: 'flat', value: '', min_order_value: '', max_discount: '', usage_limit: '', per_user_limit: 1, starts_at: '', expires_at: '', is_active: true };
  const [form, setForm] = useState(initForm);

  useEffect(() => { fetchCoupons(); }, []);

  const openEdit = (c) => {
    setEditing(c);
    setForm({ code: c.code, description: c.description || '', type: c.type, value: c.value, min_order_value: c.min_order_value || '', max_discount: c.max_discount || '', usage_limit: c.usage_limit || '', per_user_limit: c.per_user_limit || 1, starts_at: c.starts_at?.slice(0, 16) || '', expires_at: c.expires_at?.slice(0, 16) || '', is_active: c.is_active });
    setShowForm(true);
  };

  const handleSave = async () => {
    const payload = { ...form, value: parseFloat(form.value), min_order_value: form.min_order_value ? parseFloat(form.min_order_value) : 0, max_discount: form.max_discount ? parseFloat(form.max_discount) : null, usage_limit: form.usage_limit ? parseInt(form.usage_limit) : null, per_user_limit: parseInt(form.per_user_limit) || 1 };
    try {
      if (editing) await updateCoupon(editing.id, payload);
      else await createCoupon(payload);
      setShowForm(false); fetchCoupons();
    } catch (err) { alert(err.response?.data?.detail || 'Failed'); }
  };

  const columns = [
    { header: 'Code', render: (r) => <span className="font-mono font-semibold text-sm">{r.code}</span> },
    { header: 'Type/Value', render: (r) => r.type === 'percent' ? `${r.value}%` : `₹${r.value}` },
    { header: 'Min Order', render: (r) => r.min_order_value ? `₹${r.min_order_value}` : '—' },
    { header: 'Used', render: (r) => `${r.used_count || 0}/${r.usage_limit || '∞'}` },
    { header: 'Expires', render: (r) => r.expires_at ? new Date(r.expires_at).toLocaleDateString() : '—' },
    { header: 'Status', render: (r) => <StatusBadge status={r.is_active ? 'active' : 'inactive'} /> },
    { header: '', render: (r) => (
      <div className="flex gap-1">
        <button onClick={(e) => { e.stopPropagation(); openEdit(r); }} className="text-blue-600 text-sm hover:underline">Edit</button>
        <button onClick={(e) => { e.stopPropagation(); setDeleteTarget(r); }} className="text-red-500 text-sm hover:underline">Del</button>
      </div>
    )},
  ];

  return (
    <div>
      <PageHeader title="Coupons" actions={<button onClick={() => { setEditing(null); setForm(initForm); setShowForm(true); }} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">+ Add Coupon</button>} />
      <DataTable columns={columns} data={coupons} loading={loading} />
      <Modal open={showForm} onClose={() => setShowForm(false)} title={editing ? 'Edit Coupon' : 'New Coupon'}>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="block text-sm font-medium mb-1">Code</label><input type="text" value={form.code} onChange={(e) => setForm({...form, code: e.target.value.toUpperCase()})} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm font-mono" /></div>
            <div><label className="block text-sm font-medium mb-1">Type</label><select value={form.type} onChange={(e) => setForm({...form, type: e.target.value})} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"><option value="flat">Flat (₹)</option><option value="percent">Percent (%)</option></select></div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div><label className="block text-sm font-medium mb-1">Value</label><input type="number" value={form.value} onChange={(e) => setForm({...form, value: e.target.value})} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" /></div>
            <div><label className="block text-sm font-medium mb-1">Min Order</label><input type="number" value={form.min_order_value} onChange={(e) => setForm({...form, min_order_value: e.target.value})} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" /></div>
            <div><label className="block text-sm font-medium mb-1">Max Discount</label><input type="number" value={form.max_discount} onChange={(e) => setForm({...form, max_discount: e.target.value})} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" /></div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="block text-sm font-medium mb-1">Starts</label><input type="datetime-local" value={form.starts_at} onChange={(e) => setForm({...form, starts_at: e.target.value})} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" /></div>
            <div><label className="block text-sm font-medium mb-1">Expires</label><input type="datetime-local" value={form.expires_at} onChange={(e) => setForm({...form, expires_at: e.target.value})} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" /></div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="block text-sm font-medium mb-1">Usage Limit</label><input type="number" value={form.usage_limit} onChange={(e) => setForm({...form, usage_limit: e.target.value})} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" placeholder="Unlimited" /></div>
            <div><label className="block text-sm font-medium mb-1">Per User</label><input type="number" value={form.per_user_limit} onChange={(e) => setForm({...form, per_user_limit: e.target.value})} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" /></div>
          </div>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_active} onChange={(e) => setForm({...form, is_active: e.target.checked})} className="w-4 h-4 rounded" /> Active</label>
          <button onClick={handleSave} className="w-full py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">{editing ? 'Update' : 'Create'}</button>
        </div>
      </Modal>
      <ConfirmDialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)} onConfirm={() => { deleteCoupon(deleteTarget.id); setDeleteTarget(null); }} title="Delete Coupon" message={`Delete "${deleteTarget?.code}"?`} confirmText="Delete" danger />
    </div>
  );
}
