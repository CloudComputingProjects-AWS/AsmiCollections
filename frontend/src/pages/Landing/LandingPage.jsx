import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Sparkles, Truck, ShieldCheck, RotateCcw } from 'lucide-react';
import { useLandingData } from '../../hooks/useCatalog';
import ProductCard from '../../components/catalog/ProductCard';
import SearchBar from '../../components/catalog/SearchBar';
import apiClient from '../../api/apiClient';


export default function LandingPage() {
  const { featuredProducts, categoryCards, loading } = useLandingData();
  const [shippingConfig, setShippingConfig] = useState({ shipping_fee: 0, free_shipping_threshold: 0 });

  // Fetch shipping config from API (dynamic, not hardcoded)
  useEffect(() => {
    apiClient.get('/catalog/shipping-config')
      .then((res) => setShippingConfig(res.data))
      .catch(() => {});
  }, []);

  // Build features array dynamically based on shipping config
  const shippingDesc = shippingConfig.free_shipping_threshold > 0
    ? `On orders above \u20B9${Number(shippingConfig.free_shipping_threshold).toLocaleString('en-IN')}`
    : 'On all orders';

  const FEATURES = [
    { icon: Truck, title: 'Free Shipping', desc: shippingDesc },
    { icon: ShieldCheck, title: 'Secure Payments', desc: 'UPI \u2014 Secure & Instant' },
    { icon: RotateCcw, title: 'Easy Returns', desc: '7-day return policy' },
    { icon: Sparkles, title: 'Premium Quality', desc: 'Curated collection' },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-neutral-900 via-neutral-800 to-neutral-900 overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-20 w-72 h-72 bg-indigo-500 rounded-full blur-3xl" />
          <div className="absolute bottom-10 right-20 w-96 h-96 bg-rose-500 rounded-full blur-3xl" />
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-28 lg:py-36">
          <div className="max-w-2xl">
            <p className="text-indigo-300 font-semibold text-sm uppercase tracking-widest mb-4">
              New Season Collection
            </p>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white leading-tight mb-6">
              Style That Speaks{' '}
              <span className="bg-gradient-to-r from-indigo-400 to-rose-400 bg-clip-text text-transparent">
                Your Language
              </span>
            </h1>
            <p className="text-lg text-neutral-300 mb-8 leading-relaxed">
              Discover curated apparel for every occasion {'\u2014'} from everyday essentials to
              statement pieces. For men, women, and kids.
            </p>
            <SearchBar className="max-w-lg mb-6" />
            <div className="flex flex-wrap gap-3">
              <Link
                to="/shop"
                className="inline-flex items-center gap-2 px-6 py-3 bg-white text-neutral-900 font-bold rounded-xl hover:bg-neutral-100 transition-colors"
              >
                Shop Now <ArrowRight size={18} />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Category Cards from API */}
      {categoryCards.length > 0 && (
        <section className="bg-neutral-50 py-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">      
            <h2 className="text-2xl font-black text-neutral-900 mb-8">Explore Collections</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {categoryCards.map((cat) => (
                <Link
                  key={cat.id}
                  to={`/shop?category_id=${cat.id}`}
                  className="group bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-lg transition-all"
                >
                  {cat.image_url ? (
                    <div className="aspect-[4/3] overflow-hidden">      
                      <img
                        src={cat.image_url}
                        alt={cat.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      />
                    </div>
                  ) : (
                    <div className="aspect-[4/3] bg-gradient-to-br from-neutral-100 to-neutral-200 flex items-center justify-center">
                      <Sparkles size={32} className="text-neutral-300" />
                    </div>
                  )}
                  <div className="p-4">
                    <h3 className="font-bold text-neutral-800 group-hover:text-indigo-600 transition-colors">
                      {cat.name}
                    </h3>
                    {cat.product_count > 0 && (
                      <p className="text-xs text-neutral-400 mt-1">     
                        {cat.product_count} products
                      </p>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Featured Products */}
      {featuredProducts.length > 0 && (
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="flex items-center justify-between mb-8">      
            <h2 className="text-2xl font-black text-neutral-900">Featured Products</h2>
            <Link
              to="/shop?featured=true"
              className="text-sm font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
            >
              View all <ArrowRight size={16} />
            </Link>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
            {featuredProducts.slice(0, 8).map((product) => (
              <ProductCard key={product.id} product={product} />        
            ))}
          </div>
        </section>
      )}

      {/* Features Strip */}
      <section className="bg-white border-b border-neutral-100">        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">   
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">       
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="flex items-center gap-3">     
                <div className="p-2.5 bg-indigo-50 rounded-xl">
                  <Icon size={20} className="text-indigo-600" />        
                </div>
                <div>
                  <p className="text-sm font-bold text-neutral-800">{title}</p>
                  <p className="text-xs text-neutral-500">{desc}</p>    
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

            {/* Loading skeleton */}
      {loading && !featuredProducts.length && (
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="aspect-[3/4] bg-neutral-200 rounded-2xl mb-3" />
                <div className="h-3 bg-neutral-200 rounded w-1/3 mb-2" />
                <div className="h-4 bg-neutral-200 rounded w-3/4 mb-2" />
                <div className="h-4 bg-neutral-200 rounded w-1/4" />    
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
