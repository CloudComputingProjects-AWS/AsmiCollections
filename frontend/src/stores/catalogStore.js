import { create } from 'zustand';

const useCatalogStore = create((set, get) => ({
  // Products
  products: [],
  totalProducts: 0,
  totalPages: 0,
  currentPage: 1,
  loading: false,
  error: null,

  // Filters
  filters: {
    gender: '',
    age_group: '',
    category_id: '',
    size: '',
    color: '',
    brand: '',
    price_min: '',
    price_max: '',
    rating_min: '',
    attributes: {},
    search: '',
  },
  sort: 'newest',
  limit: 24,

  // Categories
  categories: [],
  categoriesLoading: false,

  // Filter options (populated from API)
  filterOptions: {
    sizes: [],
    colors: [],
    brands: [],
    attributes: [],
  },

  // Featured / Landing
  featuredProducts: [],
  categoryCards: [],
  landingLoading: false,

  // Single product
  selectedProduct: null,
  productLoading: false,

  // Search
  searchSuggestions: [],
  searchLoading: false,

  setFilters: (newFilters) =>
    set((state) => ({
      filters: { ...state.filters, ...newFilters },
      currentPage: 1,
    })),

  setAttributeFilter: (key, value) =>
    set((state) => ({
      filters: {
        ...state.filters,
        attributes: { ...state.filters.attributes, [key]: value },
      },
      currentPage: 1,
    })),

  removeAttributeFilter: (key) =>
    set((state) => {
      const attrs = { ...state.filters.attributes };
      delete attrs[key];
      return { filters: { ...state.filters, attributes: attrs }, currentPage: 1 };
    }),

  setSort: (sort) => set({ sort, currentPage: 1 }),
  setPage: (page) => set({ currentPage: page }),

  clearFilters: () =>
    set({
      filters: {
        gender: '',
        age_group: '',
        category_id: '',
        size: '',
        color: '',
        brand: '',
        price_min: '',
        price_max: '',
        rating_min: '',
        attributes: {},
        search: '',
      },
      sort: 'newest',
      currentPage: 1,
    }),

  setProducts: (data) =>
    set({
      products: data.items || data.products || [],
      totalProducts: data.total || 0,
      totalPages: data.total_pages || 1,
      loading: false,
      error: null,
    }),

  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error, loading: false }),
  setCategories: (categories) => set({ categories, categoriesLoading: false }),
  setCategoriesLoading: (loading) => set({ categoriesLoading: loading }),
  setLandingData: (data) =>
    set({
      featuredProducts: data.featured_products || [],
      categoryCards: data.category_cards || [],
      landingLoading: false,
    }),
  setLandingLoading: (loading) => set({ landingLoading: loading }),
  setSelectedProduct: (product) => set({ selectedProduct: product, productLoading: false }),
  setProductLoading: (loading) => set({ productLoading: loading }),
  setSearchSuggestions: (suggestions) => set({ searchSuggestions: suggestions, searchLoading: false }),
  setSearchLoading: (loading) => set({ searchLoading: loading }),
  setFilterOptions: (options) => set({ filterOptions: options }),
}));

export default useCatalogStore;
