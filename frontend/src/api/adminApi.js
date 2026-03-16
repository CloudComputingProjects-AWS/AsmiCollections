/**
 * Admin API Client — Phase F4
 * All admin endpoint calls organized by domain.
 */
import apiClient from './apiClient';

// ——— Dashboard ———————————————————————
export const dashboardApi = {
  getStats: () => apiClient.get('/admin/dashboard/stats'),
  getRevenueChart: (params) => apiClient.get('/admin/dashboard/revenue-trend', { params }),
  getTopProducts: (params) => apiClient.get('/admin/dashboard/top-products', { params }),
  getAlerts: () => apiClient.get('/admin/dashboard/low-stock'),
};

// ——— Products ————————————————————————
export const productApi = {
  list: (params) => apiClient.get('/admin/products', { params }),      
  get: (id) => apiClient.get(`/admin/products/${id}`),
  create: (data) => apiClient.post('/admin/products', data),
  update: (id, data) => apiClient.put(`/admin/products/${id}`, data),  
  delete: (id) => apiClient.delete(`/admin/products/${id}`),
  bulkUpload: (formData) => apiClient.post('/admin/products/bulk-upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
};

// ——— Variants ————————————————————————
export const variantApi = {
  list: (productId) => apiClient.get(`/admin/products/${productId}`).then(res => ({ data: (res.data.product || res.data).variants || [] })),
  create: (productId, data) => apiClient.post('/admin/variants', { ...data, product_id: productId }),
  update: (productId, variantId, data) =>
    apiClient.put(`/admin/variants/${variantId}`, data),
  delete: (productId, variantId) =>
    apiClient.delete(`/admin/variants/${variantId}`),
};

// ——— Categories ——————————————————————
export const categoryApi = {
  list: (params) => apiClient.get('/admin/categories', { params }),    
  get: (id) => apiClient.get(`/admin/categories/${id}`),
  create: (data) => apiClient.post('/admin/categories', data),
  update: (id, data) => apiClient.put(`/admin/categories/${id}`, data),
  delete: (id) => apiClient.delete(`/admin/categories/${id}`),
};

// ——— Attribute Definitions ———————————
export const attributeApi = {
  list: () => apiClient.get('/admin/attribute-definitions'),
  create: (data) => apiClient.post('/admin/attribute-definitions', data),
  update: (id, data) => apiClient.put(`/admin/attribute-definitions/${id}`, data),
  delete: (id) => apiClient.delete(`/admin/attribute-definitions/${id}`),
};

// ——— Inventory ———————————————————————
export const inventoryApi = {
  list: (params) => apiClient.get('/admin/inventory', { params }),     
  update: (variantId, data) => apiClient.put(`/admin/inventory/${variantId}`, data),
  bulkUpdate: (data) => apiClient.post('/admin/inventory/bulk-update', data),
  lowStock: (params) => apiClient.get('/admin/inventory/low-stock', { params }),
};

// ——— Orders ——————————————————————————        
export const orderApi = {
  list: (params) => apiClient.get('/admin/orders', { params }),        
  get: (id) => apiClient.get(`/admin/orders/${id}`),
  transition: (id, data) => apiClient.put(`/admin/orders/${id}/transition`, data),
  history: (id) => apiClient.get(`/admin/orders/${id}/history`),       
};

// ——— Returns & Refunds ——————————————
export const returnApi = {
  list: (params) => apiClient.get('/admin/returns', { params }),       
  get: (id) => apiClient.get(`/admin/returns/${id}`),
  approve: (id, data) => apiClient.post(`/admin/returns/${id}/approve`, data),
  reject: (id, data) => apiClient.post(`/admin/returns/${id}/reject`, data),
  receive: (id) => apiClient.post(`/admin/returns/${id}/receive`),     
};

export const refundApi = {
  initiate: (data) => apiClient.post('/admin/payments/refund', data),  
};

// ——— Coupons —————————————————————————
export const couponApi = {
  list: (params) => apiClient.get('/admin/coupons', { params }),       
  get: (id) => apiClient.get(`/admin/coupons/${id}`),
  create: (data) => apiClient.post('/admin/coupons', data),
  update: (id, data) => apiClient.put(`/admin/coupons/${id}`, data),   
  delete: (id) => apiClient.delete(`/admin/coupons/${id}`),
};

// ——— Invoices & Credit Notes —————————
export const invoiceApi = {
  list: (params) => apiClient.get('/admin/invoices', { params }),      
  download: (id) => apiClient.get(`/admin/invoices/${id}/download`, { responseType: 'blob' }),
  creditNotes: (params) => apiClient.get('/admin/credit-notes', { params }),
  downloadCN: (id) => apiClient.get(`/admin/credit-notes/${id}/download`, { responseType: 'blob' }),
};

// ——— Users ———————————————————————————      
export const userApi = {
  list: (params) => apiClient.get('/admin/users', { params }),
  get: (id) => apiClient.get(`/admin/users/${id}`),
  updateRole: (id, data) => apiClient.put(`/admin/users/${id}/role`, data),
  toggleActive: (id) => apiClient.put(`/admin/users/${id}/status`),    
};

// ——— Audit Logs ——————————————————————
export const auditApi = {
  list: (params) => apiClient.get('/admin/audit-logs', { params }),    
  archivePreview: (months = 12) => apiClient.post('/admin/audit-logs/archive', null, { params: { months, confirm: false } }),
  archiveConfirm: (months = 12) => apiClient.post('/admin/audit-logs/archive', null, { params: { months, confirm: true }, responseType: 'blob' }),
};

// ——— Reports —————————————————————————
export const reportApi = {
  sales: (params) => apiClient.get('/admin/reports/sales', { params }),
  gstSummary: (params) => apiClient.get('/admin/reports/gst-summary', { params }),
  couponPerformance: (params) => apiClient.get('/admin/reports/coupon-performance', { params }),
  exportCsv: (type, params) => apiClient.get(`/admin/reports/${type}/export`, {
    params, responseType: 'blob',
  }),
};

// ——— Images ——————————————————————————        
export const imageApi = {
  getUploadUrl: (productId, data) =>
    apiClient.post(`/admin/images/upload/${productId}`, data),
  list: (productId) => apiClient.get(`/admin/images/${productId}`),
  reorder: (productId, data) =>
    apiClient.post(`/admin/images/${productId}/reorder`, data),
  setPrimary: (productId, imageId) =>
    apiClient.post(`/admin/images/set-primary/${imageId}`),
  delete: (productId, imageId) =>
    apiClient.delete(`/admin/images/${imageId}`),
};

// ——— Size Guides —————————————————————
export const sizeGuideApi = {
  list: (categoryId) => apiClient.get(`/admin/size-guides/${categoryId}`),
  upsert: (categoryId, data) => apiClient.post(`/admin/size-guides/${categoryId}`, data),
};

// ——— Store Settings (Phase 13H) ——————
export const settingsApi = {
  getUpi: () => apiClient.get('/admin/settings/upi'),
  updateUpi: (data) => apiClient.put('/admin/settings/upi', data),     
  getUpiAudit: (limit = 5) => apiClient.get('/admin/settings/upi/audit', { params: { limit } }),
};
