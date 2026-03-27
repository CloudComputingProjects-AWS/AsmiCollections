import { useSearchParams, Navigate } from 'react-router-dom';

export default function SearchResultsPage() {
  const [searchParams] = useSearchParams();
  const q = searchParams.get('q');

  if (q) {
    return <Navigate to={`/shop?search=${encodeURIComponent(q)}`} replace />;
  }

  return <Navigate to="/shop" replace />;
}
