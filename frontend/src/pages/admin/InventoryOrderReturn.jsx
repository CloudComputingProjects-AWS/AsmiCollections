/**
 * Inventory Manager, Order Manager, Return Manager — Phase F4 (Screens #24, #25, #26)
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useInventoryStore, useAdminOrderStore, useReturnStore } from '../../stores/adminStores';
import { refundApi } from '../../api/adminApi';
import { DataTable, PageHeader, SearchFilterBar, Pagination, StatusBadge, Modal } from '../../components/admin/AdminUI';

export function InventoryManager() {
  const { items, lowStock, total, loading, fetchInventory, fetchLowStock, updateStock } = useInventoryStore();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showLowOnly, setShowLowOnly] = useState(false);

  useEffect(() => { fetchInventory({ page, limit: 25, search }); fetchLowStock(); }, [page, search]);

  const data = showLowOnly ? lowStock : items;

  const columns = [
    { header: 'Product', render: (r) => <div><div className="font-medium text-sm">{r.product_title}</div><div className="text-xs text-gray-500">{r.brand || '\u2014'}</div></div> },
    { header: 'SKU', render: (r) => <span className="font-mono text-xs">{r.sku}</span> },
    { header: 'Size', key: 'size' },
    { header: 'Color', render: (r) => (
      <div className="flex items-center gap-1.5">
        {r.color_hex && <span className="w-3 h-3 rounded-full border" style={{ backgroundColor: r.color_hex }} />}
        <span className="text-sm">{r.color || '\u2014'}</span>
      </div>
    )},
    { header: 'Stock', render: (r) => (
      <span className={`font-semibold ${r.stock_quantity < 10 ? 'text-red-600' : r.stock_quantity < 30 ? 'text-amber-600' : 'text-emerald-600'}`}>
        {r.stock_quantity}
      </span>
    )},
    { header: 'Update', render: (r) => (
      <div className="flex items-center gap-1">
        <input type="number" defaultValue={r.stock_quantity} aria-label={`Update stock for ${r.product_title} ${r.size || ''} ${r.color || ''}`.trim()} className="w-16 px-2 py-1 border border-gray-200 rounded text-sm"
          onBlur={(e) => { const val = parseInt(e.target.value); if (val !== r.stock_quantity) updateStock(r.id, { stock_quantity: val }); }} />
      </div>
    )},
  ];

  return (
    <div>
      <PageHeader title="Inventory" subtitle={`${total} variants | ${lowStock.length} low stock`} actions={
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={showLowOnly} onChange={(e) => setShowLowOnly(e.target.checked)} className="w-4 h-4 rounded text-red-600" />
          Low stock only
        </label>
      } />
      <SearchFilterBar searchPlaceholder="Search by product, SKU..." onSearch={setSearch} />
      <DataTable columns={columns} data={data} loading={loading} />
      {!showLowOnly && <Pagination page={page} total={total} limit={25} onPageChange={setPage} />}
    </div>
  );
}

/**
 * Order Manager — Phase F4 (Screen #25)
 */

const ORDER_TRANSITIONS = {
  placed: ['confirmed', 'cancelled'],
  confirmed: ['processing', 'delivered', 'cancelled'],
  processing: ['shipped', 'cancelled'],
  shipped: ['out_for_delivery'],
  out_for_delivery: ['delivered'],
  delivered: ['return_requested'],
  return_requested: ['return_approved', 'return_rejected'],
  return_approved: ['return_received'],
  return_received: ['refunded'],
};

export function OrderManager() {
  const navigate = useNavigate();
  const { orders, total, loading, fetchOrders, transitionOrder, fetchHistory } = useAdminOrderStore();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState({});
  const [transitionModal, setTransitionModal] = useState(null);
  const [historyModal, setHistoryModal] = useState(null);
  const [historyData, setHistoryData] = useState([]);
  const [reason, setReason] = useState('');

  useEffect(() => { fetchOrders({ page, limit: 20, search, ...filters }); }, [page, search, filters]);

  const handleTransition = async (orderId, newStatus) => {
    try {
      await transitionOrder(orderId, newStatus, reason);
      setTransitionModal(null);
      setReason('');
      fetchOrders({ page, limit: 20, search, ...filters });
    } catch (err) { alert(err.response?.data?.detail || 'Transition failed'); }
  };

  const showHistory = async (order) => {
    const data = await fetchHistory(order.id);
    setHistoryData(data);
    setHistoryModal(order);
  };

  const columns = [
    { header: 'Order #', render: (r) => <span className="font-mono text-sm font-medium">{r.order_number}</span> },
    { header: 'Customer', render: (r) => <div><div className="text-sm">{r.customer_name || r.shipping_name}</div><div className="text-xs text-gray-500">{r.customer_email}</div></div> },
    { header: 'Total', render: (r) => <span className="font-semibold">{'\u20B9'}{parseFloat(r.grand_total || 0).toLocaleString()}</span> },
    { header: 'Payment', render: (r) => <StatusBadge status={r.payment_status} /> },
    { header: 'Status', render: (r) => <StatusBadge status={r.order_status} /> },
    { header: 'Date', render: (r) => new Date(r.created_at).toLocaleDateString() },
    { header: 'Actions', render: (r) => (
      <div className="flex gap-1">
        {ORDER_TRANSITIONS[r.order_status]?.length > 0 && (
          <button onClick={(e) => { e.stopPropagation(); setTransitionModal(r); }} className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100">Update</button>
        )}

      </div>
    )},
  ];

  const statusOptions = ['placed', 'confirmed', 'processing', 'shipped', 'out_for_delivery', 'delivered', 'return_requested', 'cancelled', 'refunded'].map((s) => ({ value: s, label: s.replace(/_/g, ' ') }));

  return (
    <div>
      <PageHeader title="Orders" subtitle={`${total} orders`} />
      <SearchFilterBar searchPlaceholder="Search by order #, customer..." onSearch={setSearch}
        filters={[{ key: 'order_status', label: 'Status', options: statusOptions }, { key: 'payment_status', label: 'Payment', options: [{ value: 'paid', label: 'Paid' }, { value: 'pending', label: 'Pending' }, { value: 'failed', label: 'Failed' }] }]}
        values={filters} onFilter={(key, val) => setFilters((f) => ({ ...f, [key]: val || undefined }))} />
      <DataTable columns={columns} data={orders} loading={loading} />
      <Pagination page={page} total={total} limit={20} onPageChange={setPage} />

      {/* Transition Modal */}
      <Modal open={!!transitionModal} onClose={() => setTransitionModal(null)} title={`Update Order ${transitionModal?.order_number}`}>
        <div className="space-y-3">
          <p className="text-sm">Current: <StatusBadge status={transitionModal?.order_status} /></p>
          <p className="text-sm font-medium">Move to:</p>
          <div className="flex flex-wrap gap-2">
            {(ORDER_TRANSITIONS[transitionModal?.order_status] || []).map((status) => (
              <button key={status} onClick={() => handleTransition(transitionModal.id, status)}
                className={`px-3 py-1.5 text-sm rounded-lg border ${status === 'cancelled' ? 'border-red-200 text-red-700 hover:bg-red-50' : 'border-blue-200 text-blue-700 hover:bg-blue-50'}`}>
                {status.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
          <div><label htmlFor="order-transition-reason" className="block text-sm font-medium mb-1">Reason (optional)</label><input id="order-transition-reason" type="text" value={reason} onChange={(e) => setReason(e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" /></div>
        </div>
      </Modal>

      {/* History Modal */}
      <Modal open={!!historyModal} onClose={() => setHistoryModal(null)} title={`History \u2014 ${historyModal?.order_number}`}>
        <div className="space-y-2">
          {historyData.length === 0 ? <p className="text-sm text-gray-500">No history</p> : historyData.map((h, i) => (
            <div key={i} className="flex items-start gap-3 p-2 rounded-lg bg-gray-50">
              <div className="w-2 h-2 rounded-full bg-blue-500 mt-1.5 flex-shrink-0" />
              <div className="flex-1">
                <div className="text-sm"><StatusBadge status={h.from_status} /> {'\u2192'} <StatusBadge status={h.to_status} /></div>
                {h.change_reason && <p className="text-xs text-gray-500 mt-0.5">{h.change_reason}</p>}
                <p className="text-xs text-gray-500 mt-0.5">{new Date(h.created_at).toLocaleString()}</p>
              </div>
            </div>
          ))}
        </div>
      </Modal>
    </div>
  );
}

/**
 * Return/Refund Manager — Phase F4 (Screen #26)
 */

export function ReturnManager() {
  const { returns: returnsList, total, loading, fetchReturns, approveReturn, rejectReturn, receiveReturn } = useReturnStore();
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({});
  const [actionModal, setActionModal] = useState(null);
  const [notes, setNotes] = useState('');

  useEffect(() => { fetchReturns({ page, limit: 20, ...filters }); }, [page, filters]);

  const handleAction = async (action) => {
    try {
      if (action === 'approve') await approveReturn(actionModal.id, { admin_notes: notes });
      else if (action === 'reject') await rejectReturn(actionModal.id, { admin_notes: notes });
      else if (action === 'receive') await receiveReturn(actionModal.id);
      else if (action === 'refund') await refundApi.initiate({ order_id: actionModal.order_id, return_id: actionModal.id, reason: notes || 'Return refund' });
      setActionModal(null);
      setNotes('');
      fetchReturns({ page, limit: 20, ...filters });
    } catch (err) { alert(err.response?.data?.detail || 'Action failed'); }
  };

  const columns = [
    { header: 'Return ID', render: (r) => <span className="font-mono text-xs">{r.id?.slice(0, 8)}</span> },
    { header: 'Order', render: (r) => <span className="font-mono text-sm">{r.order_number || r.order_id?.slice(0, 8)}</span> },
    { header: 'Customer', key: 'customer_name' },
    { header: 'Reason', render: (r) => <span className="text-sm max-w-[150px] truncate block">{r.reason}</span> },
    { header: 'Type', render: (r) => <span className="capitalize text-sm">{r.return_type}</span> },
    { header: 'Qty', key: 'quantity' },
    { header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
    { header: 'Date', render: (r) => new Date(r.created_at).toLocaleDateString() },
    { header: 'Actions', render: (r) => (
      <button onClick={(e) => { e.stopPropagation(); setActionModal(r); }} className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100">
        Manage
      </button>
    )},
  ];

  return (
    <div>
      <PageHeader title="Returns & Refunds" subtitle={`${total} returns`} />
      <SearchFilterBar filters={[
        { key: 'status', label: 'Status', options: [{ value: 'requested', label: 'Requested' }, { value: 'approved', label: 'Approved' }, { value: 'rejected', label: 'Rejected' }, { value: 'received', label: 'Received' }] },
      ]} values={filters} onFilter={(key, val) => setFilters((f) => ({ ...f, [key]: val || undefined }))} />
      <DataTable columns={columns} data={returnsList} loading={loading} />
      <Pagination page={page} total={total} limit={20} onPageChange={setPage} />

      <Modal open={!!actionModal} onClose={() => setActionModal(null)} title={`Return \u2014 ${actionModal?.id?.slice(0, 8)}`}>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div><span className="text-gray-500">Status:</span> <StatusBadge status={actionModal?.status} /></div>
            <div><span className="text-gray-500">Type:</span> <span className="capitalize">{actionModal?.return_type}</span></div>
            <div><span className="text-gray-500">Reason:</span> {actionModal?.reason}</div>
            <div><span className="text-gray-500">Qty:</span> {actionModal?.quantity}</div>
          </div>
          {actionModal?.reason_detail && <p className="text-sm bg-gray-50 p-2 rounded">{actionModal.reason_detail}</p>}
          <div><label htmlFor="return-admin-notes" className="block text-sm font-medium mb-1">Admin Notes</label><textarea id="return-admin-notes" rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" /></div>
          <div className="flex flex-wrap gap-2">
            {actionModal?.status === 'requested' && (
              <>
                <button onClick={() => handleAction('approve')} className="px-3 py-1.5 text-sm bg-emerald-600 text-white rounded-lg hover:bg-emerald-700">Approve</button>
                <button onClick={() => handleAction('reject')} className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700">Reject</button>
              </>
            )}
            {actionModal?.status === 'approved' && (
              <button onClick={() => handleAction('receive')} className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">Mark Received</button>
            )}
            {actionModal?.status === 'received' && (
              <button onClick={() => handleAction('refund')} className="px-3 py-1.5 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700">Initiate Refund</button>
            )}
          </div>
        </div>
      </Modal>
    </div>
  );
}
