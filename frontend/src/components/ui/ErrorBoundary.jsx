// ============================================
// Phase 13F — File 9/12: ErrorBoundary Component
// Catches render errors, shows friendly fallback, allows retry
// Usage: Wrap page routes or sections:
//   <ErrorBoundary><ProductDetailPage /></ErrorBoundary>
// ============================================
import { Component } from 'react';

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    console.error('[ErrorBoundary]', error, errorInfo);

    if (typeof this.props.onError === 'function') {
      this.props.onError(error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback via props
      if (this.props.fallback) {
        return typeof this.props.fallback === 'function'
          ? this.props.fallback({ error: this.state.error, retry: this.handleRetry })
          : this.props.fallback;
      }

      // Default fallback
      return (
        <div
          className="flex flex-col items-center justify-center min-h-[300px] p-8 text-center"
          role="alert"
        >
          <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3m0 3h.01M10.29 3.86L1.82 18a1 1 0 00.86 1.5h16.64a1 1 0 00.86-1.5L11.71 3.86a1 1 0 00-1.42 0z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-gray-800 mb-2">Something went wrong</h2>
          <p className="text-sm text-gray-600 mb-4 max-w-md">
            An unexpected error occurred. Please try again or refresh the page.
          </p>
          {import.meta.env.DEV && this.state.error && (
            <details className="mb-4 text-left max-w-lg w-full">
              <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                Error details (dev only)
              </summary>
              <pre className="mt-2 p-3 bg-gray-100 rounded text-xs text-red-700 overflow-auto max-h-40">
                {this.state.error.toString()}
                {this.state.errorInfo?.componentStack}
              </pre>
            </details>
          )}
          <div className="flex gap-3">
            <button
              onClick={this.handleRetry}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium
                hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                transition-colors"
            >
              Try Again
            </button>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium
                hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2
                transition-colors"
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
