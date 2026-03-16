/**
 * Product Form - Phase F5 (Screen #21)
 * Add/Edit product with dynamic attribute fields, variants, images.
 */
import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useProductStore, useCategoryStore, useAttributeStore } from '../../stores/adminStores';
import { PageHeader } from '../../components/admin/AdminUI';
import { imageApi, variantApi } from '../../api/adminApi';

const GST_RATES = [0, 5, 12, 18, 28];
const SIZE_SUGGESTIONS = {
  men: ['S', 'M', 'L', 'XL'],
  women: ['S', 'M', 'L', 'XL'],
  boys: ['4-6', '7-9', '10-12', '13-15', '16+'],
  girls: ['4-6', '7-9', '10-12', '13-15', '16+'],
  unisex: ['S', 'M', 'L', 'XL'],
};
const WAIST_SIZES = ['26', '28', '30', '32', '34', '36', '38'];
const MAX_IMAGES = 8;
const MAX_FILE_SIZE_MB = 5;
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

export default function ProductForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = !!id;
  const { product, fetchProduct, createProduct, updateProduct } = useProductStore();
  const { categories, fetchCategories } = useCategoryStore();
  const { attributes, fetchAttributes } = useAttributeStore();

  const [form, setForm] = useState({
    title: '', description: '', category_id: '', brand: '',
    base_price: '', sale_price: '', hsn_code: '', gst_rate: 5,
    attributes: {}, tags: [], meta_title: '', meta_description: '',
    is_active: true, is_featured: false,
  });
  const [variants, setVariants] = useState([]);
  const [images, setImages] = useState([]);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState({});
  const [activeTab, setActiveTab] = useState('basic');

  // Image upload state
  const [uploadDragging, setUploadDragging] = useState(false);
  const [uploadErrors, setUploadErrors] = useState([]);

  useEffect(() => {
    fetchCategories();
    fetchAttributes();
    if (isEdit) fetchProduct(id);
  }, [id]);

  useEffect(() => {
    if (isEdit && product) {
      setForm({
        title: product.title || '', description: product.description || '',
        category_id: product.category_id || '', brand: product.brand || '',
        base_price: product.base_price || '', sale_price: product.sale_price || '',
        hsn_code: product.hsn_code || '', gst_rate: product.gst_rate ?? 5,
        meta_title: product.meta_title || '', meta_description: product.meta_description || '',
        is_active: product.is_active ?? true, is_featured: product.is_featured ?? false,
      });
      setVariants(product.variants || []);
      setImages(product.images || []);
    }
  }, [product, isEdit]);

  const updateField = (key, value) => setForm((f) => ({ ...f, [key]: value }));
  const updateAttr = (key, value) => setForm((f) => ({ ...f, attributes: { ...f.attributes, [key]: value } }));
  const addVariant = () => setVariants((v) => [...v, { size: '', color: '', color_hex: '#000000', sku: '', stock_quantity: 0, price_override: '', is_new: true }]);
  const updateVariant = (i, key, val) => setVariants((v) => v.map((item, idx) => idx === i ? { ...item, [key]: val } : item));
  const removeVariant = (i) => setVariants((v) => v.filter((_, idx) => idx !== i));

  const getSelectedGender = () => {
    if (!form.category_id || !categories) return null;
    const cat = categories.find((c) => String(c.id) === String(form.category_id));
    return cat?.gender || null;
  };

  const addAllStandardSizes = () => {
    const gender = getSelectedGender();
    const sizes = SIZE_SUGGESTIONS[gender] || SIZE_SUGGESTIONS.unisex;
    const existingSizes = variants.map((v) => v.size);
    const newVariants = sizes
      .filter((s) => !existingSizes.includes(s))
      .map((s) => ({ size: s, color: '', color_hex: '#000000', sku: '', stock_quantity: 0, price_override: '', is_new: true }));
    if (newVariants.length > 0) {
      setVariants((v) => [...v, ...newVariants]);
    }
  };

  const addWaistSizes = () => {
    const existingSizes = variants.map((v) => v.size);
    const newVariants = WAIST_SIZES
      .filter((s) => !existingSizes.includes(s))
      .map((s) => ({ size: s, color: '', color_hex: '#000000', sku: '', stock_quantity: 0, price_override: '', is_new: true }));
    if (newVariants.length > 0) {
      setVariants((v) => [...v, ...newVariants]);
    }
  };

  // ─── IMAGE UPLOAD HANDLERS ────────────────────────────────────────────────

  /**
   * Validate files before upload.
   * Returns { valid: File[], errors: string[] }
   */
  const validateFiles = useCallback((files) => {
    const valid = [];
    const errs = [];
    const currentCount = images.length;

    for (const file of files) {
      if (!ALLOWED_TYPES.includes(file.type)) {
        errs.push(`"${file.name}" — unsupported format. JPG, PNG, WebP only.`);
        continue;
      }
      if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
        errs.push(`"${file.name}" — exceeds 5MB limit.`);
        continue;
      }
      if (currentCount + valid.length >= MAX_IMAGES) {
        errs.push(`Maximum ${MAX_IMAGES} images allowed. "${file.name}" skipped.`);
        break;
      }
      valid.push(file);
    }
    return { valid, errs };
  }, [images]);

  /**
   * Upload a single file via pre-signed URL flow:
   * 1. POST /admin/products/{id}/images/upload-url  → get presigned URL + image_id
   * 2. PUT presigned URL directly to S3 with file bytes
   * 3. Update local images state: set processing_status = 'pending' (Lambda processes async)
   */
  const uploadFile = useCallback(async (file) => {
    // Create local preview entry with 'uploading' status immediately
    const localPreview = URL.createObjectURL(file);
    const tempId = `temp-${Date.now()}-${Math.random()}`;

    setImages((prev) => [
      ...prev,
      {
        id: null,
        tempId,
        localPreview,
        processing_status: 'uploading',
        is_primary: false,
        original_url: null,
        processed_url: null,
        medium_url: null,
        thumbnail_url: null,
      },
    ]);

    try {
      // Step 1: Get pre-signed URL from backend
      const { data } = await imageApi.getUploadUrl(id, {
        filename: file.name,
        content_type: file.type,
      });
      // data = { upload_url, image_id, s3_key, expires_in }

      // Step 2: PUT file directly to S3 using pre-signed URL
      // Must use native fetch — not axios — because pre-signed S3 URLs
      // reject the Authorization header that axios interceptors add.
      const s3Response = await fetch(data.upload_url, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type,
        },
      });

      if (!s3Response.ok) {
        throw new Error(`S3 upload failed with status ${s3Response.status}`);
      }

      // Step 3: Replace temp entry with real image_id + pending status
      // Lambda will process async and update processed_url/thumbnail_url via callback
      setImages((prev) =>
        prev.map((img) =>
          img.tempId === tempId
            ? {
                id: data.image_id,
                localPreview,
                processing_status: 'pending',
                is_primary: false,
                original_url: null,
                processed_url: null,
                medium_url: null,
                thumbnail_url: null,
                s3_key: data.s3_key,
              }
            : img
        )
      );
    } catch (err) {
      // Remove failed temp entry from images list
      setImages((prev) => prev.filter((img) => img.tempId !== tempId));
      URL.revokeObjectURL(localPreview);
      // Surface error to user
      setUploadErrors((prev) => [
        ...prev,
        `Failed to upload "${file.name}": ${err.message || 'Unknown error'}`,
      ]);
    }
  }, [id, images]);

  /**
   * Handle files from either drag-drop or file input.
   */
  const handleImageFiles = useCallback(async (files) => {
    setUploadErrors([]);
    const { valid, errs } = validateFiles(files);
    if (errs.length > 0) setUploadErrors(errs);
    // Upload valid files sequentially to avoid race conditions on images state
    for (const file of valid) {
      await uploadFile(file);
    }
  }, [validateFiles, uploadFile]);

  const handleImageDrop = useCallback((e) => {
    e.preventDefault();
    setUploadDragging(false);
    const files = Array.from(e.dataTransfer.files);
    handleImageFiles(files);
  }, [handleImageFiles]);

  const handleSetPrimary = useCallback(async (imageId) => {
    try {
      await imageApi.setPrimary(id, imageId);
      setImages((prev) =>
        prev.map((img) => ({ ...img, is_primary: img.id === imageId }))
      );
    } catch (err) {
      setUploadErrors([`Failed to set primary image: ${err.response?.data?.detail || err.message}`]);
    }
  }, [id]);

  const handleDeleteImage = useCallback(async (imageId) => {
    try {
      await imageApi.delete(id, imageId);
      setImages((prev) => prev.filter((img) => img.id !== imageId));
    } catch (err) {
      setUploadErrors([`Failed to delete image: ${err.response?.data?.detail || err.message}`]);
    }
  }, [id]);

  // ─── END IMAGE UPLOAD HANDLERS ────────────────────────────────────────────

  const validate = () => {
    const e = {};
    if (!form.title.trim()) e.title = 'Required';
    if (!form.category_id) e.category_id = 'Required';
    if (!form.base_price || form.base_price <= 0) e.base_price = 'Must be > 0';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSave = async () => {
    if (!validate()) return;
    setSaving(true);
    try {
      const payload = {
        ...form,
        base_price: parseFloat(form.base_price),
        sale_price: form.sale_price ? parseFloat(form.sale_price) : null,
        gst_rate: parseFloat(form.gst_rate),
      };
      if (isEdit) {
        await updateProduct(id, payload);
      } else {
        const created = await createProduct(payload);
        if (variants.length > 0) {
          for (const v of variants) {
            await variantApi.create(created.id, {
              size: v.size,
              color: v.color,
              color_hex: v.color_hex,
              stock_quantity: parseInt(v.stock_quantity),
              price_override: v.price_override ? parseFloat(v.price_override) : null,
            });
          }
        }
      }
      navigate('/admin/products');
    } catch (err) {
      setErrors({ _form: err.response?.data?.detail || 'Save failed' });
    } finally {
      setSaving(false);
    }
  };

  const tabs = [
    { key: 'basic', label: 'Basic Info' },
    { key: 'pricing', label: 'Pricing & Tax' },
    { key: 'attributes', label: 'Attributes' },
    { key: 'variants', label: `Variants (${variants.length})` },
    { key: 'images', label: `Images (${images.length})` },
    { key: 'seo', label: 'SEO' },
  ];

  return (
    <div>
      <PageHeader
        title={isEdit ? 'Edit Product' : 'New Product'}
        subtitle={isEdit ? product?.title : 'Create a new product'}
        actions={
          <div className="flex gap-2">
            <button onClick={() => navigate('/admin/products')} className="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">Cancel</button>
            <button onClick={handleSave} disabled={saving}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50">
              {saving ? 'Saving...' : isEdit ? 'Update' : 'Create Product'}
            </button>
          </div>
        }
      />

      {errors._form && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{errors._form}</div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-5 bg-gray-50 rounded-lg p-1 overflow-x-auto" role="tablist">
        {tabs.map((tab) => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)}
            role="tab"
            aria-selected={activeTab === tab.key}
            className={`px-4 py-2 text-sm font-medium rounded-md whitespace-nowrap transition-colors ${activeTab === tab.key ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}>
            {tab.label}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-gray-100 p-5">

        {/* Basic Info */}
        {activeTab === 'basic' && (
          <div className="space-y-4 max-w-2xl">
            <div>
              <label htmlFor="pf-title" className="block text-sm font-medium text-gray-700 mb-1">Product Title *</label>
              <input id="pf-title" type="text" value={form.title} onChange={(e) => updateField('title', e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none ${errors.title ? 'border-red-300' : 'border-gray-200'}`} />
              {errors.title && <p className="text-xs text-red-500 mt-1">{errors.title}</p>}
            </div>
            <div>
              <label htmlFor="pf-description" className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea id="pf-description" rows={4} value={form.description} onChange={(e) => updateField('description', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="pf-category" className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
                <select id="pf-category" value={form.category_id} onChange={(e) => updateField('category_id', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg text-sm outline-none ${errors.category_id ? 'border-red-300' : 'border-gray-200'}`}>
                  <option value="">Select category</option>
                  {(categories || []).map((c) => (
                    <option key={c.id} value={c.id}>{c.gender} / {c.age_group} / {c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="pf-brand" className="block text-sm font-medium text-gray-700 mb-1">Brand</label>
                <input id="pf-brand" type="text" value={form.brand} onChange={(e) => updateField('brand', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none" />
              </div>
            </div>
            <div className="flex items-center gap-6">
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.is_active} onChange={(e) => updateField('is_active', e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 text-blue-600" /> Active
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.is_featured} onChange={(e) => updateField('is_featured', e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 text-amber-500" /> Featured {'\u2605'}
              </label>
            </div>
          </div>
        )}

        {/* Pricing & Tax */}
        {activeTab === 'pricing' && (
          <div className="space-y-4 max-w-lg">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="pf-base-price" className="block text-sm font-medium text-gray-700 mb-1">Base Price (INR) *</label>
                <input id="pf-base-price" type="number" step="0.01" value={form.base_price} onChange={(e) => updateField('base_price', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg text-sm outline-none ${errors.base_price ? 'border-red-300' : 'border-gray-200'}`} />
              </div>
              <div>
                <label htmlFor="pf-sale-price" className="block text-sm font-medium text-gray-700 mb-1">Sale Price</label>
                <input id="pf-sale-price" type="number" step="0.01" value={form.sale_price} onChange={(e) => updateField('sale_price', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none" placeholder="Optional" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="pf-hsn" className="block text-sm font-medium text-gray-700 mb-1">HSN Code</label>
                <input id="pf-hsn" type="text" value={form.hsn_code} onChange={(e) => updateField('hsn_code', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none" placeholder="e.g. 6109" />
              </div>
              <div>
                <label htmlFor="pf-gst-rate" className="block text-sm font-medium text-gray-700 mb-1">GST Rate</label>
                <select id="pf-gst-rate" value={form.gst_rate} onChange={(e) => updateField('gst_rate', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none">
                  {GST_RATES.map((r) => <option key={r} value={r}>{r}%</option>)}
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Apparel Attributes (dynamic) */}
        {activeTab === 'attributes' && (
          <div className="space-y-4 max-w-2xl">
            <p className="text-sm text-gray-500 mb-2">Apparel-specific attributes (auto-populated from attribute definitions)</p>
            {(attributes || []).map((attr) => {
              const fieldId = `pf-attr-${attr.attribute_key}`;
              return (
                <div key={attr.id || attr.attribute_key}>
                  <label htmlFor={attr.input_type !== 'multiselect' ? fieldId : undefined} className="block text-sm font-medium text-gray-700 mb-1">
                    {attr.display_name} {attr.is_required && <span className="text-red-500">*</span>}
                  </label>
                  {attr.input_type === 'select' ? (
                    <select id={fieldId} value={form.attributes[attr.attribute_key] || ''}
                      onChange={(e) => updateAttr(attr.attribute_key, e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none">
                      <option value="">Select {attr.display_name}</option>
                      {(attr.options || []).map((opt) => <option key={opt} value={opt}>{opt}</option>)}
                    </select>
                  ) : attr.input_type === 'multiselect' ? (
                    <div className="flex flex-wrap gap-2" role="group" aria-label={attr.display_name}>
                      {(attr.options || []).map((opt) => {
                        const vals = Array.isArray(form.attributes[attr.attribute_key]) ? form.attributes[attr.attribute_key] : [];
                        const checked = vals.includes(opt);
                        return (
                          <label key={opt} className="flex items-center gap-1.5 text-sm">
                            <input type="checkbox" checked={checked}
                              onChange={(e) => {
                                const newVals = e.target.checked ? [...vals, opt] : vals.filter((v) => v !== opt);
                                updateAttr(attr.attribute_key, newVals);
                              }}
                              className="w-3.5 h-3.5 rounded border-gray-300 text-blue-600" />
                            {opt}
                          </label>
                        );
                      })}
                    </div>
                  ) : (
                    <input id={fieldId} type="text" value={form.attributes[attr.attribute_key] || ''}
                      onChange={(e) => updateAttr(attr.attribute_key, e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none" />
                  )}
                </div>
              );
            })}
            {(!attributes || attributes.length === 0) && (
              <p className="text-sm text-gray-500">No attribute definitions found. Create them in the Attribute Manager.</p>
            )}
          </div>
        )}

        {/* Variants */}
        {activeTab === 'variants' && (
          <div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="px-3 py-2 text-left font-semibold text-gray-600">Size</th>
                    <th className="px-3 py-2 text-left font-semibold text-gray-600">Color</th>
                    <th className="px-3 py-2 text-left font-semibold text-gray-600">Hex</th>
                    <th className="px-3 py-2 text-left font-semibold text-gray-600">SKU</th>
                    <th className="px-3 py-2 text-left font-semibold text-gray-600">Stock</th>
                    <th className="px-3 py-2 text-left font-semibold text-gray-600">Price Override</th>
                    <th className="px-3 py-2"><span className="sr-only">Actions</span></th>
                  </tr>
                </thead>
                <tbody>
                  {variants.map((v, i) => (
                    <tr key={i} className="border-t border-gray-100">
                      <td className="px-3 py-2"><input type="text" value={v.size || ''} onChange={(e) => updateVariant(i, 'size', e.target.value)} aria-label={`Size for variant ${i + 1}`} className="w-16 px-2 py-1 border border-gray-200 rounded text-sm" /></td>
                      <td className="px-3 py-2"><input type="text" value={v.color || ''} onChange={(e) => updateVariant(i, 'color', e.target.value)} aria-label={`Color for variant ${i + 1}`} className="w-20 px-2 py-1 border border-gray-200 rounded text-sm" /></td>
                      <td className="px-3 py-2"><input type="color" value={v.color_hex || '#000000'} onChange={(e) => updateVariant(i, 'color_hex', e.target.value)} aria-label={`Color hex for variant ${i + 1}`} className="w-10 h-7 border border-gray-200 rounded cursor-pointer" /></td>
                      <td className="px-3 py-2"><input type="text" value={v.sku || ''} onChange={(e) => updateVariant(i, 'sku', e.target.value)} aria-label={`SKU for variant ${i + 1}`} className="w-28 px-2 py-1 border border-gray-200 rounded text-sm" placeholder="Auto" /></td>
                      <td className="px-3 py-2"><input type="number" value={v.stock_quantity || 0} onChange={(e) => updateVariant(i, 'stock_quantity', e.target.value)} aria-label={`Stock for variant ${i + 1}`} className="w-20 px-2 py-1 border border-gray-200 rounded text-sm" /></td>
                      <td className="px-3 py-2"><input type="number" step="0.01" value={v.price_override || ''} onChange={(e) => updateVariant(i, 'price_override', e.target.value)} aria-label={`Price override for variant ${i + 1}`} className="w-24 px-2 py-1 border border-gray-200 rounded text-sm" placeholder={'\u2014'} /></td>
                      <td className="px-3 py-2"><button type="button" onClick={() => removeVariant(i)} className="text-red-500 hover:text-red-700" aria-label={`Remove variant ${i + 1}`}>{'\u2718'}</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button type="button" onClick={addVariant} className="mt-3 px-4 py-2 text-sm border border-dashed border-gray-300 rounded-lg hover:border-blue-400 hover:text-blue-600">
              + Add Variant
            </button>
            <button type="button" onClick={addAllStandardSizes} className="mt-3 ml-2 px-4 py-2 text-sm border border-dashed border-green-300 rounded-lg hover:border-green-500 hover:text-green-600">
              + Add All Standard Sizes {getSelectedGender() && `(${(SIZE_SUGGESTIONS[getSelectedGender()] || []).join(', ')})`}
            </button>
            {['men', 'women', 'unisex'].includes(getSelectedGender()) && (
              <button type="button" onClick={addWaistSizes} className="mt-3 ml-2 px-4 py-2 text-sm border border-dashed border-purple-300 rounded-lg hover:border-purple-500 hover:text-purple-600">
                + Add Waist Sizes (26-38)
              </button>
            )}
          </div>
        )}

        {/* Images */}
        {activeTab === 'images' && (
          <div className="space-y-4">

            {isEdit ? (
              <div>
                {/* Drop zone */}
                <div
                  role="button"
                  tabIndex={0}
                  aria-label="Upload images by clicking or dragging files here"
                  className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                    uploadDragging ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
                  }`}
                  onDragOver={(e) => { e.preventDefault(); setUploadDragging(true); }}
                  onDragLeave={() => setUploadDragging(false)}
                  onDrop={handleImageDrop}
                  onClick={() => document.getElementById('imageFileInput').click()}
                  onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') document.getElementById('imageFileInput').click(); }}
                >
                  <input
                    id="imageFileInput"
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    multiple
                    className="hidden"
                    onChange={(e) => { handleImageFiles(Array.from(e.target.files)); e.target.value = ''; }}
                  />
                  <svg className="mx-auto mb-2 w-8 h-8 text-gray-400" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                  </svg>
                  <p className="text-sm font-medium text-gray-700">Drag and drop images here, or click to select</p>
                  <p className="text-xs text-gray-500 mt-1">JPG, PNG, WebP only — max 5MB each — up to {MAX_IMAGES} images total</p>
                  <p className="text-xs text-gray-400 mt-1">{images.length} / {MAX_IMAGES} uploaded</p>
                </div>

                {/* Upload errors */}
                {uploadErrors.length > 0 && (
                  <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg space-y-1">
                    {uploadErrors.map((err, i) => (
                      <p key={i} className="text-xs text-red-600">{err}</p>
                    ))}
                    <button
                      type="button"
                      onClick={() => setUploadErrors([])}
                      className="text-xs text-red-500 underline mt-1"
                    >
                      Dismiss
                    </button>
                  </div>
                )}

                {/* Image grid */}
                {images.length > 0 && (
                  <div className="grid grid-cols-4 gap-4 mt-4">
                    {images.map((img, i) => (
                      <div
                        key={img.id || img.tempId || i}
                        className="relative group rounded-lg overflow-hidden border border-gray-200 bg-gray-50"
                      >
                        <img
                          src={img.thumbnail_url || img.processed_url || img.original_url || img.localPreview}
                          alt={`Product image ${i + 1}`}
                          className="w-full aspect-square object-cover"
                        />

                        {/* Primary badge */}
                        {img.is_primary && (
                          <span className="absolute top-2 left-2 bg-blue-600 text-white text-xs px-1.5 py-0.5 rounded">
                            Primary
                          </span>
                        )}

                        {/* Status badge */}
                        <span className={`absolute top-2 right-2 text-xs px-1.5 py-0.5 rounded ${
                          img.processing_status === 'completed'  ? 'bg-green-100 text-green-700' :
                          img.processing_status === 'processing' ? 'bg-yellow-100 text-yellow-700' :
                          img.processing_status === 'failed'     ? 'bg-red-100 text-red-700' :
                          img.processing_status === 'uploading'  ? 'bg-blue-100 text-blue-700' :
                                                                    'bg-gray-100 text-gray-600'
                        }`}>
                          {img.processing_status || 'pending'}
                        </span>

                        {/* Uploading spinner overlay */}
                        {img.processing_status === 'uploading' && (
                          <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center">
                            <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          </div>
                        )}

                        {/* Action buttons — shown on hover, hidden while uploading */}
                        {img.processing_status !== 'uploading' && img.id && (
                          <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all flex items-end justify-center pb-2 gap-2 opacity-0 group-hover:opacity-100">
                            {!img.is_primary && (
                              <button
                                type="button"
                                onClick={() => handleSetPrimary(img.id)}
                                className="bg-white text-xs text-blue-700 px-2 py-1 rounded shadow hover:bg-blue-50"
                              >
                                Set Primary
                              </button>
                            )}
                            <button
                              type="button"
                              onClick={() => handleDeleteImage(img.id)}
                              className="bg-white text-xs text-red-600 px-2 py-1 rounded shadow hover:bg-red-50"
                            >
                              Delete
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {images.length === 0 && (
                  <p className="text-sm text-gray-400 mt-4 text-center">No images uploaded yet.</p>
                )}

                {/* Processing note */}
                <p className="text-xs text-gray-400 mt-3">
                  Images with status &quot;pending&quot; are queued for processing. Processed variants (thumbnail, medium, full) are generated automatically by Lambda within 1-2 minutes.
                </p>
              </div>
            ) : (
              <div className="text-center py-10">
                <p className="text-sm text-gray-500">Save the product first, then upload images.</p>
                <p className="text-xs text-gray-400 mt-1">Images can only be added after the product record is created.</p>
              </div>
            )}
          </div>
        )}

        {/* SEO */}
        {activeTab === 'seo' && (
          <div className="space-y-4 max-w-2xl">
            <div>
              <label htmlFor="pf-meta-title" className="block text-sm font-medium text-gray-700 mb-1">Meta Title</label>
              <input id="pf-meta-title" type="text" value={form.meta_title} onChange={(e) => updateField('meta_title', e.target.value)} maxLength={200}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none" />
              <p className="text-xs text-gray-500 mt-1">{form.meta_title.length}/200</p>
            </div>
            <div>
              <label htmlFor="pf-meta-desc" className="block text-sm font-medium text-gray-700 mb-1">Meta Description</label>
              <textarea id="pf-meta-desc" rows={3} value={form.meta_description} onChange={(e) => updateField('meta_description', e.target.value)} maxLength={500}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none" />
              <p className="text-xs text-gray-500 mt-1">{form.meta_description.length}/500</p>
            </div>
            <div>
              <label htmlFor="pf-tags" className="block text-sm font-medium text-gray-700 mb-1">Tags</label>
              <input id="pf-tags" type="text" value={(form.tags || []).join(', ')}
                onChange={(e) => updateField('tags', e.target.value.split(',').map((t) => t.trim()).filter(Boolean))}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none" placeholder="casual, summer, cotton" />
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
