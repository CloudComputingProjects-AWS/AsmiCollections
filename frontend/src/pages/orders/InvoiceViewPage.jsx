/**
 * InvoiceViewPage — Phase F5 (Screen #17)
 * View/download GST invoice PDF from order detail
 */
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Download, FileText, Loader2 } from 'lucide-react';
import api from '../../api/apiClient';

export default function InvoiceViewPage() {
  const { orderId } = useParams();
  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get(`/orders/${orderId}/invoice/preview`);
        setInvoice(res.data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Invoice not found for this order');
      }
      setLoading(false);
    })();
  }, [orderId]);

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const res = await api.get(`/orders/${orderId}/invoice`);
      const { download_url, filename } = res.data;
      const a = document.createElement('a');
      a.href = download_url;
      a.download = filename;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch {
      alert('Failed to download invoice');
    }
    setDownloading(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 size={24} className="animate-spin text-gray-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-10">
        <Link to={`/orders/${orderId}`} className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-black mb-6 transition">
          <ArrowLeft size={16} /> Back to Order
        </Link>
        <div className="text-center py-16 border-2 border-dashed rounded-xl">
          <FileText size={40} className="mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500">{error}</p>
          <p className="text-sm text-gray-400 mt-1">Invoice may not have been generated yet for this order.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <Link to={`/orders/${orderId}`} className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-black mb-6 transition">
        <ArrowLeft size={16} /> Back to Order
      </Link>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tax Invoice</h1>
          <p className="text-sm text-gray-500">{invoice?.invoice_number}</p>
        </div>
        <button
          onClick={handleDownload}
          disabled={downloading}
          className="flex items-center gap-2 bg-black text-white px-5 py-2.5 rounded-lg font-medium text-sm hover:bg-gray-800 transition disabled:opacity-50"
        >
          <Download size={16} /> {downloading ? 'Downloading...' : 'Download PDF'}
        </button>
      </div>

      {/* Invoice Preview Card */}
      <div className="border rounded-xl p-6 bg-white">
        {/* Header */}
        <div className="text-center border-b pb-4 mb-4">
          <h2 className="text-lg font-bold uppercase tracking-wider">Tax Invoice</h2>
        </div>

        {/* Invoice Details */}
        <div className="grid grid-cols-2 gap-6 mb-6 text-sm">
          <div>
            <p className="text-gray-500 mb-1">Invoice Number</p>
            <p className="font-semibold">{invoice?.invoice_number}</p>
          </div>
          <div className="text-right">
            <p className="text-gray-500 mb-1">Date</p>
            <p className="font-semibold">{new Date(invoice?.generated_at).toLocaleDateString('en-IN')}</p>
          </div>
        </div>

        {/* Seller / Buyer */}
        <div className="grid grid-cols-2 gap-6 mb-6 text-sm border rounded-lg p-4 bg-gray-50">
          <div>
            <p className="font-semibold text-gray-900 mb-1">Sold By</p>
            <p className="text-gray-600">{invoice?.seller_name}</p>
            {invoice?.seller_gstin && <p className="text-gray-500 text-xs">GSTIN: {invoice.seller_gstin}</p>}
            <p className="text-gray-500 text-xs">{invoice?.seller_address}</p>
          </div>
          <div>
            <p className="font-semibold text-gray-900 mb-1">Bill To</p>
            <p className="text-gray-600">{invoice?.buyer_name}</p>
            {invoice?.buyer_gstin && <p className="text-gray-500 text-xs">GSTIN: {invoice.buyer_gstin}</p>}
            <p className="text-gray-500 text-xs">{invoice?.buyer_address}</p>
          </div>
        </div>

        {/* Supply Type */}
        {invoice?.supply_type && (
          <div className="text-sm mb-4">
            <span className="text-gray-500">Supply Type: </span>
            <span className="font-medium capitalize">{invoice.supply_type.replace('_', ' ')}</span>
            {invoice?.place_of_supply && <span className="text-gray-500"> | Place of Supply: {invoice.place_of_supply}</span>}
          </div>
        )}

        {/* Line Items */}
        <table className="w-full text-sm mb-6">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-2 font-medium">#</th>
              <th className="py-2 font-medium">Item</th>
              <th className="py-2 font-medium">HSN</th>
              <th className="py-2 font-medium text-right">Qty</th>
              <th className="py-2 font-medium text-right">Rate</th>
              <th className="py-2 font-medium text-right">Tax</th>
              <th className="py-2 font-medium text-right">Total</th>
            </tr>
          </thead>
          <tbody>
            {(invoice?.line_items || []).map((item, i) => (
              <tr key={i} className="border-b">
                <td className="py-2 text-gray-500">{i + 1}</td>
                <td className="py-2">{item.description}</td>
                <td className="py-2 text-gray-500">{item.hsn_code || '—'}</td>
                <td className="py-2 text-right">{item.quantity}</td>
                <td className="py-2 text-right">₹{item.unit_price?.toLocaleString('en-IN')}</td>
                <td className="py-2 text-right text-gray-500">
                  {item.cgst_amount > 0 && <div>CGST: ₹{item.cgst_amount}</div>}
                  {item.sgst_amount > 0 && <div>SGST: ₹{item.sgst_amount}</div>}
                  {item.igst_amount > 0 && <div>IGST: ₹{item.igst_amount}</div>}
                </td>
                <td className="py-2 text-right font-medium">₹{item.total_amount?.toLocaleString('en-IN')}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Totals */}
        <div className="border-t pt-4 space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-500">Subtotal</span>
            <span>₹{invoice?.subtotal?.toLocaleString('en-IN')}</span>
          </div>
          {invoice?.cgst_amount > 0 && (
            <div className="flex justify-between">
              <span className="text-gray-500">CGST</span>
              <span>₹{invoice.cgst_amount?.toLocaleString('en-IN')}</span>
            </div>
          )}
          {invoice?.sgst_amount > 0 && (
            <div className="flex justify-between">
              <span className="text-gray-500">SGST</span>
              <span>₹{invoice.sgst_amount?.toLocaleString('en-IN')}</span>
            </div>
          )}
          {invoice?.igst_amount > 0 && (
            <div className="flex justify-between">
              <span className="text-gray-500">IGST</span>
              <span>₹{invoice.igst_amount?.toLocaleString('en-IN')}</span>
            </div>
          )}
          {invoice?.shipping_fee > 0 && (
            <div className="flex justify-between">
              <span className="text-gray-500">Shipping</span>
              <span>₹{invoice.shipping_fee?.toLocaleString('en-IN')}</span>
            </div>
          )}
          {invoice?.discount_amount > 0 && (
            <div className="flex justify-between text-green-600">
              <span>Discount</span>
              <span>-₹{invoice.discount_amount?.toLocaleString('en-IN')}</span>
            </div>
          )}
          <div className="flex justify-between font-bold text-base pt-2 border-t">
            <span>Grand Total</span>
            <span>₹{invoice?.grand_total?.toLocaleString('en-IN')}</span>
          </div>
        </div>

        {/* Footer */}
        <p className="text-xs text-gray-400 text-center mt-6">This is a computer-generated invoice. No signature required.</p>
      </div>
    </div>
  );
}
