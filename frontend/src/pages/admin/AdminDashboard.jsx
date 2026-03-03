/**
 * Admin Dashboard — Phase F4 (Screen #19)
 * Revenue, orders, charts.
 */
import { useEffect } from 'react';
import { useDashboardStore } from '../../stores/adminStores';
import { StatCard, PageHeader } from '../../components/admin/AdminUI';

export default function AdminDashboard() {
  const { stats, revenueChart, topProducts, loading, fetchStats, fetchRevenueChart, fetchTopProducts } = useDashboardStore();

  useEffect(() => {
    fetchStats();
    fetchRevenueChart({ period: '30d' });
    fetchTopProducts({ limit: 5 });
  }, []);

  const statCards = stats ? [
    { title: 'Total Revenue', value: `₹${(stats.total_revenue || 0).toLocaleString()}`, icon: '₹', color: 'green' },
    { title: 'Total Orders', value: stats.total_orders || 0, icon: '📦', color: 'blue' },
    { title: 'Avg Order Value', value: `₹${(stats.avg_order_value || 0).toLocaleString()}`, icon: '📊', color: 'purple' },
    { title: 'Total Customers', value: stats.total_customers || 0, icon: '👥', color: 'indigo' },
    { title: 'Pending Orders', value: stats.pending_orders || 0, icon: '⏳', color: 'amber' },
    { title: 'Failed Payments', value: stats.failed_payments || 0, icon: '⚠', color: 'red' },
  ] : [];

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Overview of your store performance" />

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-6">
        {loading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-gray-100 p-5 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-2/3 mb-3" />   
              <div className="h-7 bg-gray-200 rounded w-1/2" />        
            </div>
          ))
        ) : (
          statCards.map((card, i) => <StatCard key={i} {...card} />)   
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Chart */}
        <div className="bg-white rounded-xl border border-gray-100 p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Revenue Trend (30 Days)</h3>
          {revenueChart.length > 0 ? (
            <div className="h-64 flex items-end gap-1">
              {revenueChart.map((d, i) => {
                const max = Math.max(...revenueChart.map(r => r.revenue || 0), 1);
                const h = ((d.revenue || 0) / max) * 100;
                return (
                  <div key={i} className="flex-1 group relative">      
                    <div
                      className="bg-gradient-to-t from-blue-500 to-blue-400 rounded-t-sm hover:from-blue-600 hover:to-blue-500 transition-all"
                      style={{ height: `${Math.max(h, 2)}%` }}
                    />
                    <div className="hidden group-hover:block absolute bottom-full mb-1 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
                      ₹{(d.revenue || 0).toLocaleString()} — {d.date}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400 text-sm">
              No revenue data yet
            </div>
          )}
        </div>

        {/* Top Products */}
        <div className="bg-white rounded-xl border border-gray-100 p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Top Products</h3>
          <div className="space-y-3">
            {topProducts.length === 0 ? (
              <p className="text-sm text-gray-400">No data</p>
            ) : (
              topProducts.map((p, i) => (
                <div key={i} className="flex items-center gap-3">      
                  <span className="w-6 h-6 rounded-full bg-blue-50 text-blue-600 text-xs font-bold flex items-center justify-center">{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">{p.title}</p>
                    <p className="text-xs text-gray-400">{p.total_sold || 0} sold</p>
                  </div>
                  <span className="text-sm font-semibold text-gray-700">₹{(p.total_revenue || 0).toLocaleString()}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
