// ============================================
// Phase 13F — File 7/12: Responsive & Image Optimization
// Hooks: useMediaQuery, useBreakpoint
// Components: ResponsiveImage (srcset + lazy loading)
// ============================================
import { useState, useEffect, useCallback } from 'react';

// ---- useMediaQuery ----
export function useMediaQuery(query) {
  const [matches, setMatches] = useState(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    const mql = window.matchMedia(query);
    const handler = (e) => setMatches(e.matches);
    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, [query]);

  return matches;
}

// ---- useBreakpoint ----
// Returns current Tailwind breakpoint name
export function useBreakpoint() {
  const sm = useMediaQuery('(min-width: 640px)');
  const md = useMediaQuery('(min-width: 768px)');
  const lg = useMediaQuery('(min-width: 1024px)');
  const xl = useMediaQuery('(min-width: 1280px)');

  if (xl) return 'xl';
  if (lg) return 'lg';
  if (md) return 'md';
  if (sm) return 'sm';
  return 'xs';
}

// ---- useIsMobile ----
export function useIsMobile() {
  return !useMediaQuery('(min-width: 768px)');
}

// ---- useMobileMenu ----
export function useMobileMenu() {
  const [isOpen, setIsOpen] = useState(false);
  const isMobile = useIsMobile();

  const toggle = useCallback(() => setIsOpen((p) => !p), []);
  const close = useCallback(() => setIsOpen(false), []);
  const open = useCallback(() => setIsOpen(true), []);

  // Close on resize to desktop
  useEffect(() => {
    if (!isMobile && isOpen) setIsOpen(false);
  }, [isMobile, isOpen]);

  // Prevent body scroll when menu open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  return { isOpen, toggle, close, open, isMobile };
}

// ============================================
// ResponsiveImage — srcset + lazy loading + WebP
// Usage:
//   <ResponsiveImage
//     src="https://cdn.store.com/img_800.webp"
//     thumbnail="https://cdn.store.com/img_300.webp"
//     full="https://cdn.store.com/img.webp"
//     alt="Product Name - Blue - M"
//     className="w-full h-64 object-cover"
//   />
// ============================================
export function ResponsiveImage({
  src,          // medium (800px) — default
  thumbnail,    // 300px
  full,         // 1200px
  alt,
  className = '',
  sizes = '(max-width: 640px) 300px, (max-width: 1024px) 800px, 1200px',
  ...props
}) {
  const srcSet = [
    thumbnail && `${thumbnail} 300w`,
    src && `${src} 800w`,
    full && `${full} 1200w`,
  ].filter(Boolean).join(', ');

  return (
    <img
      src={src}
      srcSet={srcSet || undefined}
      sizes={srcSet ? sizes : undefined}
      alt={alt || ''}
      loading="lazy"
      decoding="async"
      className={className}
      onError={(e) => {
        // Fallback: hide broken image icon
        e.target.style.opacity = '0.5';
        e.target.alt = 'Image unavailable';
      }}
      {...props}
    />
  );
}
