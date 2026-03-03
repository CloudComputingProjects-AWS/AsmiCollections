import { useState, useEffect } from 'react';
import { X, ChevronDown, ChevronUp, SlidersHorizontal } from 'lucide-react';
import useCatalogStore from '../../stores/catalogStore';
import { useFilterOptions } from '../../hooks/useCatalog';

const DEFAULT_COLORS = [
  { name: 'Black', hex: '#000000' },
  { name: 'White', hex: '#FFFFFF' },
  { name: 'Red', hex: '#EF4444' },
  { name: 'Blue', hex: '#3B82F6' },
  { name: 'Green', hex: '#22C55E' },
  { name: 'Yellow', hex: '#EAB308' },
  { name: 'Pink', hex: '#EC4899' },
  { name: 'Navy', hex: '#1E3A5F' },
  { name: 'Grey', hex: '#9CA3AF' },
  { name: 'Brown', hex: '#92400E' },
  { name: 'Beige', hex: '#D4B896' },
  { name: 'Maroon', hex: '#7F1D1D' },
];

const COLOR_HEX_MAP = {};
DEFAULT_COLORS.forEach((c) => { COLOR_HEX_MAP[c.name.toLowerCase()] = c.hex; });

function FilterSection({ title, defaultOpen = true, children }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-b border-neutral-100 py-4">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full text-sm font-semibold text-neutral-700 hover:text-neutral-900"
      >
        {title}
        {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>
      {open && <div className="mt-3">{children}</div>}
    </div>
  );
}

export default function FilterSidebar({ onClose, isMobile = false, onFilterChange, onClearFilters }) {
  const filters = useCatalogStore((s) => s.filters);
  const setAttributeFilter = useCatalogStore((s) => s.setAttributeFilter);
  const removeAttributeFilter = useCatalogStore((s) => s.removeAttributeFilter);
  const filterOptions = useFilterOptions();
  const [priceMin, setPriceMin] = useState(filters.price_min || '');
  const [priceMax, setPriceMax] = useState(filters.price_max || '');

  useEffect(() => {
    setPriceMin(filters.price_min || '');
    setPriceMax(filters.price_max || '');
  }, [filters.price_min, filters.price_max]);

  // Use onFilterChange prop if provided (triggers fetch), otherwise fall back to store direct
  const applyFilter = (newFilters) => {
    if (onFilterChange) {
      onFilterChange(newFilters);
    } else {
      useCatalogStore.getState().setFilters(newFilters);
    }
  };

  const handleClear = () => {
    if (onClearFilters) {
      onClearFilters();
    } else {
      useCatalogStore.getState().clearFilters();
    }
  };

  const applyPriceRange = () => {
    applyFilter({ price_min: priceMin, price_max: priceMax });
  };

  const handleAttributeChange = (attrKey, opt) => {
    if (filters.attributes[attrKey] === opt) {
      removeAttributeFilter(attrKey);
    } else {
      setAttributeFilter(attrKey, opt);
    }
    // Attribute changes need a fetch too
    if (onFilterChange) {
      // Small delay to let Zustand commit attribute change
      setTimeout(() => {
        const { filters: f } = useCatalogStore.getState();
        onFilterChange({ ...f });
      }, 0);
    }
  };

  const availableSizes = filterOptions.sizes?.length > 0
    ? filterOptions.sizes
    : ['S', 'M', 'L', 'XL'];

  const availableColors = filterOptions.colors?.length > 0
    ? filterOptions.colors.map((c) => {
        if (typeof c === 'string') {
          return { name: c, hex: COLOR_HEX_MAP[c.toLowerCase()] || '#9CA3AF' };
        }
        // API returns { color: "Burgundy", color_hex: "#800020" }
        const colorName = c.color || c.name || 'Unknown';
        const colorHex = c.color_hex || c.hex || COLOR_HEX_MAP[colorName.toLowerCase()] || '#9CA3AF';
        return { name: colorName, hex: colorHex };
      })
    : DEFAULT_COLORS;

  const activeFilterCount = [
    filters.size,
    filters.color,
    filters.brand,
    filters.price_min,
    filters.price_max,
    filters.rating_min,
    ...Object.values(filters.attributes),
  ].filter(Boolean).length;

  return (
    <div
      className={`${
        isMobile ? 'fixed inset-0 z-50 bg-white overflow-y-auto' : 'sticky top-24'
      }`}
    >
      <div className="flex items-center justify-between px-1 pb-3 border-b border-neutral-200">
        <div className="flex items-center gap-2">
          <SlidersHorizontal size={18} className="text-neutral-600" />
          <h2 className="text-base font-bold text-neutral-800">Filters</h2>
          {activeFilterCount > 0 && (
            <span className="bg-indigo-100 text-indigo-700 text-xs font-bold px-2 py-0.5 rounded-full">
              {activeFilterCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {activeFilterCount > 0 && (
            <button
              onClick={handleClear}
              className="text-xs text-rose-500 hover:text-rose-600 font-medium"
            >
              Clear all
            </button>
          )}
          {isMobile && (
            <button onClick={onClose} className="p-1 hover:bg-neutral-100 rounded-lg">
              <X size={20} />
            </button>
          )}
        </div>
      </div>

      <FilterSection title="Size">
        <div className="flex flex-wrap gap-2">
          {availableSizes.map((s) => (
            <button
              key={s}
              onClick={() => applyFilter({ size: filters.size === s ? '' : s })}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
                filters.size === s
                  ? 'bg-neutral-900 text-white border-neutral-900'
                  : 'border-neutral-200 text-neutral-600 hover:border-neutral-400'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </FilterSection>

      <FilterSection title="Color">
        <div className="grid grid-cols-6 gap-2">
          {availableColors.map((c) => (
            <button
              key={c.name}
              onClick={() => applyFilter({ color: filters.color === c.name ? '' : c.name })}
              title={c.name}
              className={`w-8 h-8 rounded-full border-2 transition-all ${
                filters.color === c.name
                  ? 'border-indigo-500 ring-2 ring-indigo-200 scale-110'
                  : 'border-neutral-200 hover:border-neutral-400'
              }`}
              style={{ backgroundColor: c.hex }}
            >
              {c.hex === '#FFFFFF' && (
                <span className="block w-full h-full rounded-full border border-neutral-200" />
              )}
            </button>
          ))}
        </div>
      </FilterSection>

      <FilterSection title="Price Range">
        <div className="flex items-center gap-2">
          <input
            type="number"
            placeholder="Min"
            value={priceMin}
            onChange={(e) => setPriceMin(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none"
          />
          <span className="text-neutral-400">—</span>
          <input
            type="number"
            placeholder="Max"
            value={priceMax}
            onChange={(e) => setPriceMax(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-lg focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none"
          />
          <button
            onClick={applyPriceRange}
            className="px-3 py-2 bg-neutral-900 text-white text-xs font-medium rounded-lg hover:bg-neutral-700 transition-colors whitespace-nowrap"
          >
            Go
          </button>
        </div>
      </FilterSection>

      <FilterSection title="Rating" defaultOpen={false}>
        <div className="space-y-1.5">
          {[4, 3, 2, 1].map((r) => (
            <button
              key={r}
              onClick={() =>
                applyFilter({ rating_min: filters.rating_min === String(r) ? '' : String(r) })
              }
              className={`flex items-center gap-1.5 w-full px-2 py-1.5 rounded-lg text-sm transition-colors ${
                filters.rating_min === String(r)
                  ? 'bg-amber-50 text-amber-700'
                  : 'hover:bg-neutral-50 text-neutral-600'
              }`}
            >
              {'★'.repeat(r)}{'☆'.repeat(5 - r)}
              <span className="text-xs">&amp; up</span>
            </button>
          ))}
        </div>
      </FilterSection>

      {filterOptions.attributes
        .filter((attr) => attr.options?.length > 0)
        .map((attr) => (
          <FilterSection key={attr.key || attr.attribute_key} title={attr.display_name} defaultOpen={false}>
            <div className="space-y-1.5 max-h-40 overflow-y-auto">
              {attr.options.map((opt) => (
                <label
                  key={opt}
                  className="flex items-center gap-2 cursor-pointer px-1 py-1 rounded hover:bg-neutral-50"
                >
                  <input
                    type="checkbox"
                    checked={filters.attributes[attr.key || attr.attribute_key] === opt}
                    onChange={() => handleAttributeChange(attr.key || attr.attribute_key, opt)}
                    className="w-4 h-4 rounded border-neutral-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="text-sm text-neutral-600">{opt}</span>
                </label>
              ))}
            </div>
          </FilterSection>
        ))}

      {isMobile && (
        <div className="sticky bottom-0 bg-white border-t border-neutral-200 p-4">
          <button
            onClick={onClose}
            className="w-full py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors"
          >
            Apply Filters
          </button>
        </div>
      )}
    </div>
  );
}
