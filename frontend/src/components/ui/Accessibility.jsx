// ============================================
// Phase 13F â€” File 6/12: Accessibility Components
// SkipToContent, FocusTrap, VisuallyHidden, ScreenReaderOnly
// ============================================
import { useEffect, useRef } from 'react';

/**
 * SkipToContent â€” renders a skip link for keyboard users
 * Place at the top of App.jsx, BEFORE any other content.
 * Usage: <SkipToContent />
 * Then add id="main-content" to your <main> tag.
 */
export function SkipToContent({ targetId = 'main-content', label = 'Skip to main content' }) {
  return (
    <a
      href={`#${targetId}`} tabIndex={0}
      className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[99999]
        focus:bg-white focus:text-blue-700 focus:px-4 focus:py-2 focus:rounded-lg
        focus:shadow-lg focus:border-2 focus:border-blue-500 focus:outline-none
        focus:text-sm focus:font-semibold"
    >
      {label}
    </a>
  );
}

/**
 * FocusTrap â€” traps focus within a container (for modals/dialogs)
 * Usage: <FocusTrap active={isOpen}><Modal /></FocusTrap>
 */
export function FocusTrap({ active = true, children }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!active || !containerRef.current) return;

    const container = containerRef.current;
    const focusableSelector =
      'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

    const handleKeyDown = (e) => {
      if (e.key !== 'Tab') return;
      const focusable = container.querySelectorAll(focusableSelector);
      if (!focusable.length) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    // Auto-focus first focusable element
    const focusable = container.querySelectorAll(focusableSelector);
    if (focusable.length) focusable[0].focus();

    container.addEventListener('keydown', handleKeyDown);
    return () => container.removeEventListener('keydown', handleKeyDown);
  }, [active]);

  return <div ref={containerRef}>{children}</div>;
}

/**
 * VisuallyHidden â€” content visible only to screen readers
 * Usage: <VisuallyHidden>Additional context for screen readers</VisuallyHidden>
 */
export function VisuallyHidden({ children, as: Tag = 'span', ...props }) {
  return (
    <Tag className="sr-only" {...props}>
      {children}
    </Tag>
  );
}

/**
 * LiveRegion â€” announces dynamic content changes to screen readers
 * Usage: <LiveRegion>{statusMessage}</LiveRegion>
 */
export function LiveRegion({ children, politeness = 'polite' }) {
  return (
    <div aria-live={politeness} aria-atomic="true" className="sr-only">
      {children}
    </div>
  );
}
