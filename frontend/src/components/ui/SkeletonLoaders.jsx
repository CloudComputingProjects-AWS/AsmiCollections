// ============================================
// Phase 13F — File 8/12: Skeleton Loaders
// Comprehensive skeleton components for all page types
// ============================================

function Pulse({ className = '' }) {
  return <div className={`animate-pulse bg-gray-200 rounded ${className}`} />;
}

// ---- Product Card Skeleton ----
export function ProductCardSkeleton() {
  return (
    <div className="bg-white rounded-lg border border-gray-100 overflow-hidden" aria-hidden="true">
      <Pulse className="h-56 w-full rounded-none" />
      <div className="p-4 space-y-3">
        <Pulse className="h-3 w-2/3" />
        <Pulse className="h-4 w-full" />
        <div className="flex gap-2">
          <Pulse className="h-5 w-16" />
          <Pulse className="h-5 w-12" />
        </div>
        <Pulse className="h-3 w-1/3" />
      </div>
    </div>
  );
}

// ---- Product Grid Skeleton ----
export function ProductGridSkeleton({ count = 8 }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4" role="status" aria-label="Loading products">
      {Array.from({ length: count }).map((_, i) => (
        <ProductCardSkeleton key={i} />
      ))}
      <span className="sr-only">Loading products...</span>
    </div>
  );
}

// ---- Table Row Skeleton ----
export function TableRowSkeleton({ cols = 6 }) {
  return (
    <tr aria-hidden="true">
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <Pulse className={`h-4 ${i === 0 ? 'w-8' : i === 1 ? 'w-40' : 'w-20'}`} />
        </td>
      ))}
    </tr>
  );
}

// ---- Table Skeleton ----
export function TableSkeleton({ rows = 5, cols = 6 }) {
  return (
    <div role="status" aria-label="Loading table data">
      <table className="w-full">
        <thead>
          <tr>
            {Array.from({ length: cols }).map((_, i) => (
              <th key={i} className="px-4 py-3 text-left">
                <Pulse className="h-3 w-20" />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, i) => (
            <TableRowSkeleton key={i} cols={cols} />
          ))}
        </tbody>
      </table>
      <span className="sr-only">Loading table data...</span>
    </div>
  );
}

// ---- Dashboard Stat Card Skeleton ----
export function StatCardSkeleton() {
  return (
    <div className="bg-white rounded-lg border p-5 space-y-3" aria-hidden="true">
      <div className="flex justify-between">
        <Pulse className="h-3 w-24" />
        <Pulse className="h-8 w-8 rounded-full" />
      </div>
      <Pulse className="h-7 w-20" />
      <Pulse className="h-3 w-32" />
    </div>
  );
}

// ---- Dashboard Skeleton ----
export function DashboardSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-label="Loading dashboard">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => <StatCardSkeleton key={i} />)}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border p-5">
          <Pulse className="h-4 w-32 mb-4" />
          <Pulse className="h-48 w-full" />
        </div>
        <div className="bg-white rounded-lg border p-5">
          <Pulse className="h-4 w-32 mb-4" />
          <Pulse className="h-48 w-full" />
        </div>
      </div>
      <span className="sr-only">Loading dashboard...</span>
    </div>
  );
}

// ---- Product Detail Skeleton ----
export function ProductDetailSkeleton() {
  return (
    <div className="max-w-6xl mx-auto p-4" role="status" aria-label="Loading product details">
      <Pulse className="h-3 w-64 mb-6" /> {/* Breadcrumb */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="space-y-3">
          <Pulse className="h-96 w-full rounded-lg" />
          <div className="flex gap-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Pulse key={i} className="h-16 w-16 rounded" />
            ))}
          </div>
        </div>
        <div className="space-y-4">
          <Pulse className="h-3 w-20" />
          <Pulse className="h-7 w-3/4" />
          <Pulse className="h-3 w-24" />
          <div className="flex gap-3 pt-2">
            <Pulse className="h-8 w-24" />
            <Pulse className="h-8 w-20" />
          </div>
          <Pulse className="h-4 w-48 mt-4" />
          <div className="flex gap-2 mt-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Pulse key={i} className="h-10 w-10 rounded-full" />
            ))}
          </div>
          <div className="flex gap-2 mt-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Pulse key={i} className="h-10 w-12 rounded" />
            ))}
          </div>
          <Pulse className="h-12 w-full rounded-lg mt-6" />
          <div className="space-y-2 mt-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <Pulse key={i} className="h-3 w-full" />
            ))}
          </div>
        </div>
      </div>
      <span className="sr-only">Loading product details...</span>
    </div>
  );
}

// ---- Form Skeleton ----
export function FormSkeleton({ fields = 6 }) {
  return (
    <div className="space-y-5 max-w-lg" role="status" aria-label="Loading form">
      {Array.from({ length: fields }).map((_, i) => (
        <div key={i} className="space-y-2">
          <Pulse className="h-3 w-24" />
          <Pulse className="h-10 w-full rounded-lg" />
        </div>
      ))}
      <Pulse className="h-11 w-36 rounded-lg mt-4" />
      <span className="sr-only">Loading form...</span>
    </div>
  );
}

// ---- Generic Page Skeleton ----
export function PageSkeleton() {
  return (
    <div className="space-y-6 p-4" role="status" aria-label="Loading page">
      <Pulse className="h-8 w-48" />
      <Pulse className="h-4 w-full max-w-2xl" />
      <Pulse className="h-4 w-3/4 max-w-xl" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
        <Pulse className="h-40 w-full rounded-lg" />
        <Pulse className="h-40 w-full rounded-lg" />
      </div>
      <span className="sr-only">Loading page...</span>
    </div>
  );
}
