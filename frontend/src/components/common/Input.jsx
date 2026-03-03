import { forwardRef, useState } from 'react';
import clsx from 'clsx';
import { Eye, EyeOff } from 'lucide-react';

const Input = forwardRef(function Input(
  { label, error, type = 'text', icon: Icon, className, ...props }, ref
) {
  const [showPassword, setShowPassword] = useState(false);
  const isPassword = type === 'password';
  const inputType = isPassword && showPassword ? 'text' : type;

  return (
    <div className="space-y-1.5">
      {label && (
        <label className="block text-sm font-medium text-ink-muted">{label}</label>
      )}
      <div className="relative">
        {Icon && (
          <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-ink-faint">
            <Icon size={18} />
          </div>
        )}
        <input
          ref={ref}
          type={inputType}
          className={clsx(
            'block w-full rounded-[var(--radius-md)] border bg-surface-raised px-3 py-2 text-sm',
            'placeholder:text-ink-faint transition-colors duration-150',
            'focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500',
            error ? 'border-error' : 'border-ink-faint/30',
            Icon && 'pl-10',
            isPassword && 'pr-10',
            className
          )}
          {...props}
        />
        {isPassword && (
          <button
            type="button"
            tabIndex={-1}
            onClick={() => setShowPassword(!showPassword)}
            aria-label={showPassword ? "Hide password" : "Show password"}
            className="absolute inset-y-0 right-0 flex items-center pr-3 text-ink-faint hover:text-ink-muted"
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
      </div>
      {error && <p className="text-xs text-error">{error}</p>}
    </div>
  );
});

export default Input;
