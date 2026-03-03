/**
 * Attribute Manager — Phase F4 (Screen #22)
 */
import { useEffect, useState } from 'react';
import { useAttributeStore } from '../../stores/adminStores';
import { DataTable, PageHeader, Modal, ConfirmDialog } from '../../components/admin/AdminUI';

export default function AttributeManager() {
  const { attributes, loading, fetchAttributes, createAttribute, updateAttribute, deleteAttribute } = useAttributeStore();
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [form, setForm] = useState({ attribute_key: '', display_name: '', input_type: 'text', options: '', is_filterable: false, is_required: false, sort_order: 0 });

  useEffect(() => { fetchAttributes(); }, []);

  const openEdit = (attr) => {
    setEditing(attr);
    setForm({ attribute_key: attr.attribute_key, display_name: attr.display_name, input_type: attr.input_type, options: (attr.options || []).join(', '), is_filterable: attr.is_filterable, is_required: attr.is_required, sort_order: attr.sort_order || 0 });
    setShowForm(true);
  };

  const handleSave = async () => {
    const payload = { ...form, options: form.options ? form.options.split(',').map((s) => s.trim()).filter(Boolean) : [], sort_order: parseInt(form.sort_order) || 0 };
    try {
      if (editing) { await updateAttribute(editing.id, payload); }
      else { await createAttribute(payload); }
      setShowForm(false);
      fetchAttributes();
    } catch (err) { alert(err.response?.data?.detail || 'Failed'); }
  };

  const columns = [
    { header: 'Key', render: (r) => <span className="font-mono text-xs">{r.attribute_key}</span> },
    { header: 'Display Name', key: 'display_name' },
    { header: 'Type', render: (r) => <span className="capitalize text-xs bg-gray-100 px-2 py-0.5 rounded">{r.input_type}</span> },
    { header: 'Options', render: (r) => <span className="text-xs text-gray-500 max-w-[200px] truncate block">{(r.options || []).join(', ') || '—'}</span> },
    { header: 'Filterable', render: (r) => r.is_filterable ? <span className="text-emerald-600 text-sm">✓</span> : <span className="text-gray-300">—</span> },
    { header: 'Required', render: (r) => r.is_required ? <span className="text-blue-600 text-sm">✓</span> : <span className="text-gray-300">—</span> },
    { header: 'Sort', key: 'sort_order' },
    { header: 'Actions', render: (r) => (
      <div className="flex gap-1">
        <button onClick={(e) => { e.stopPropagation(); openEdit(r); }} className="p-1.5 hover:bg-blue-50 rounded text-blue-600 text-sm">Edit</button>
        <button onClick={(e) => { e.stopPropagation(); setDeleteTarget(r); }} className="p-1.5 hover:bg-red-50 rounded text-red-500 text-sm">Delete</button>
      </div>
    )},
  ];

  return (
    <div>
      <PageHeader title="Attribute Definitions" subtitle="Manage filterable product attributes" actions={
        <button onClick={() => { setEditing(null); setForm({ attribute_key: '', display_name: '', input_type: 'text', options: '', is_filterable: false, is_required: false, sort_order: 0 }); setShowForm(true); }}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">+ Add Attribute</button>
      } />
      <DataTable columns={columns} data={attributes} loading={loading} />
      <Modal open={showForm} onClose={() => setShowForm(false)} title={editing ? 'Edit Attribute' : 'New Attribute'}>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="block text-sm font-medium mb-1">Key</label><input type="text" value={form.attribute_key} onChange={(e) => setForm({ ...form, attribute_key: e.target.value })} disabled={!!editing} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm disabled:bg-gray-50" placeholder="e.g. material" /></div>
            <div><label className="block text-sm font-medium mb-1">Display Name</label><input type="text" value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" /></div>
          </div>
          <div><label className="block text-sm font-medium mb-1">Input Type</label><select value={form.input_type} onChange={(e) => setForm({ ...form, input_type: e.target.value })} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"><option value="text">Text</option><option value="select">Select</option><option value="multiselect">Multi-select</option></select></div>
          {(form.input_type === 'select' || form.input_type === 'multiselect') && (
            <div><label className="block text-sm font-medium mb-1">Options (comma-separated)</label><input type="text" value={form.options} onChange={(e) => setForm({ ...form, options: e.target.value })} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" placeholder="Regular, Slim, Relaxed" /></div>
          )}
          <div className="flex items-center gap-6">
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_filterable} onChange={(e) => setForm({ ...form, is_filterable: e.target.checked })} className="w-4 h-4 rounded" /> Filterable</label>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_required} onChange={(e) => setForm({ ...form, is_required: e.target.checked })} className="w-4 h-4 rounded" /> Required</label>
          </div>
          <button onClick={handleSave} className="w-full py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">{editing ? 'Update' : 'Create'}</button>
        </div>
      </Modal>
      <ConfirmDialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)} onConfirm={() => { deleteAttribute(deleteTarget.id); setDeleteTarget(null); }} title="Delete Attribute" message={`Delete "${deleteTarget?.display_name}"? Products using this attribute won't lose data, but it will no longer appear in forms/filters.`} confirmText="Delete" danger />
    </div>
  );
}
