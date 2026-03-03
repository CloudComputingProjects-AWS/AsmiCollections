// ============================================
// Phase 13F — File 2/12: useFormValidation Hook
// Integrates Zod schemas with React form state
// ============================================
import { useState, useCallback } from 'react';
import { validateForm } from '../lib/validations';

/**
 * Usage:
 *   import { useFormValidation } from '../hooks/useFormValidation';
 *   import { loginSchema } from '../lib/validations';
 *
 *   const { errors, validate, clearError, clearErrors, getFieldProps } = useFormValidation(loginSchema);
 *
 *   const handleSubmit = (formData) => {
 *     const result = validate(formData);
 *     if (!result.success) return;
 *     // proceed with result.data (parsed & typed)
 *   };
 *
 *   // In JSX:
 *   <input {...getFieldProps('email')} />
 *   {errors.email && <span className="text-red-500 text-sm">{errors.email}</span>}
 */
export function useFormValidation(schema) {
  const [errors, setErrors] = useState({});

  const validate = useCallback(
    (data) => {
      const result = validateForm(schema, data);
      if (!result.success) {
        setErrors(result.errors);
        return { success: false, data: null };
      }
      setErrors({});
      return { success: true, data: result.data };
    },
    [schema]
  );

  const validateField = useCallback(
    (field, value, allData = {}) => {
      const testData = { ...allData, [field]: value };
      const result = schema.safeParse(testData);
      if (result.success) {
        setErrors((prev) => {
          const next = { ...prev };
          delete next[field];
          return next;
        });
        return true;
      }
      const fieldError = result.error.issues.find(
        (i) => i.path.join('.') === field
      );
      if (fieldError) {
        setErrors((prev) => ({ ...prev, [field]: fieldError.message }));
        return false;
      }
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
      return true;
    },
    [schema]
  );

  const clearError = useCallback((field) => {
    setErrors((prev) => {
      const next = { ...prev };
      delete next[field];
      return next;
    });
  }, []);

  const clearErrors = useCallback(() => setErrors({}), []);

  // Returns ARIA props for accessible error display
  const getFieldProps = useCallback(
    (field) => ({
      'aria-invalid': !!errors[field],
      'aria-describedby': errors[field] ? `${field}-error` : undefined,
    }),
    [errors]
  );

  return { errors, validate, validateField, clearError, clearErrors, getFieldProps };
}
