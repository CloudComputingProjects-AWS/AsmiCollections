/**
 * Category Manager — Phase F4 (Screen #23)
 */
import { useEffect, useState } from 'react';
import { useCategoryStore } from '../../stores/adminStores';
import { DataTable, PageHeader, SearchFilterBar, Modal, ConfirmDialog } from '../../components/admin/AdminUI';

const GENDERS = ['men', 'women', 'boys', 'girls', 'unisex'];
const AGE_GROUPS = ['infant', 'kids', 'teen', 'adult', 'senior'];

export default function CategoryManager() {
  const { categories, loading, fetchCategories, createCategory, updateCategory, deleteCategory } = useCategoryStore();
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [form, setForm] = useState({ name: '', gender: 'men', age_group: 'adult', description: '', sort_order: 0, is_active: true });

  useEffect(() => { fetchCategories(); }, []);

  const openEdit = (cat) => { setEditing(cat); setForm({ name: cat.name, gender: cat.gender, age_group: cat.age_group, description: cat.description || '', sort_order: cat.sort_order || 0, is_active: cat.is_active }); setShowForm(true); };
  const openNew = () => { setEditing(null); setForm({ name: '', gender: 'men', age_group: 'adult', description: '', sort_order: 0, is_active: true }); setShowForm(true); };

  const handleSave = async () => {
    try {
      if (editing) { await updateCategory(editing.id, form); }
      else { await createCategory(form); }
      setShowForm(false);
      fetchCategories();
    } catch (err) { alert(err.response?.data?.detail || 'Failed'); }
  };

  const columns = [
    { header: 'Name', key: 'name' },
    { header: 'Gender', render: (r) => <span className="capitalize">{r.gender}</span> },
    { header: 'Age Group', render: (r) => <span className="capitalize">{r.age_group}</span> },
    { header: 'Slug', render: (r) => <span className="text-xs text-gray-500 font-mono">{r.slug}</span> },
    { header: 'Sort', key: 'sort_order' },
    { header: 'Status', render: (r) => <span className={`text-xs font-semibold ${r.is_active ? 'text-emerald-700' : 'text-gray-500'}`}>{r.is_active ? 'Active' : 'Inactive'}</span> },
    { header: 'Actions', render: (r) => (
      <div className="flex gap-1">
        <button onClick={(e) => { e.stopPropagation(); openEdit(r); }} className="p-1.5 hover:bg-blue-50 rounded text-blue-600 text-sm">Edit</button>
        <button onClick={(e) => { e.stopPropagation(); setDeleteTarget(r); }} className="p-1.5 hover:bg-red-50 rounded text-red-500 text-sm">Delete</button>
      </div>
    )},
  ];

  return (
    <div>
      <PageHeader title="Categories" subtitle={`${(categories || []).length} categories`} actions={
        <button onClick={openNew} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">+ Add Category</button>
      } />
      <DataTable columns={columns} data={categories} loading={loading} />
      <Modal open={showForm} onClose={() => setShowForm(false)} title={editing ? 'Edit Category' : 'New Category'}>
        <div className="space-y-3">
          <div><label htmlFor="cat-name" className="block text-sm font-medium mb-1">Name</label><input id="cat-name" type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><label htmlFor="cat-gender" className="block text-sm font-medium mb-1">Gender</label><select id="cat-gender" value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">{GENDERS.map((g) => <option key={g} value={g} className="capitalize">{g}</option>)}</select></div>
            <div><label htmlFor="cat-age-group" className="block text-sm font-medium mb-1">Age Group</label><select id="cat-age-group" value={form.age_group} onChange={(e) => setForm({ ...form, age_group: e.target.value })} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">{AGE_GROUPS.map((a) => <option key={a} value={a} className="capitalize">{a}</option>)}</select></div>
          </div>
          <div><label htmlFor="cat-description" className="block text-sm font-medium mb-1">Description</label><textarea id="cat-description" rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" /></div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} className="w-4 h-4 rounded" /> Active</label>
            <div><label htmlFor="cat-sort-order" className="text-sm font-medium mr-2">Sort Order:</label><input id="cat-sort-order" type="number" value={form.sort_order} onChange={(e) => setForm({ ...form, sort_order: parseInt(e.target.value) || 0 })} className="w-16 px-2 py-1 border border-gray-200 rounded text-sm" /></div>
          </div>
          <button onClick={handleSave} className="w-full py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">{editing ? 'Update' : 'Create'}</button>
        </div>
      </Modal>
      <ConfirmDialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)} onConfirm={() => { deleteCategory(deleteTarget.id); setDeleteTarget(null); }} title="Delete Category" message={`Delete "${deleteTarget?.name}"?`} confirmText="Delete" danger />
    </div>
  );
}
