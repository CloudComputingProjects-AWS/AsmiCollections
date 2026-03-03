import clsx from 'clsx';
import Spinner from './Spinner';

const variants = {
  primary: 'bg-brand-600 text-white hover:bg-brand-700 focus-visible:ring-brand-500',
  secondary: 'bg-surface-sunken text-ink hover:bg-surface-sunken/80 focus-visible:ring-ink-faint',
  outline: 'border border-ink-faint text-ink hover:bg-surface-sunken focus-visible:ring-brand-500',
  danger: 'bg-error text-white hover:bg-error/90 focus-visible:ring-error',
  ghost: 'text-ink-muted hover:bg-surface-sunken focus-visible:ring-brand-500',
};

const sizeClasses = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

export default function Button({
  children, variant = 'primary', size = 'md', loading = false,
  disabled = false, className, ...props
}) {
  return (
    <button
      className={clsx(
        'inline-flex items-center justify-center gap-2 font-medium rounded-[var(--radius-md)]',
        'transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variants[variant], sizeClasses[size], className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Spinner size="sm" className="text-current" />}
      {children}
    </button>
  );
}
