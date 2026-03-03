import { useState, useCallback } from 'react';

/**
 * Lightweight form hook — no external deps.
 * Usage: const { values, errors, set, setError, validate, reset } = useForm(initialValues, validationRules);
 */
export default function useForm(initialValues = {}, validationRules = {}) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});

  const set = useCallback((key) => (e) => {
    const val = e?.target ? (e.target.type === 'checkbox' ? e.target.checked : e.target.value) : e;
    setValues((prev) => ({ ...prev, [key]: val }));
    setErrors((prev) => ({ ...prev, [key]: undefined }));
  }, []);

  const setError = useCallback((key, msg) => {
    setErrors((prev) => ({ ...prev, [key]: msg }));
  }, []);

  const validate = useCallback(() => {
    const newErrors = {};
    for (const [key, rules] of Object.entries(validationRules)) {
      for (const rule of rules) {
        const error = rule(values[key], values);
        if (error) { newErrors[key] = error; break; }
      }
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [values, validationRules]);

  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
  }, [initialValues]);

  return { values, errors, set, setError, setErrors, setValues, validate, reset };
}

// ── Common validators ──
export const required = (msg = 'Required') => (v) => (!v && v !== 0 ? msg : null);
export const email = (msg = 'Invalid email') => (v) => (v && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) ? msg : null);
export const minLength = (n, msg) => (v) => (v && v.length < n ? (msg || `Minimum ${n} characters`) : null);
export const matches = (field, msg = 'Does not match') => (v, all) => (v !== all[field] ? msg : null);
