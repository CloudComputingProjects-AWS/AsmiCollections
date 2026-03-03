import { useCallback, useEffect, useRef } from 'react';
import useCatalogStore from '../stores/catalogStore';
import apiClient from '../api/apiClient';

// ── Landing Page Data ──
export function useLandingData() {
  const { featuredProducts, categoryCards, landingLoading, setLandingData, setLandingLoading } =
    useCatalogStore();

  const fetchLanding = useCallback(async () => {
    setLandingLoading(true);
    try {
      const res = await apiClient.get('/catalog/landing');
      setLandingData(res.data);
    } catch {
      setLandingData({ featured_products: [], category_cards: [] });
    }
  }, [setLandingData, setLandingLoading]);

  useEffect(() => {
    fetchLanding();
  }, [fetchLanding]);

  return { featuredProducts, categoryCards, loading: landingLoading, refetch: fetchLanding };
}

// ── Categories ──
export function useCategories(gender, ageGroup) {
  const { categories, categoriesLoading, setCategories, setCategoriesLoading } = useCatalogStore();

  useEffect(() => {
    const fetchCategories = async () => {
      setCategoriesLoading(true);
      try {
        const params = {};
        if (gender) params.gender = gender;
        if (ageGroup) params.age_group = ageGroup;
        const res = await apiClient.get('/catalog/categories', { params });
        setCategories(res.data);
      } catch {
        setCategories([]);
      }
    };
    fetchCategories();
  }, [gender, ageGroup, setCategories, setCategoriesLoading]);

  return { categories, loading: categoriesLoading };
}

// ── Product Listing: pure data reader ──
export function useProducts() {
  const products = useCatalogStore((s) => s.products);
  const totalProducts = useCatalogStore((s) => s.totalProducts);
  const totalPages = useCatalogStore((s) => s.totalPages);
  const currentPage = useCatalogStore((s) => s.currentPage);
  const loading = useCatalogStore((s) => s.loading);
  const error = useCatalogStore((s) => s.error);
  const setPage = useCatalogStore((s) => s.setPage);

  return { products, totalProducts, totalPages, currentPage, loading, error, setPage };
}

// Standalone fetch — reads ALL params from store at call time
export async function fetchCatalogProducts() {
  const { filters, sort, limit, currentPage, setProducts, setLoading, setError } =
    useCatalogStore.getState();

  setLoading(true);
  try {
    const params = {
      page: currentPage,
      page_size: limit,
      sort,
    };
    if (filters.gender) params.gender = filters.gender;
    if (filters.age_group) params.age_group = filters.age_group;
    if (filters.category_id) params.category_id = filters.category_id;
    if (filters.size) params.size = filters.size;
    if (filters.color) params.color = filters.color;
    if (filters.brand) params.brand = filters.brand;
    if (filters.price_min) params.price_min = filters.price_min;
    if (filters.price_max) params.price_max = filters.price_max;
    if (filters.rating_min) params.rating_min = filters.rating_min;
    if (filters.search) params.search = filters.search;

    if (filters.attributes) {
      Object.entries(filters.attributes).forEach(([key, value]) => {
        if (value) params[`attr.${key}`] = value;
      });
    }

    const res = await apiClient.get('/catalog/products', { params });
    setProducts(res.data);
  } catch (err) {
    setError(err.response?.data?.detail || 'Failed to load products');
  }
}

// ── Product Detail ──
export function useProductDetail(slug) {
  const { selectedProduct, productLoading, setSelectedProduct, setProductLoading } =
    useCatalogStore();

  useEffect(() => {
    if (!slug) return;
    const fetchProduct = async () => {
      setProductLoading(true);
      try {
        const res = await apiClient.get(`/catalog/products/slug/${slug}`);
        setSelectedProduct(res.data.product || res.data);
      } catch {
        setSelectedProduct(null);
      }
    };
    fetchProduct();
  }, [slug, setSelectedProduct, setProductLoading]);

  return { product: selectedProduct, loading: productLoading };
}

// ── Search Autocomplete ──
export function useSearchAutocomplete() {
  const { searchSuggestions, searchLoading, setSearchSuggestions, setSearchLoading } =
    useCatalogStore();
  const debounceRef = useRef(null);

  const search = useCallback(
    (query) => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      if (!query || query.length < 2) {
        setSearchSuggestions([]);
        return;
      }
      setSearchLoading(true);
      debounceRef.current = setTimeout(async () => {
        try {
          const res = await apiClient.get('/catalog/search/autocomplete', {
            params: { q: query },
          });
          setSearchSuggestions(res.data || []);
        } catch {
          setSearchSuggestions([]);
        }
      }, 300);
    },
    [setSearchSuggestions, setSearchLoading]
  );

  return { suggestions: searchSuggestions, loading: searchLoading, search };
}

// ── Filter Options ──
// Re-fetches when gender changes so Boys/Girls show age-group sizes
// (4-6, 7-9, etc.) while Men/Women show standard sizes (S, M, L, XL).
export function useFilterOptions() {
  const { filterOptions, setFilterOptions } = useCatalogStore();
  const gender = useCatalogStore((s) => s.filters.gender);

  useEffect(() => {
    const fetchFilterOptions = async () => {
      try {
        const params = {};
        if (gender) params.gender = gender;
        const res = await apiClient.get('/catalog/filters', { params });
        setFilterOptions({
          sizes: res.data.sizes || [],
          colors: res.data.colors || [],
          brands: res.data.brands || [],
          attributes: res.data.attributes || [],
        });
      } catch {
        // silent fail
      }
    };
    fetchFilterOptions();
  }, [gender, setFilterOptions]);

  return filterOptions;
}
