/**
 * Loading Skeletons + Error Boundary — Phase F5
 */
import { Component } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

/* ─── Skeleton Components ─── */
export function Skeleton({ className = '', variant = 'rect' }) {
  const base = 'animate-pulse bg-gray-200 rounded';
  if (variant === 'circle') return <div className={`${base} rounded-full ${className}`} />;
  if (variant === 'text') return <div className={`${base} h-4 ${className}`} />;
  return <div className={`${base} ${className}`} />;
}

export function ProductCardSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
      <Skeleton className="w-full aspect-[3/4]" />
      <div className="p-4 space-y-2">
        <Skeleton variant="text" className="w-3/4" />
        <Skeleton variant="text" className="w-1/2" />
        <div className="flex justify-between items-center pt-2">
          <Skeleton variant="text" className="w-20 h-5" />
          <Skeleton className="w-8 h-8 rounded-full" />
        </div>
      </div>
    </div>
  );
}

export function ProductGridSkeleton({ count = 8 }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => <ProductCardSkeleton key={i} />)}
    </div>
  );
}

export function TableSkeleton({ rows = 5, cols = 5 }) {
  return (
    <div className="bg-white rounded-xl border overflow-hidden">
      <div className="border-b bg-gray-50 px-4 py-3 flex gap-4">
        {Array.from({ length: cols }).map((_, i) => <Skeleton key={i} variant="text" className="flex-1 h-4" />)}
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="px-4 py-3 flex gap-4 border-b border-gray-50">
          {Array.from({ length: cols }).map((_, c) => <Skeleton key={c} variant="text" className="flex-1 h-4" />)}
        </div>
      ))}
    </div>
  );
}

export function DetailSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton variant="text" className="w-48 h-8" />
      <div className="bg-white rounded-xl border p-6 space-y-4">
        <Skeleton variant="text" className="w-full" />
        <Skeleton variant="text" className="w-3/4" />
        <Skeleton variant="text" className="w-1/2" />
        <Skeleton className="w-full h-48 mt-4" />
      </div>
    </div>
  );
}

/* ─── Error Boundary ─── */
export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
          <div className="p-4 bg-red-50 rounded-full mb-4">
            <AlertTriangle className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Something went wrong</h2>
          <p className="text-sm text-gray-500 mb-6 max-w-md">
            {this.state.error?.message || 'An unexpected error occurred. Please try again.'}
          </p>
          <button onClick={() => { this.setState({ hasError: false, error: null }); window.location.reload(); }}
            className="flex items-center gap-2 px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 text-sm font-medium transition-colors">
            <RefreshCw className="w-4 h-4" /> Reload Page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
