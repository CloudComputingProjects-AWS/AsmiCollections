/**
 * Invoice Viewer, User Manager, Audit Log, Reports â€” Phase F4 (Screens #28-31)
 */
import { useEffect, useState } from 'react';
import {
  useInvoiceStore, useUserManagementStore, useAuditStore, useReportStore,
} from '../../stores/adminStores';
import { DataTable, PageHeader, SearchFilterBar, Pagination, StatusBadge, Modal } from '../../components/admin/AdminUI';

const ROLES = ['customer', 'product_manager', 'order_manager', 'finance_manager', 'admin'];

export function InvoiceViewer() {
  const { invoices, creditNotes, total, loading, fetchInvoices, fetchCreditNotes, downloadInvoice, downloadCreditNote } = useInvoiceStore();
  const [tab, setTab] = useState('invoices');
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (tab === 'invoices') fetchInvoices({ page, page_size: 20, search });
    else fetchCreditNotes({ page, page_size: 20, search });
  }, [tab, page, search]);

  const invColumns = [
    { header: 'Invoice #', render: (r) => <span className="font-mono text-sm font-medium">{r.invoice_number}</span> },
    { header: 'Order', render: (r) => <span className="font-mono text-xs">{r.order_number || r.order_id?.slice(0, 8)}</span> },
    { header: 'Buyer', key: 'buyer_name' },
    { header: 'Supply', render: (r) => <span className="text-xs capitalize">{(r.supply_type || '').replace(/_/g, ' ')}</span> },
    { header: 'Total', render: (r) => <span className="font-semibold">{'\u20B9'}{parseFloat(r.grand_total || 0).toLocaleString()}</span> },
    { header: 'Date', render: (r) => new Date(r.generated_at || r.created_at).toLocaleDateString() },
    { header: '', render: (r) => <button onClick={() => downloadInvoice(r.id)} className="text-blue-600 text-sm hover:underline">Download</button> },
  ];

  const cnColumns = [
    { header: 'CN #', render: (r) => <span className="font-mono text-sm font-medium">{r.credit_note_number}</span> },
    { header: 'Invoice', render: (r) => <span className="font-mono text-xs">{r.invoice_number || '\u2014'}</span> },
    { header: 'Reason', render: (r) => <span className="text-sm max-w-[200px] truncate block">{r.reason}</span> },
    { header: 'Amount', render: (r) => <span className="font-semibold">{'\u20B9'}{parseFloat(r.total_amount || 0).toLocaleString()}</span> },
    { header: 'Date', render: (r) => new Date(r.issued_at || r.created_at).toLocaleDateString() },
    { header: '', render: (r) => <button onClick={() => downloadCreditNote(r.id)} className="text-blue-600 text-sm hover:underline">Download</button> },
  ];

  return (
    <div>
      <PageHeader title="Invoices & Credit Notes" />
      <div className="flex gap-1 mb-4 bg-gray-50 rounded-lg p-1 w-fit">
        <button onClick={() => setTab('invoices')} className={`px-4 py-2 text-sm rounded-md ${tab === 'invoices' ? 'bg-white shadow-sm font-medium' : 'text-gray-500'}`}>Invoices</button>
        <button onClick={() => setTab('credit_notes')} className={`px-4 py-2 text-sm rounded-md ${tab === 'credit_notes' ? 'bg-white shadow-sm font-medium' : 'text-gray-500'}`}>Credit Notes</button>
      </div>
      <SearchFilterBar searchPlaceholder={`Search ${tab === 'invoices' ? 'invoice' : 'credit note'}...`} onSearch={setSearch} />
      <DataTable columns={tab === 'invoices' ? invColumns : cnColumns} data={tab === 'invoices' ? invoices : creditNotes} loading={loading} />
      <Pagination page={page} total={total} limit={20} onPageChange={setPage} />
    </div>
  );
}

/**
 * User Manager â€” Phase F4 (Screen #29)
 */

export function UserManager() {
  const { users, total, loading, fetchUsers, updateRole, toggleActive } = useUserManagementStore();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState({});
  const [roleModal, setRoleModal] = useState(null);
  const [newRole, setNewRole] = useState('');

  useEffect(() => { fetchUsers({ page, page_size: 20, search, ...filters }); }, [page, search, filters]);

  const handleRoleUpdate = async () => {
    try {
      await updateRole(roleModal.id, newRole);
      setRoleModal(null);
      fetchUsers({ page, page_size: 20, search, ...filters });
    } catch (err) { alert(err.response?.data?.detail || 'Failed'); }
  };

  const columns = [
    { header: 'User', render: (r) => <div><div className="text-sm font-medium">{r.first_name} {r.last_name}</div><div className="text-xs text-gray-500">{r.email}</div></div> },
    { header: 'Role', render: (r) => <span className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full font-medium capitalize">{(r.role || '').replace(/_/g, ' ')}</span> },
    { header: 'Verified', render: (r) => r.email_verified ? <span className="text-emerald-600">{'\u2714'}</span> : <span className="text-gray-300">{'\u2718'}</span> },
    { header: 'Status', render: (r) => <StatusBadge status={r.is_active ? 'active' : 'inactive'} /> },
    { header: 'Joined', render: (r) => new Date(r.created_at).toLocaleDateString() },
    { header: 'Actions', render: (r) => (
      <div className="flex gap-1">
        <button onClick={(e) => { e.stopPropagation(); setRoleModal(r); setNewRole(r.role); }} className="text-blue-600 text-xs hover:underline">Role</button>
        <button onClick={(e) => { e.stopPropagation(); toggleActive(r.id).then(() => fetchUsers({ page, page_size: 20, search, ...filters })); }} className={`text-xs ${r.is_active ? 'text-red-500' : 'text-emerald-600'} hover:underline`}>
          {r.is_active ? 'Disable' : 'Enable'}
        </button>
      </div>
    )},
  ];

  return (
    <div>
      <PageHeader title="Users" subtitle={`${total} users`} />
      <SearchFilterBar searchPlaceholder="Search by name, email..." onSearch={setSearch}
        filters={[{ key: 'role', label: 'Role', options: ROLES.map((r) => ({ value: r, label: r.replace(/_/g, ' ') })) }]}
        values={filters} onFilter={(key, val) => setFilters((f) => ({ ...f, [key]: val || undefined }))} />
      <DataTable columns={columns} data={users} loading={loading} />
      <Pagination page={page} total={total} limit={20} onPageChange={setPage} />
      <Modal open={!!roleModal} onClose={() => setRoleModal(null)} title={`Change Role \u2014 ${roleModal?.email}`} size="sm">
        <div className="space-y-3">
          <label htmlFor="user-role-select" className="block text-sm font-medium mb-1">New Role</label>
          <select id="user-role-select" value={newRole} onChange={(e) => setNewRole(e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">
            {ROLES.map((r) => <option key={r} value={r} className="capitalize">{r.replace(/_/g, ' ')}</option>)}
          </select>
          <button onClick={handleRoleUpdate} className="w-full py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">Update Role</button>
        </div>
      </Modal>
    </div>
  );
}

/**
 * Audit Log Viewer â€” Phase F4 (Screen #30)
 */

export function AuditLogViewer() {
  const { logs, total, loading, fetchLogs, archiveCount, archiving, previewArchive, confirmArchive } = useAuditStore();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState({});
  const [showArchive, setShowArchive] = useState(false);
  const [archiveMonths, setArchiveMonths] = useState(12);

  useEffect(() => { fetchLogs({ page, page_size: 25, search, ...filters }); }, [page, search, filters]);

  const handleArchivePreview = async () => {
    const result = await previewArchive(archiveMonths);
    setShowArchive(true);
  };

  const handleArchiveConfirm = async () => {
    const ok = await confirmArchive(archiveMonths);
    if (ok) {
      setShowArchive(false);
      setPage(1);
      setTimeout(() => fetchLogs({ page: 1, page_size: 25 }), 500);
    }
  };

  const columns = [
    { header: 'Admin', render: (r) => <span className="text-sm">{r.admin_email || r.admin_id?.slice(0, 8)}</span> },
    { header: 'Action', render: (r) => <span className="text-xs font-mono bg-gray-100 px-2 py-0.5 rounded">{r.action}</span> },
    { header: 'Target', render: (r) => <span className="text-sm">{r.target_type} {r.target_id ? `(${r.target_id.slice(0, 8)})` : ''}</span> },
    { header: 'Details', render: (r) => <span className="text-xs text-gray-500 max-w-[200px] truncate block">{r.details ? JSON.stringify(r.details).slice(0, 80) : '\u2014'}</span> },
    { header: 'IP', render: (r) => <span className="text-xs font-mono text-gray-500">{r.ip_address || '\u2014'}</span> },
    { header: 'Time', render: (r) => new Date(r.created_at).toLocaleString() },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <PageHeader title="Audit Logs" subtitle="Admin activity history" />
        <button onClick={handleArchivePreview} className="px-4 py-2 text-sm font-medium text-white bg-amber-700 rounded-lg hover:bg-amber-800 whitespace-nowrap">Archive Old Logs</button>
      </div>
      {showArchive && (
        <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-xl">
          <h4 className="text-sm font-semibold text-amber-800 mb-2">Archive Audit Logs</h4>
          <div className="flex items-center gap-3 mb-3">
            <label htmlFor="archive-months" className="text-sm text-gray-600">Logs older than</label>
            <select id="archive-months" value={archiveMonths} onChange={(e) => setArchiveMonths(Number(e.target.value))} className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm">
              <option value={6}>6 months</option>
              <option value={12}>12 months</option>
              <option value={18}>18 months</option>
              <option value={24}>24 months</option>
            </select>
            <button onClick={handleArchivePreview} className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">Check Count</button>
          </div>
          {archiveCount > 0 ? (
            <div className="flex items-center gap-3">
              <span className="text-sm text-amber-700 font-medium">{archiveCount} logs found for archival</span>
              <button onClick={handleArchiveConfirm} disabled={archiving} className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50">
                {archiving ? 'Exporting & Purging...' : 'Export CSV & Purge'}
              </button>

            </div>
          ) : (
            <span className="text-sm text-gray-500">No logs older than {archiveMonths} months found.</span>
          )}
        </div>
      )}
      <SearchFilterBar searchPlaceholder="Search by admin, action, target..." onSearch={setSearch}
        filters={[{ key: 'action', label: 'Action', options: ['create', 'update', 'delete', 'transition', 'login', 'refund'].map((a) => ({ value: a, label: a })) }]}
        values={filters} onFilter={(key, val) => setFilters((f) => ({ ...f, [key]: val || undefined }))} />
      <DataTable columns={columns} data={logs} loading={loading} />
      <Pagination page={page} total={total} limit={25} onPageChange={setPage} />
    </div>
  );
}

/**
 * Reports & Finance â€” Phase F4 (Screen #31)
 */

export function ReportsPage() {
  const { salesData, gstData, loading, fetchSalesReport, fetchGstReport, exportReport } = useReportStore();
  const [tab, setTab] = useState('sales');
  const [dateRange, setDateRange] = useState({ from: '', to: '' });

  const handleFetch = () => {
    if (tab === 'sales') fetchSalesReport({ from_date: dateRange.from, to_date: dateRange.to });
    else if (tab === 'gst') {
      const yr = dateRange.from ? new Date(dateRange.from).getFullYear() : new Date().getFullYear();
      const month = dateRange.from ? new Date(dateRange.from).getMonth() + 1 : new Date().getMonth() + 1;
      const fyStart = month >= 4 ? yr : yr - 1;
      const financialYear = `${fyStart}-${String(fyStart + 1).slice(2)}`;
      fetchGstReport({ financial_year: financialYear, from_date: dateRange.from, to_date: dateRange.to });
    }
};

  return (
    <div>
      <PageHeader title="Reports & Finance" />
      <div className="flex gap-1 mb-4 bg-gray-50 rounded-lg p-1 w-fit">
        {['sales', 'gst', 'coupon'].map((t) => (
          <button key={t} onClick={() => setTab(t)} className={`px-4 py-2 text-sm rounded-md capitalize ${tab === t ? 'bg-white shadow-sm font-medium' : 'text-gray-500'}`}>{t === 'gst' ? 'GST Summary' : t}</button>
        ))}
      </div>

      <div className="flex items-end gap-3 mb-4">
        <div><label htmlFor="report-from" className="block text-xs font-medium mb-1">From</label><input id="report-from" type="date" value={dateRange.from} onChange={(e) => setDateRange({ ...dateRange, from: e.target.value })} className="px-3 py-2 border border-gray-200 rounded-lg text-sm" /></div>
        <div><label htmlFor="report-to" className="block text-xs font-medium mb-1">To</label><input id="report-to" type="date" value={dateRange.to} onChange={(e) => setDateRange({ ...dateRange, to: e.target.value })} className="px-3 py-2 border border-gray-200 rounded-lg text-sm" /></div>
        <button onClick={handleFetch} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">Generate</button>
        <button onClick={() => exportReport(tab, { from_date: dateRange.from, to_date: dateRange.to })} className="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">Export CSV</button>
      </div>

      <div className="bg-white rounded-xl border border-gray-100 p-5">
        {loading ? (
          <div className="text-center py-10 text-gray-500">Loading...</div>
        ) : tab === 'sales' && salesData ? (
          <div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
              <div className="text-center"><div className="text-2xl font-bold">{'\u20B9'}{(salesData.summary?.total_revenue || 0).toLocaleString()}</div><div className="text-xs text-gray-500">Revenue</div></div>
              <div className="text-center"><div className="text-2xl font-bold">{salesData.summary?.total_orders || 0}</div><div className="text-xs text-gray-500">Orders</div></div>
              <div className="text-center"><div className="text-2xl font-bold">{'\u20B9'}{(salesData.summary?.avg_order_value || 0).toLocaleString()}</div><div className="text-xs text-gray-500">Avg Order</div></div>
              <div className="text-center"><div className="text-2xl font-bold">{'\u20B9'}{(salesData.summary?.total_refunds || 0).toLocaleString()}</div><div className="text-xs text-gray-500">Refunds</div></div>
            </div>
            {salesData.by_category && (
              <div>
                <h4 className="text-sm font-semibold mb-2">By Category</h4>
                <table className="w-full text-sm">
                  <thead><tr className="bg-gray-50"><th className="px-3 py-2 text-left">Category</th><th className="px-3 py-2 text-right">Orders</th><th className="px-3 py-2 text-right">Revenue</th></tr></thead>
                  <tbody>{(salesData.by_category || []).map((c, i) => (
                    <tr key={i} className="border-t"><td className="px-3 py-2">{c.category_name}</td><td className="px-3 py-2 text-right">{c.orders}</td><td className="px-3 py-2 text-right font-medium">{'\u20B9'}{c.revenue?.toLocaleString()}</td></tr>
                  ))}</tbody>
                </table>
              </div>
            )}
          </div>
        ) : tab === 'gst' && gstData ? (
          <div>
            <h4 className="text-sm font-semibold mb-3">Invoice-wise GST Summary</h4>
            <table className="w-full text-sm">
              <thead><tr className="bg-gray-50"><th className="px-3 py-2 text-left">Invoice #</th><th className="px-3 py-2 text-left">Date</th><th className="px-3 py-2 text-left">Supply</th><th className="px-3 py-2 text-right">Taxable</th><th className="px-3 py-2 text-right">CGST</th><th className="px-3 py-2 text-right">SGST</th><th className="px-3 py-2 text-right">IGST</th><th className="px-3 py-2 text-right">Total Tax</th></tr></thead>
              <tbody>{(gstData.invoices || []).map((inv, i) => (
                <tr key={i} className="border-t">
                  <td className="px-3 py-2 font-mono text-sm">{inv.invoice_number}</td><td className="px-3 py-2 text-sm">{inv.invoice_date ? new Date(inv.invoice_date).toLocaleDateString() : ''}</td><td className="px-3 py-2 text-sm capitalize">{inv.supply_type?.replace('_', ' ')}</td>
                  <td className="px-3 py-2 text-right">{'\u20B9'}{Number(inv.total_taxable_amount)?.toLocaleString()}</td>
                  <td className="px-3 py-2 text-right">{'\u20B9'}{Number(inv.cgst_amount)?.toLocaleString()}</td>
                  <td className="px-3 py-2 text-right">{'\u20B9'}{Number(inv.sgst_amount)?.toLocaleString()}</td>
                  <td className="px-3 py-2 text-right">{'\u20B9'}{Number(inv.igst_amount)?.toLocaleString()}</td>
                  <td className="px-3 py-2 text-right font-semibold">{'\u20B9'}{Number(inv.total_tax)?.toLocaleString()}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-10 text-gray-500">Select a date range and click Generate</div>
        )}
      </div>
    </div>
  );
}
