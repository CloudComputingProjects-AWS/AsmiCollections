// ============================================
// Phase 13F — File 5/12: FormField Component
// Reusable form field with label, error display, ARIA
// Usage:
//   <FormField label="Email" name="email" errors={errors}>
//     <input type="email" value={...} onChange={...} />
//   </FormField>
// ============================================
export default function FormField({ label, name, errors = {}, required, hint, children, className = '' }) {
  const error = errors[name];

  return (
    <div className={`space-y-1 ${className}`}>
      {label && (
        <label
          htmlFor={name}
          className="block text-sm font-medium text-gray-700"
        >
          {label}
          {required && <span className="text-red-500 ml-0.5" aria-hidden="true">*</span>}
        </label>
      )}
      {children}
      {hint && !error && (
        <p className="text-xs text-gray-500" id={`${name}-hint`}>{hint}</p>
      )}
      {error && (
        <p
          className="text-xs text-red-600 flex items-center gap-1"
          id={`${name}-error`}
          role="alert"
        >
          <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3m0 3h.01" />
          </svg>
          {error}
        </p>
      )}
    </div>
  );
}

// ============================================
// ValidatedInput — input with built-in ARIA and styling
// ============================================
export function ValidatedInput({ name, errors = {}, className = '', ...props }) {
  const error = errors[name];
  return (
    <input
      id={name}
      name={name}
      aria-invalid={!!error}
      aria-describedby={error ? `${name}-error` : props['aria-describedby']}
      className={`w-full px-3 py-2 border rounded-lg text-sm transition-colors
        focus:outline-none focus:ring-2 focus:ring-offset-0
        ${error
          ? 'border-red-400 focus:ring-red-300 bg-red-50/30'
          : 'border-gray-300 focus:ring-blue-400 focus:border-blue-400'
        } ${className}`}
      {...props}
    />
  );
}

// ============================================
// ValidatedSelect — select with ARIA
// ============================================
export function ValidatedSelect({ name, errors = {}, children, className = '', ...props }) {
  const error = errors[name];
  return (
    <select
      id={name}
      name={name}
      aria-invalid={!!error}
      aria-describedby={error ? `${name}-error` : undefined}
      className={`w-full px-3 py-2 border rounded-lg text-sm transition-colors
        focus:outline-none focus:ring-2 focus:ring-offset-0
        ${error
          ? 'border-red-400 focus:ring-red-300 bg-red-50/30'
          : 'border-gray-300 focus:ring-blue-400 focus:border-blue-400'
        } ${className}`}
      {...props}
    >
      {children}
    </select>
  );
}

// ============================================
// ValidatedTextarea — textarea with ARIA
// ============================================
export function ValidatedTextarea({ name, errors = {}, className = '', ...props }) {
  const error = errors[name];
  return (
    <textarea
      id={name}
      name={name}
      aria-invalid={!!error}
      aria-describedby={error ? `${name}-error` : undefined}
      className={`w-full px-3 py-2 border rounded-lg text-sm transition-colors resize-y
        focus:outline-none focus:ring-2 focus:ring-offset-0
        ${error
          ? 'border-red-400 focus:ring-red-300 bg-red-50/30'
          : 'border-gray-300 focus:ring-blue-400 focus:border-blue-400'
        } ${className}`}
      {...props}
    />
  );
}
