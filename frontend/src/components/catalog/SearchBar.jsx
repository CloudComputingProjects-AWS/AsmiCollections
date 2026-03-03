import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, X, Loader2 } from 'lucide-react';
import { useSearchAutocomplete } from '../../hooks/useCatalog';
import useCatalogStore from '../../stores/catalogStore';

export default function SearchBar({ className = '', compact = false }) {
  const [query, setQuery] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const { suggestions, loading, search } = useSearchAutocomplete();
  const { setFilters } = useCatalogStore();
  const navigate = useNavigate();
  const wrapperRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    search(query);
  }, [query, search]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      setFilters({ search: query.trim() });
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
      setShowDropdown(false);
    }
  };

  const handleSuggestionClick = (item) => {
    if (item.slug) {
      navigate(`/products/${item.slug}`);
    } else {
      setFilters({ search: item.title });
      navigate(`/search?q=${encodeURIComponent(item.title)}`);
    }
    setQuery('');
    setShowDropdown(false);
  };

  return (
    <div ref={wrapperRef} className={`relative ${className}`}>
      <form onSubmit={handleSubmit} className="relative">
        <Search
          size={18}
          className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-400"
        />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setShowDropdown(true);
          }}
          onFocus={() => query.length >= 2 && setShowDropdown(true)}
          placeholder={compact ? 'Search...' : 'Search for products, brands, categories...'}
          className={`w-full pl-10 pr-10 bg-neutral-50 border border-neutral-200 rounded-xl text-sm text-neutral-800 placeholder-neutral-400 focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none transition-all ${
            compact ? 'py-2' : 'py-2.5'
          }`}
        />
        {query && (
          <button
            type="button"
            onClick={() => {
              setQuery('');
              setShowDropdown(false);
              inputRef.current?.focus();
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600"
          >
            <X size={16} />
          </button>
        )}
      </form>

      {/* Autocomplete Dropdown */}
      {showDropdown && query.length >= 2 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-xl shadow-xl border border-neutral-100 overflow-hidden z-50 max-h-80 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-6">
              <Loader2 size={20} className="animate-spin text-indigo-500" />
            </div>
          ) : suggestions.length > 0 ? (
            <ul>
              {suggestions.map((item, i) => (
                <li key={item.id || i}>
                  <button
                    onClick={() => handleSuggestionClick(item)}
                    className="flex items-center gap-3 w-full px-4 py-2.5 hover:bg-neutral-50 transition-colors text-left"
                  >
                    {item.image_url ? (
                      <img
                        src={item.image_url}
                        alt=""
                        className="w-10 h-10 rounded-lg object-cover bg-neutral-100"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-lg bg-neutral-100 flex items-center justify-center">
                        <Search size={14} className="text-neutral-300" />
                      </div>
                    )}
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-neutral-800 truncate">
                        {item.title}
                      </p>
                      {item.brand && (
                        <p className="text-xs text-neutral-400">{item.brand}</p>
                      )}
                    </div>
                    {item.sale_price && (
                      <span className="ml-auto text-sm font-semibold text-neutral-700 whitespace-nowrap">
                        ₹{Number(item.sale_price || item.base_price).toLocaleString('en-IN')}
                      </span>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <div className="py-6 text-center text-sm text-neutral-400">
              No products found for "{query}"
            </div>
          )}
        </div>
      )}
    </div>
  );
}
