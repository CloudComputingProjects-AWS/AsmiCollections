import { useState, useMemo } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ShoppingBag, Star, Truck, ShieldCheck, RotateCcw,
  ChevronLeft, ChevronRight, ZoomIn, Minus, Plus, Ruler,
} from 'lucide-react';
import { useProductDetail } from '../../hooks/useCatalog';
import useAuthStore from '../../stores/authStore';
import Breadcrumb from '../../components/common/Breadcrumb';
import useCartStore from '../../stores/cartStore';
import DOMPurify from 'dompurify';
import toast from 'react-hot-toast';

export default function ProductDetailPage() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { addToCart } = useCartStore();
  const { product, loading } = useProductDetail(slug);

  const [selectedImageIdx, setSelectedImageIdx] = useState(0);
  const [selectedSize, setSelectedSize] = useState('');
  const [selectedColor, setSelectedColor] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [showSizeGuide, setShowSizeGuide] = useState(false);
  const [addingToCart, setAddingToCart] = useState(false);
  const [showZoom, setShowZoom] = useState(false);

  // Derive available sizes/colors from variants
  const sizes = useMemo(() => {
    if (!product?.variants) return [];
    return [...new Set(product.variants.filter((v) => v.is_active).map((v) => v.size).filter(Boolean))];
  }, [product]);

  const colors = useMemo(() => {
    if (!product?.variants) return [];
    const colorMap = new Map();
    product.variants
      .filter((v) => v.is_active)
      .forEach((v) => {
        if (v.color && !colorMap.has(v.color)) {
          colorMap.set(v.color, { name: v.color, hex: v.color_hex || '#999' });
        }
      });
    return Array.from(colorMap.values());
  }, [product]);

  // Find matching variant
  const selectedVariant = useMemo(() => {
    if (!product?.variants) return null;
    return product.variants.find(
      (v) =>
        v.is_active &&
        (!selectedSize || v.size === selectedSize) &&
        (!selectedColor || v.color === selectedColor)
    );
  }, [product, selectedSize, selectedColor]);

  const images = product?.images || [];
  const currentImage = images[selectedImageIdx];
  const displayPrice = product?.sale_price || product?.base_price;
  const hasDiscount = product?.sale_price && product?.sale_price < product?.base_price;

  const handleAddToCart = async () => {
    if (!user) {
      navigate('/login');
      return;
    }
    if (!selectedVariant) return;
    setAddingToCart(true);
    try {
      const ok = await addToCart(selectedVariant.id, quantity, true);
      if (ok) toast.success('Added to cart!');
      else toast.error('Failed to add to cart');
    } finally {
      setAddingToCart(false);
    }
  };


  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid lg:grid-cols-2 gap-10 animate-pulse">
          <div className="aspect-square bg-neutral-200 rounded-2xl" />
          <div className="space-y-4">
            <div className="h-4 bg-neutral-200 rounded w-1/4" />
            <div className="h-8 bg-neutral-200 rounded w-3/4" />
            <div className="h-6 bg-neutral-200 rounded w-1/3" />
            <div className="h-20 bg-neutral-200 rounded w-full" />
          </div>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <p className="text-6xl mb-4">😕</p>
        <h2 className="text-xl font-bold text-neutral-800 mb-2">Product Not Found</h2>
        <Link to="/shop" className="text-indigo-600 font-medium hover:underline">
          Back to Shop
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Breadcrumb
        items={[
          { label: 'Shop', href: '/shop' },
          ...(product.category
            ? [{ label: product.category.name, href: `/shop?category_id=${product.category.id}` }]
            : []),
          { label: product.title },
        ]}
      />

      <div className="grid lg:grid-cols-2 gap-10">
        {/* Image Gallery */}
        <div>
          {/* Main Image */}
          <div
            className="relative aspect-square bg-neutral-100 rounded-2xl overflow-hidden cursor-zoom-in mb-4"
            onClick={() => setShowZoom(true)}
          >
            {currentImage ? (
              <img
                src={currentImage.medium_url || currentImage.processed_url || currentImage.original_url}
                alt={product.title}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-neutral-300">
                <ShoppingBag size={64} />
              </div>
            )}
            <button className="absolute bottom-4 right-4 p-2 bg-white/90 backdrop-blur rounded-lg shadow-sm">
              <ZoomIn size={18} className="text-neutral-600" />
            </button>

            {/* Image Nav */}
            {images.length > 1 && (
              <>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedImageIdx((i) => (i > 0 ? i - 1 : images.length - 1));
                  }}
                  className="absolute left-3 top-1/2 -translate-y-1/2 p-2 bg-white/90 backdrop-blur rounded-full shadow-sm hover:bg-white"
                >
                  <ChevronLeft size={18} />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedImageIdx((i) => (i < images.length - 1 ? i + 1 : 0));
                  }}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-white/90 backdrop-blur rounded-full shadow-sm hover:bg-white"
                >
                  <ChevronRight size={18} />
                </button>
              </>
            )}
          </div>

          {/* Thumbnails */}
          {images.length > 1 && (
            <div className="flex gap-2 overflow-x-auto pb-2">
              {images.map((img, i) => (
                <button
                  key={img.id || i}
                  onClick={() => setSelectedImageIdx(i)}
                  className={`w-16 h-16 flex-shrink-0 rounded-xl overflow-hidden border-2 transition-colors ${
                    i === selectedImageIdx ? 'border-indigo-500' : 'border-transparent hover:border-neutral-300'
                  }`}
                >
                  <img
                    src={img.thumbnail_url || img.original_url}
                    alt=""
                    className="w-full h-full object-cover"
                  />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Product Info */}
        <div>
          {product.brand && (
            <p className="text-sm font-semibold text-indigo-600 uppercase tracking-wider mb-1">
              {product.brand}
            </p>
          )}
          <h1 className="text-2xl sm:text-3xl font-black text-neutral-900 mb-3">
            {product.title}
          </h1>

          {/* Rating */}
          {product.avg_rating > 0 && (
            <div className="flex items-center gap-2 mb-4">
              <div className="flex items-center gap-1 bg-green-50 px-2 py-1 rounded-lg">
                <Star size={14} className="fill-green-600 text-green-600" />
                <span className="text-sm font-bold text-green-700">{product.avg_rating?.toFixed(1)}</span>
              </div>
              <span className="text-sm text-neutral-500">
                {product.review_count} review{product.review_count !== 1 ? 's' : ''}
              </span>
            </div>
          )}

          {/* Price */}
          <div className="flex items-baseline gap-3 mb-6">
            <span className="text-3xl font-black text-neutral-900">
              ₹{Number(displayPrice).toLocaleString('en-IN')}
            </span>
            {hasDiscount && (
              <>
                <span className="text-lg text-neutral-400 line-through">
                  ₹{Number(product.base_price).toLocaleString('en-IN')}
                </span>
                <span className="text-sm font-bold text-green-600 bg-green-50 px-2 py-0.5 rounded">
                  {Math.round(((product.base_price - product.sale_price) / product.base_price) * 100)}% OFF
                </span>
              </>
            )}
          </div>
          <p className="text-xs text-neutral-400 -mt-4 mb-6">Inclusive of all taxes</p>

          {/* Color Selector */}
          {colors.length > 0 && (
            <div className="mb-6">
              <p className="text-sm font-semibold text-neutral-700 mb-2">
                Color: <span className="font-normal text-neutral-500">{selectedColor || 'Select'}</span>
              </p>
              <div className="flex gap-2.5">
                {colors.map((c) => (
                  <button
                    key={c.name}
                    onClick={() => setSelectedColor(selectedColor === c.name ? '' : c.name)}
                    title={c.name}
                    className={`w-9 h-9 rounded-full border-2 transition-all ${
                      selectedColor === c.name
                        ? 'border-indigo-500 ring-2 ring-indigo-200 scale-110'
                        : 'border-neutral-200 hover:border-neutral-400'
                    }`}
                    style={{ backgroundColor: c.hex }}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Size Selector */}
          {sizes.length > 0 && (
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-semibold text-neutral-700">
                  Size: <span className="font-normal text-neutral-500">{selectedSize || 'Select'}</span>
                </p>
                <button
                  onClick={() => setShowSizeGuide(true)}
                  className="text-xs font-medium text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
                >
                  <Ruler size={12} /> Size Guide
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {sizes.map((s) => {
                  const variant = product.variants.find(
                    (v) =>
                      v.size === s &&
                      v.is_active &&
                      (!selectedColor || v.color === selectedColor)
                  );
                  const inStock = variant && variant.stock_quantity > 0;
                  return (
                    <button
                      key={s}
                      onClick={() => inStock && setSelectedSize(selectedSize === s ? '' : s)}
                      disabled={!inStock}
                      className={`min-w-[48px] px-4 py-2.5 text-sm font-medium rounded-xl border transition-all ${
                        selectedSize === s
                          ? 'bg-neutral-900 text-white border-neutral-900'
                          : inStock
                          ? 'border-neutral-200 text-neutral-700 hover:border-neutral-400'
                          : 'border-neutral-100 text-neutral-300 cursor-not-allowed line-through'
                      }`}
                    >
                      {s}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Quantity */}
          <div className="mb-6">
            <p className="text-sm font-semibold text-neutral-700 mb-2">Quantity</p>
            <div className="inline-flex items-center border border-neutral-200 rounded-xl overflow-hidden">
              <button
                onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                className="p-2.5 hover:bg-neutral-50 transition-colors"
              >
                <Minus size={16} />
              </button>
              <span className="px-5 py-2 text-sm font-bold text-neutral-800 min-w-[48px] text-center">
                {quantity}
              </span>
              <button
                onClick={() => setQuantity((q) => Math.min(10, q + 1))}
                className="p-2.5 hover:bg-neutral-50 transition-colors"
              >
                <Plus size={16} />
              </button>
            </div>
            {selectedVariant && selectedVariant.stock_quantity <= 5 && selectedVariant.stock_quantity > 0 && (
              <p className="text-xs text-rose-500 font-medium mt-1.5">
                Only {selectedVariant.stock_quantity} left in stock!
              </p>
            )}
          </div>

          {/* Add to Cart */}
          <div className="flex gap-3 mb-8">
            <button
              onClick={handleAddToCart}
              disabled={addingToCart || (sizes.length > 0 && !selectedVariant)}
              className="flex-1 flex items-center justify-center gap-2 py-3.5 bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700 disabled:bg-neutral-300 disabled:cursor-not-allowed transition-colors"
            >
              <ShoppingBag size={18} />
              {addingToCart ? 'Adding...' : 'Add to Cart'}
            </button>
          </div>

          {/* Delivery Features */}
          <div className="grid grid-cols-3 gap-3 mb-8">
            {[
              { icon: Truck, label: 'Free Delivery' },
              { icon: RotateCcw, label: '7 Day Returns' },
              { icon: ShieldCheck, label: 'Secure Payment' },
            ].map(({ icon: Icon, label }) => (
              <div key={label} className="text-center p-3 bg-neutral-50 rounded-xl">
                <Icon size={18} className="mx-auto text-neutral-500 mb-1" />
                <p className="text-xs font-medium text-neutral-600">{label}</p>
              </div>
            ))}
          </div>

          {/* Product Description */}
          {product.description && (
            <div className="mb-8">
              <h3 className="text-base font-bold text-neutral-800 mb-3">Description</h3>
              <div
                className="text-sm text-neutral-600 leading-relaxed prose prose-sm max-w-none"
                dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(product.description) }}
              />
            </div>
          )}

          {/* Apparel Attributes */}
          {product.attributes && Object.keys(product.attributes).length > 0 && (
            <div className="mb-8">
              <h3 className="text-base font-bold text-neutral-800 mb-3">Product Details</h3>
              <div className="grid grid-cols-2 gap-x-6 gap-y-2.5">
                {Object.entries(product.attributes).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-sm py-1.5 border-b border-neutral-50">
                    <span className="text-neutral-500 capitalize">{key.replace(/_/g, ' ')}</span>
                    <span className="text-neutral-800 font-medium">{String(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* HSN / GST Info */}
          {product.hsn_code && (
            <p className="text-xs text-neutral-400">
              HSN: {product.hsn_code} · GST: {product.gst_rate}%
            </p>
          )}
        </div>
      </div>

      {/* Size Guide Modal */}
      {showSizeGuide && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/50" onClick={() => setShowSizeGuide(false)} />
          <div className="relative bg-white rounded-2xl max-w-lg w-full max-h-[80vh] overflow-y-auto p-6">
            <h3 className="text-lg font-bold text-neutral-800 mb-4">Size Guide</h3>
            <p className="text-sm text-neutral-500 mb-4">Measurements in centimeters</p>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-200">
                  <th className="text-left py-2 font-semibold">Size</th>
                  <th className="text-center py-2 font-semibold">Chest</th>
                  <th className="text-center py-2 font-semibold">Waist</th>
                  <th className="text-center py-2 font-semibold">Hip</th>
                </tr>
              </thead>
              <tbody>
                {['S', 'M', 'L', 'XL', 'XXL'].map((s) => (
                  <tr key={s} className="border-b border-neutral-50">
                    <td className="py-2 font-medium">{s}</td>
                    <td className="py-2 text-center text-neutral-600">
                      {{ S: '91', M: '96', L: '101', XL: '107', XXL: '112' }[s]}
                    </td>
                    <td className="py-2 text-center text-neutral-600">
                      {{ S: '76', M: '81', L: '86', XL: '91', XXL: '97' }[s]}
                    </td>
                    <td className="py-2 text-center text-neutral-600">
                      {{ S: '91', M: '96', L: '101', XL: '107', XXL: '112' }[s]}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <button
              onClick={() => setShowSizeGuide(false)}
              className="mt-4 w-full py-2.5 bg-neutral-900 text-white font-semibold rounded-xl hover:bg-neutral-700 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Zoom Modal */}
      {showZoom && currentImage && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4 cursor-zoom-out"
          onClick={() => setShowZoom(false)}
        >
          <img
            src={currentImage.processed_url || currentImage.original_url}
            alt={product.title}
            className="max-w-full max-h-full object-contain"
          />
        </div>
      )}
    </div>
  );
}
