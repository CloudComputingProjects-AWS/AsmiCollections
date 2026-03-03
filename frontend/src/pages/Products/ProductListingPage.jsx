import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Grid3X3, LayoutList, SlidersHorizontal, ChevronDown } from 'lucide-react';
import useCatalogStore from '../../stores/catalogStore';
import { useProducts, fetchCatalogProducts } from '../../hooks/useCatalog';
import ProductCard from '../../components/catalog/ProductCard';
import FilterSidebar from '../../components/catalog/FilterSidebar';
import Pagination from '../../components/catalog/Pagination';
import Breadcrumb from '../../components/common/Breadcrumb';

const SORT_OPTIONS = [
  { value: 'newest', label: 'Newest' },
  { value: 'price_asc', label: 'Price: Low to High' },
  { value: 'price_desc', label: 'Price: High to Low' },
  { value: 'rating', label: 'Highest Rated' },
  { value: 'popularity', label: 'Most Popular' },
];

export default function ProductListingPage() {
  const [searchParams] = useSearchParams();
  const [viewMode, setViewMode] = useState('grid');
  const [showMobileFilter, setShowMobileFilter] = useState(false);
  const [showSortDropdown, setShowSortDropdown] = useState(false);

  const filters = useCatalogStore((s) => s.filters);
  const sort = useCatalogStore((s) => s.sort);
  const setFilters = useCatalogStore((s) => s.setFilters);
  const setSort = useCatalogStore((s) => s.setSort);
  const clearFilters = useCatalogStore((s) => s.clearFilters);

  const { products, totalProducts, totalPages, currentPage, loading, setPage } = useProducts();

  // THE ONLY useEffect that fetches products — triggered by URL changes
  useEffect(() => {
    const urlFilters = {
      gender: '',
      age_group: '',
      category_id: '',
      size: '',
      color: '',
      brand: '',
      price_min: '',
      price_max: '',
      search: '',
      attributes: {},
    };
    const keys = ['gender', 'age_group', 'category_id', 'size', 'color', 'brand', 'price_min', 'price_max', 'search'];
    keys.forEach((key) => {
      const val = searchParams.get(key);
      if (val) urlFilters[key] = val;
    });

    const sortParam = searchParams.get('sort') || 'newest';

    // Zustand setState is synchronous — store is updated before next line
    setFilters(urlFilters);
    setSort(sortParam);
    // getState() now returns the committed values
    fetchCatalogProducts();
  }, [searchParams]);

  // Wrap filter/sort/page changes to also trigger fetch
  const handleFilterChange = useCallback((newFilters) => {
    useCatalogStore.getState().setFilters(newFilters);
    fetchCatalogProducts();
  }, []);

  const handleSortChange = useCallback((newSort) => {
    setSort(newSort);
    fetchCatalogProducts();
  }, [setSort]);

  const handlePageChange = useCallback((newPage) => {
    setPage(newPage);
    fetchCatalogProducts();
  }, [setPage]);

  const handleClearFilters = useCallback(() => {
    clearFilters();
    fetchCatalogProducts();
  }, [clearFilters]);

  const buildBreadcrumbs = () => {
    const crumbs = [];
    const capitalize = (s) => s ? s.charAt(0).toUpperCase() + s.slice(1).toLowerCase() : '';
    if (filters.gender) {
      crumbs.push({
        label: capitalize(filters.gender),
        href: `/shop?gender=${filters.gender}`,
      });
    }
    if (filters.age_group) {
      crumbs.push({
        label: capitalize(filters.age_group),
        href: filters.gender
          ? `/shop?gender=${filters.gender}&age_group=${filters.age_group}`
          : undefined,
      });
    }
    crumbs.push({ label: 'Products' });
    return crumbs;
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Breadcrumb items={buildBreadcrumbs()} />

      <div className="flex gap-8">
        <aside className="hidden lg:block w-64 flex-shrink-0">
          <FilterSidebar onFilterChange={handleFilterChange} onClearFilters={handleClearFilters} />
        </aside>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-6 gap-4">
            <div>
              <h1 className="text-xl font-bold text-neutral-900">
                {filters.search ? `Results for "${filters.search}"` : 'All Products'}
              </h1>
              <p className="text-sm text-neutral-500 mt-0.5">
                {totalProducts} product{totalProducts !== 1 ? 's' : ''} found
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowMobileFilter(true)}
                className="lg:hidden flex items-center gap-1.5 px-3 py-2 border border-neutral-200 rounded-xl text-sm font-medium text-neutral-700 hover:bg-neutral-50 transition-colors"
              >
                <SlidersHorizontal size={16} />
                Filters
              </button>

              <div className="relative">
                <button
                  onClick={() => setShowSortDropdown(!showSortDropdown)}
                  className="flex items-center gap-1.5 px-3 py-2 border border-neutral-200 rounded-xl text-sm font-medium text-neutral-700 hover:bg-neutral-50 transition-colors"
                >
                  {SORT_OPTIONS.find((s) => s.value === sort)?.label || 'Sort'}
                  <ChevronDown size={14} />
                </button>
                {showSortDropdown && (
                  <>
                    <div
                      className="fixed inset-0 z-10"
                      onClick={() => setShowSortDropdown(false)}
                    />
                    <div className="absolute right-0 top-full mt-1 w-48 bg-white rounded-xl shadow-xl border border-neutral-100 z-20 py-1">
                      {SORT_OPTIONS.map((opt) => (
                        <button
                          key={opt.value}
                          onClick={() => {
                            handleSortChange(opt.value);
                            setShowSortDropdown(false);
                          }}
                          className={`w-full text-left px-4 py-2 text-sm transition-colors ${
                            sort === opt.value
                              ? 'bg-indigo-50 text-indigo-700 font-medium'
                              : 'text-neutral-600 hover:bg-neutral-50'
                          }`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </div>

              <div className="hidden sm:flex items-center border border-neutral-200 rounded-xl overflow-hidden">
                <button
                  onClick={() => setViewMode('grid')}
                  aria-label="Grid view"
                  className={`p-2 transition-colors ${
                    viewMode === 'grid' ? 'bg-neutral-900 text-white' : 'text-neutral-400 hover:text-neutral-600'
                  }`}
                >
                  <Grid3X3 size={16} />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  aria-label="List view"
                  className={`p-2 transition-colors ${
                    viewMode === 'list' ? 'bg-neutral-900 text-white' : 'text-neutral-400 hover:text-neutral-600'
                  }`}
                >
                  <LayoutList size={16} />
                </button>
              </div>
            </div>
          </div>

          {loading ? (
            <div
              className={`grid gap-4 sm:gap-6 ${
                viewMode === 'grid' ? 'grid-cols-2 md:grid-cols-3' : 'grid-cols-1'
              }`}
            >
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="aspect-[3/4] bg-neutral-200 rounded-2xl mb-3" />
                  <div className="h-3 bg-neutral-200 rounded w-1/3 mb-2" />
                  <div className="h-4 bg-neutral-200 rounded w-3/4 mb-2" />
                  <div className="h-4 bg-neutral-200 rounded w-1/4" />
                </div>
              ))}
            </div>
          ) : products.length > 0 ? (
            <>
              <div
                className={`grid gap-4 sm:gap-6 ${
                  viewMode === 'grid' ? 'grid-cols-2 md:grid-cols-3' : 'grid-cols-1'
                }`}
              >
                {products.map((product) => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={handlePageChange}
              />
            </>
          ) : (
            <div className="text-center py-20">
              <p className="text-5xl mb-4">🔍</p>
              <h3 className="text-lg font-bold text-neutral-800 mb-2">No products found</h3>
              <p className="text-sm text-neutral-500">
                Try adjusting your filters or search terms.
              </p>
            </div>
          )}
        </div>
      </div>

      {showMobileFilter && (
        <div className="lg:hidden">
          <div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => setShowMobileFilter(false)}
          />
          <div className="fixed inset-y-0 left-0 w-80 max-w-full z-50 bg-white overflow-y-auto p-4">
            <FilterSidebar
              isMobile={true}
              onClose={() => setShowMobileFilter(false)}
              onFilterChange={handleFilterChange}
              onClearFilters={handleClearFilters}
            />
          </div>
        </div>
      )}
    </div>
  );
}
