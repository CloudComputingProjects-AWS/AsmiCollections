import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ShoppingBag, Star } from 'lucide-react';

export default function ProductCard({ product, className = '' }) {
  const [imgError, setImgError] = useState(false);

  const imageUrl =
    product.primary_image?.thumbnail_url ||
    product.primary_image?.medium_url ||
    product.primary_image?.original_url ||
    null;

  const displayPrice = product.sale_price || product.base_price;
  const hasDiscount = product.sale_price && product.sale_price < product.base_price;
  const discountPct = hasDiscount
    ? Math.round(((product.base_price - product.sale_price) / product.base_price) * 100)
    : 0;


  return (
    <Link
      to={`/products/${product.slug}`}
      className={`group block bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 ${className}`}
    >
      {/* Image */}
      <div className="relative aspect-[3/4] bg-neutral-100 overflow-hidden">
        {imageUrl && !imgError ? (
          <img
            src={imageUrl}
            alt={product.title}
            loading="lazy"
            onError={() => setImgError(true)}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-neutral-300">
            <ShoppingBag size={48} />
          </div>
        )}

        {/* Discount Badge */}
        {hasDiscount && (
          <span className="absolute top-3 left-3 bg-rose-600 text-white text-xs font-bold px-2.5 py-1 rounded-full">
            -{discountPct}%
          </span>
        )}

        {/* Featured Badge */}
        {product.is_featured && (
          <span className="absolute top-3 right-12 bg-amber-400 text-amber-900 text-xs font-bold px-2.5 py-1 rounded-full">
            Featured
          </span>
        )}
      </div>

      {/* Info */}
      <div className="p-4">
        {/* Brand */}
        {product.brand && (
          <p className="text-xs font-medium text-neutral-500 uppercase tracking-wider mb-1">
            {product.brand}
          </p>
        )}

        {/* Title */}
        <h2 className="text-sm font-medium text-neutral-800 line-clamp-2 leading-snug mb-2 group-hover:text-indigo-600 transition-colors">
          {product.title}
        </h2>

        {/* Rating */}
        {product.avg_rating > 0 && (
          <div className="flex items-center gap-1 mb-2">
            <Star size={12} className="fill-amber-400 text-amber-400" />
            <span className="text-xs text-neutral-600">
              {product.avg_rating?.toFixed(1)}
            </span>
            {product.review_count > 0 && (
              <span className="text-xs text-neutral-500">({product.review_count})</span>
            )}
          </div>
        )}

        {/* Price */}
        <div className="flex items-baseline gap-2">
          <span className="text-base font-bold text-neutral-900">
            ₹{Number(displayPrice).toLocaleString('en-IN')}
          </span>
          {hasDiscount && (
            <span className="text-sm text-neutral-500 line-through">
              ₹{Number(product.base_price).toLocaleString('en-IN')}
            </span>
          )}
        </div>

        {/* Color swatches (if variants have colors) */}
        {product.available_colors && product.available_colors.length > 0 && (
          <div className="flex gap-1.5 mt-2.5">
            {product.available_colors.slice(0, 5).map((c, i) => (
              <span
                key={i}
                className="w-4 h-4 rounded-full border border-neutral-200 shadow-inner"
                style={{ backgroundColor: c.hex || c }}
                title={c.name || c}
              />
            ))}
            {product.available_colors.length > 5 && (
              <span className="text-xs text-neutral-500 self-center">
                +{product.available_colors.length - 5}
              </span>
            )}
          </div>
        )}
      </div>
    </Link>
  );
}
