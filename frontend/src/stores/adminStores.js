/**
 * Admin Stores — Phase F4
 * Zustand stores for admin dashboard state.
 */
import { create } from 'zustand';
import {
  dashboardApi, productApi, variantApi, categoryApi, attributeApi,     
  inventoryApi, orderApi, returnApi, couponApi, invoiceApi,
  userApi, auditApi, reportApi, imageApi, sizeGuideApi, refundApi,     
  settingsApi,
} from '../api/adminApi';

/** Trigger a browser file download from raw response data. */
function _downloadBlob(data, filename, mimeType) {
  const blob = mimeType ? new Blob([data], { type: mimeType }) : new Blob([data]);
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
}

// ——— Dashboard Store —————————————————
export const useDashboardStore = create((set) => ({
  stats: null,
  revenueChart: [],
  topProducts: [],
  alerts: [],
  loading: false,
  error: null,

  fetchStats: async () => {
    set({ loading: true });
    try {
      const { data } = await dashboardApi.getStats();
      set({ stats: data, loading: false });
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed to fetch stats', loading: false });
    }
  },

  fetchRevenueChart: async (params) => {
    try {
      const { data } = await dashboardApi.getRevenueChart(params);     
      set({ revenueChart: data.revenue_trend || [] });
    } catch (err) { /* silent */ }
  },

  fetchTopProducts: async (params) => {
    try {
      const { data } = await dashboardApi.getTopProducts(params);      
      set({ topProducts: data.products || [] });
    } catch (err) { /* silent */ }
  },

  fetchAlerts: async () => {
    try {
      const { data } = await dashboardApi.getAlerts();
      set({ alerts: data.variants || [] });
    } catch (err) { /* silent */ }
  },
}));

// ——— Product Store ———————————————————
export const useProductStore = create((set, get) => ({
  products: [],
  product: null,
  total: 0,
  page: 1,
  loading: false,
  error: null,

  fetchProducts: async (params = {}) => {
    set({ loading: true });
    try {
      const { data } = await productApi.list(params);
      set({ products: data.items || data, total: data.total || 0, loading: false });
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed', loading: false });
    }
  },

  fetchProduct: async (id) => {
    set({ loading: true });
    try {
      const { data } = await productApi.get(id);
      set({ product: data, loading: false });
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed', loading: false });
    }
  },

  createProduct: async (data) => {
    const res = await productApi.create(data);
    return res.data;
  },

  updateProduct: async (id, data) => {
    const res = await productApi.update(id, data);
    return res.data;
  },

  deleteProduct: async (id) => {
    await productApi.delete(id);
    set((s) => ({ products: s.products.filter((p) => p.id !== id) })); 
  },

  setPage: (page) => set({ page }),
}));

// ——— Category Store ——————————————————
export const useCategoryStore = create((set) => ({
  categories: [],
  loading: false,
  error: null,

  fetchCategories: async (params = {}) => {
    set({ loading: true });
    try {
      const { data } = await categoryApi.list(params);
      set({ categories: data.items || data, loading: false });
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed', loading: false });
    }
  },

  createCategory: async (data) => {
    const res = await categoryApi.create(data);
    return res.data;
  },

  updateCategory: async (id, data) => {
    const res = await categoryApi.update(id, data);
    return res.data;
  },

  deleteCategory: async (id) => {
    await categoryApi.delete(id);
    set((s) => ({ categories: s.categories.filter((c) => c.id !== id) }));
  },
}));

// ——— Order Store (Admin) —————————————
export const useAdminOrderStore = create((set) => ({
  orders: [],
  order: null,
  total: 0,
  loading: false,
  error: null,

  fetchOrders: async (params = {}) => {
    set({ loading: true });
    try {
      const { data } = await orderApi.list(params);
      set({ orders: data.items || data, total: data.total || 0, loading: false });
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed', loading: false });
    }
  },

  fetchOrder: async (id) => {
    set({ loading: true });
    try {
      const { data } = await orderApi.get(id);
      set({ order: data, loading: false });
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed', loading: false });
    }
  },

  transitionOrder: async (id, newStatus, reason) => {
    const res = await orderApi.transition(id, { new_status: newStatus, reason });
    return res.data;
  },

  fetchHistory: async (id) => {
    const { data } = await orderApi.history(id);
    return data;
  },
}));

// ——— Return Store ————————————————————
export const useReturnStore = create((set) => ({
  returns: [],
  total: 0,
  loading: false,

  fetchReturns: async (params = {}) => {
    set({ loading: true });
    try {
      const { data } = await returnApi.list(params);
      set({ returns: data.returns || data.items || data, total: data.total || 0, loading: false });
    } catch (err) {
      set({ loading: false });
    }
  },

  approveReturn: async (id, data) => {
    const res = await returnApi.approve(id, data);
    return res.data;
  },

  rejectReturn: async (id, data) => {
    const res = await returnApi.reject(id, data);
    return res.data;
  },

  receiveReturn: async (id) => {
    const res = await returnApi.receive(id);
    return res.data;
  },
}));

// ——— Coupon Store ————————————————————
export const useCouponStore = create((set) => ({
  coupons: [],
  loading: false,

  fetchCoupons: async (params = {}) => {
    set({ loading: true });
    try {
      const { data } = await couponApi.list(params);
      set({ coupons: data.items || data, loading: false });
    } catch (err) {
      set({ loading: false });
    }
  },

  createCoupon: async (data) => {
    const res = await couponApi.create(data);
    return res.data;
  },

  updateCoupon: async (id, data) => {
    const res = await couponApi.update(id, data);
    return res.data;
  },

  deleteCoupon: async (id) => {
    await couponApi.delete(id);
    set((s) => ({ coupons: s.coupons.filter((c) => c.id !== id) }));   
  },
}));

// ——— Invoice Store ———————————————————
export const useInvoiceStore = create((set) => ({
  invoices: [],
  creditNotes: [],
  total: 0,
  loading: false,

  fetchInvoices: async (params = {}) => {
    set({ loading: true });
    try {
      const { data } = await invoiceApi.list(params);
      set({ invoices: data.invoices || data.items || data, total: data.total || 0, loading: false });
    } catch (err) {
      set({ loading: false });
    }
  },

  fetchCreditNotes: async (params = {}) => {
    set({ loading: true });
    try {
      const { data } = await invoiceApi.creditNotes(params);
      set({ creditNotes: data.credit_notes || data.items || data, loading: false });
    } catch (err) {
      set({ loading: false });
    }
  },

  downloadInvoice: async (id) => {
    const res = await invoiceApi.download(id);
    _downloadBlob(res.data, `invoice-${id}.pdf`);
  },

  downloadCreditNote: async (id) => {
    const res = await invoiceApi.downloadCN(id);
    _downloadBlob(res.data, `credit-note-${id}.pdf`);
  },
}));

// ——— User Management Store ———————————
export const useUserManagementStore = create((set) => ({
  users: [],
  total: 0,
  loading: false,

  fetchUsers: async (params = {}) => {
    set({ loading: true });
    try {
      const { data } = await userApi.list(params);
      set({ users: data.users || data.items || data, total: data.total || 0, loading: false });
    } catch (err) {
      set({ loading: false });
    }
  },

  updateRole: async (id, role) => {
    const res = await userApi.updateRole(id, { role });
    return res.data;
  },

  toggleActive: async (id) => {
    const res = await userApi.toggleActive(id);
    return res.data;
  },
}));

// ——— Audit Log Store —————————————————
export const useAuditStore = create((set) => ({
  logs: [],
  total: 0,
  loading: false,

  fetchLogs: async (params = {}) => {
    set({ loading: true });
    try {
      const { data } = await auditApi.list(params);
      set({ logs: data.logs || data.items || data, total: data.total || 0, loading: false });
    } catch (err) {
      set({ loading: false });
    }
  },

  archiveCount: 0,
  archiving: false,

  previewArchive: async (months = 12) => {
    try {
      const { data } = await auditApi.archivePreview(months);
      set({ archiveCount: data.count || 0 });
      return data;
    } catch (err) {
      return { count: 0 };
    }
  },

  confirmArchive: async (months = 12) => {
    set({ archiving: true });
    try {
      const response = await auditApi.archiveConfirm(months);
      _downloadBlob(response.data, 'audit_logs_archive_' + new Date().toISOString().slice(0, 10) + '.csv', 'text/csv');
      set({ archiving: false, archiveCount: 0 });
      return true;
    } catch (err) {
      set({ archiving: false });
      return false;
    }
  },
}));

// ——— Report Store ————————————————————
export const useReportStore = create((set) => ({
  salesData: null,
  gstData: null,
  loading: false,

  fetchSalesReport: async (params) => {
    set({ loading: true });
    try {
      const { data } = await reportApi.sales(params);
      set({ salesData: data, loading: false });
    } catch (err) {
      set({ loading: false });
    }
  },

  fetchGstReport: async (params) => {
    set({ loading: true });
    try {
      const { data } = await reportApi.gstSummary(params);
      set({ gstData: data, loading: false });
    } catch (err) {
      set({ loading: false });
    }
  },

  exportReport: async (type, params) => {
    const res = await reportApi.exportCsv(type, params);
    _downloadBlob(res.data, `${type}-report.csv`);
  },
}));

// ——— Inventory Store —————————————————
export const useInventoryStore = create((set) => ({
  items: [],
  lowStock: [],
  total: 0,
  loading: false,

  fetchInventory: async (params = {}) => {
    set({ loading: true });
    try {
      const { data } = await inventoryApi.list(params);
      set({ items: data.variants || data.items || data, total: data.total || 0, loading: false });
    } catch (err) {
      set({ loading: false });
    }
  },

  fetchLowStock: async (params = {}) => {
    try {
      const { data } = await inventoryApi.lowStock(params);
      set({ lowStock: data.products || data.items || data });
    } catch (err) { /* silent */ }
  },

  updateStock: async (variantId, data) => {
    const res = await inventoryApi.update(variantId, data);
    return res.data;
  },

  bulkUpdate: async (data) => {
    const res = await inventoryApi.bulkUpdate(data);
    return res.data;
  },
}));

// ——— Attribute Store —————————————————
export const useAttributeStore = create((set) => ({
  attributes: [],
  loading: false,

  fetchAttributes: async () => {
    set({ loading: true });
    try {
      const { data } = await attributeApi.list();
      set({ attributes: data.items || data, loading: false });
    } catch (err) {
      set({ loading: false });
    }
  },

  createAttribute: async (data) => {
    const res = await attributeApi.create(data);
    return res.data;
  },

  updateAttribute: async (id, data) => {
    const res = await attributeApi.update(id, data);
    return res.data;
  },

  deleteAttribute: async (id) => {
    await attributeApi.delete(id);
    set((s) => ({ attributes: s.attributes.filter((a) => a.id !== id) }));
  },
}));

// ——— Store Settings Store (Phase 13H) ————
export const useSettingsStore = create((set) => ({
  upiConfig: null,
  upiAudit: [],
  loading: false,
  error: null,

  fetchUpiConfig: async () => {
    set({ loading: true, error: null });
    try {
      const { data } = await settingsApi.getUpi();
      set({ upiConfig: data, loading: false });
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed to fetch UPI config', loading: false });
    }
  },

  updateUpiConfig: async (merchantUpiVpa) => {
    const res = await settingsApi.updateUpi({ merchant_upi_vpa: merchantUpiVpa });
    set({ upiConfig: res.data });
    return res.data;
  },

  fetchUpiAudit: async (limit = 5) => {
    try {
      const { data } = await settingsApi.getUpiAudit(limit);
      set({ upiAudit: data });
    } catch (err) { /* silent */ }
  },
}));