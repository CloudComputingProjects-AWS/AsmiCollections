/**
 * Product Manager — Phase F4 (Screen #20)
 * CRUD table + apparel attribute columns.
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProductStore } from '../../stores/adminStores';
import { DataTable, PageHeader, SearchFilterBar, Pagination, StatusBadge, ConfirmDialog } from '../../components/admin/AdminUI';
import apiClient from '../../api/apiClient';
import toast from 'react-hot-toast';

export default function ProductManager() {
  const navigate = useNavigate();
  const { products, total, loading, fetchProducts, deleteProduct } = useProductStore();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState({});
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [duplicateTarget, setDuplicateTarget] = useState(null);
  const [duplicateCategory, setDuplicateCategory] = useState('');
  const [duplicating, setDuplicating] = useState(false);
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    fetchProducts({ page, limit: 20, search, ...filters });
  }, [page, search, filters]);

  useEffect(() => {
    apiClient.get('/admin/categories').then((res) => setCategories(res.data)).catch(() => {});
  }, []);

  const handleDuplicate = async () => {
    if (!duplicateTarget || !duplicateCategory) return;
    setDuplicating(true);
    try {
      const res = await apiClient.post(`/admin/products/${duplicateTarget.id}/duplicate`, {
        target_category_id: duplicateCategory,
        map_sizes: true,
      });
      toast.success(`Duplicated "${duplicateTarget.title}" \u2192 ${res.data.new_title} (${res.data.variants_created} variants)`);
      setDuplicateTarget(null);
      setDuplicateCategory('');
      fetchProducts({ page, limit: 20, search, ...filters });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Duplication failed');
    }
    setDuplicating(false);
  };

  const columns = [
    {
      header: 'Product',
      render: (row) => (
        <div className="flex items-center gap-3">
          {row.primary_image_url ? (
            <img src={row.primary_image_url} alt="" className="w-10 h-10 rounded-lg object-cover" />
          ) : (
            <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center text-gray-600 text-xs">No img</div>
          )}
          <div>
            <div className="font-medium text-gray-900 max-w-[200px] truncate">{row.title}</div>
            <div className="text-xs text-gray-500">{row.brand || '\u2014'}</div>
          </div>
        </div>
      ),
    },
    { header: 'Category', render: (row) => { const cat = categories.find(c => c.id === row.category_id); return <span className="text-sm">{cat ? cat.name : '\u2014'}</span>; } },
    { header: 'Gender', render: (row) => {
      const colors = { men: 'bg-blue-100 text-blue-700', women: 'bg-pink-100 text-pink-700', boys: 'bg-cyan-100 text-cyan-700', girls: 'bg-purple-100 text-purple-700', unisex: 'bg-gray-100 text-gray-700' };
      const gender = (categories.find(c => c.id === row.category_id)?.gender || '\u2014').toLowerCase();
      return <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colors[gender] || 'bg-gray-100 text-gray-600'}`}>{gender}</span>;
    }},
    { header: 'Price', render: (row) => (
      <div>
        <span className="font-medium">{'\u20B9'}{row.base_price}</span>

      </div>
    )},
    { header: 'HSN', key: 'hsn_code' },
    { header: 'GST', render: (row) => `${row.gst_rate || 0}%` },
    { header: 'Variants', render: (row) => <span className="text-sm">{row.variants?.length || 0}</span> },
    { header: 'Stock', render: (row) => {
      const totalStock = row.variants?.reduce((s,v) => s + (v.stock_quantity || 0), 0) || 0;
      return <span className={`text-sm font-medium ${totalStock < 10 ? "text-red-600" : "text-gray-700"}`}>{totalStock}</span>;
    }},
    { header: 'Status', render: (row) => (
      <div className="flex items-center gap-1">
        <StatusBadge status={row.is_active ? 'active' : 'inactive'} />
        {row.is_featured && <span className="text-xs text-amber-500">{'\u2605'}</span>}
      </div>
    )},
    {
      header: 'Actions',
      render: (row) => (
        <div className="flex items-center gap-1">
          <button onClick={(e) => { e.stopPropagation(); navigate(`/admin/products/${row.id}/edit`); }}
            className="p-1.5 hover:bg-blue-50 rounded-lg text-blue-600" title="Edit" aria-label={`Edit ${row.title}`}>
            {'\u270E'}
          </button>
          <button onClick={(e) => { e.stopPropagation(); setDuplicateTarget(row); }}
            className="p-1.5 hover:bg-green-50 rounded-lg text-green-600" title="Duplicate to..." aria-label={`Duplicate ${row.title}`}>
            {'\u29C9'}
          </button>
          <button onClick={(e) => { e.stopPropagation(); setDeleteTarget(row); }}
            className="p-1.5 hover:bg-red-50 rounded-lg text-red-500" title="Delete" aria-label={`Delete ${row.title}`}>
            {'\uD83D\uDDD1'}
          </button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Products"
        subtitle={`${total} products`}
        actions={
          <div className="flex gap-2">
            <button onClick={() => navigate('/admin/products/bulk-upload')}
              className="px-3 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">
              {'\uD83D\uDCE4'} Bulk Upload
            </button>
            <button onClick={() => navigate('/admin/products/new')}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">
              + Add Product
            </button>
          </div>
        }
      />

      <SearchFilterBar
        searchPlaceholder="Search by title, SKU, brand..."
        onSearch={setSearch}
        filters={[
          { key: 'is_active', label: 'Status', options: [{ value: 'true', label: 'Active' }, { value: 'false', label: 'Inactive' }] },
          { key: 'is_featured', label: 'Featured', options: [{ value: 'true', label: 'Yes' }, { value: 'false', label: 'No' }] },
          { key: 'gender', label: 'Gender', options: [{ value: '', label: 'All Categories' }, { value: 'men', label: 'Men' }, { value: 'women', label: 'Women' }, { value: 'boys', label: 'Boys' }, { value: 'girls', label: 'Girls' }, { value: 'unisex', label: 'Unisex' }] },
        ]}
        values={filters}
        onFilter={(key, val) => setFilters((f) => ({ ...f, [key]: val || undefined }))}
      />

      <DataTable columns={columns} data={products} loading={loading} onRowClick={(row) => navigate(`/admin/products/${row.id}/edit`)} />
      <Pagination page={page} total={total} limit={20} onPageChange={setPage} />

      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => deleteProduct(deleteTarget.id)}
        title="Delete Product"
        message={`Are you sure you want to delete "${deleteTarget?.title}"? This action uses soft delete and can be recovered.`}
        confirmText="Delete"
        danger
      />

      {/* Duplicate Product Modal */}
      {duplicateTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-bold text-gray-900 mb-1">Duplicate Product</h3>
            <p className="text-sm text-gray-500 mb-4">Clone &ldquo;{duplicateTarget.title}&rdquo; to a different category. Sizes will be auto-mapped.</p>
            <label htmlFor="duplicate-target-category" className="block text-sm font-medium text-gray-700 mb-1">Target Category</label>
            <select id="duplicate-target-category" value={duplicateCategory} onChange={(e) => setDuplicateCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none mb-4">
              <option value="">Select target category</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.gender} / {c.age_group} / {c.name}</option>
              ))}
            </select>
            <div className="flex justify-end gap-2">
              <button onClick={() => { setDuplicateTarget(null); setDuplicateCategory(''); }}
                className="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">Cancel</button>
              <button onClick={handleDuplicate} disabled={!duplicateCategory || duplicating}
                className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50">
                {duplicating ? 'Duplicating...' : 'Duplicate'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
