import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import useCatalogStore from '../../stores/catalogStore';
import ProductListingPage from '../Products/ProductListingPage';

export default function SearchResultsPage() {
  const [searchParams] = useSearchParams();
  const { setFilters } = useCatalogStore();

  useEffect(() => {
    const q = searchParams.get('q');
    if (q) {
      setFilters({ search: q });
    }
  }, [searchParams, setFilters]);

  // Reuse the product listing page — it reads search from store filters
  return <ProductListingPage />;
}
