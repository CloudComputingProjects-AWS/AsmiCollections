// ============================================
// Phase 13F — Unit Tests: Validation Schemas
// Run: npx vitest run src/tests/unit/validations.test.js
// (Vitest comes with Vite projects)
// ============================================
import { describe, it, expect } from 'vitest';
import {
  registerSchema,
  loginSchema,
  addressSchema,
  productSchema,
  couponSchema,
  categorySchema,
  reviewSchema,
  changePasswordSchema,
  validateForm,
} from '../../lib/validations';

describe('registerSchema', () => {
  const valid = {
    email: 'test@example.com',
    password: 'StrongP@ss1',
    confirm_password: 'StrongP@ss1',
    first_name: 'John',
    consent_terms: true,
    consent_privacy: true,
  };

  it('accepts valid registration data', () => {
    const r = registerSchema.safeParse(valid);
    expect(r.success).toBe(true);
  });

  it('rejects missing email', () => {
    const r = registerSchema.safeParse({ ...valid, email: '' });
    expect(r.success).toBe(false);
  });

  it('rejects weak password (no uppercase)', () => {
    const r = registerSchema.safeParse({ ...valid, password: 'weakpass@1', confirm_password: 'weakpass@1' });
    expect(r.success).toBe(false);
  });

  it('rejects password mismatch', () => {
    const r = registerSchema.safeParse({ ...valid, confirm_password: 'DifferentP@ss1' });
    expect(r.success).toBe(false);
  });

  it('rejects if terms not accepted', () => {
    const r = registerSchema.safeParse({ ...valid, consent_terms: false });
    expect(r.success).toBe(false);
  });

  it('rejects if privacy not accepted', () => {
    const r = registerSchema.safeParse({ ...valid, consent_privacy: false });
    expect(r.success).toBe(false);
  });
});

describe('loginSchema', () => {
  it('accepts valid login', () => {
    const r = loginSchema.safeParse({ email: 'a@b.com', password: '123' });
    expect(r.success).toBe(true);
  });

  it('rejects invalid email', () => {
    const r = loginSchema.safeParse({ email: 'notanemail', password: '123' });
    expect(r.success).toBe(false);
  });

  it('rejects empty password', () => {
    const r = loginSchema.safeParse({ email: 'a@b.com', password: '' });
    expect(r.success).toBe(false);
  });

  it('accepts optional TOTP code', () => {
    const r = loginSchema.safeParse({ email: 'a@b.com', password: '123', totp_code: '123456' });
    expect(r.success).toBe(true);
  });

  it('rejects non-6-digit TOTP', () => {
    const r = loginSchema.safeParse({ email: 'a@b.com', password: '123', totp_code: '12345' });
    expect(r.success).toBe(false);
  });
});

describe('addressSchema', () => {
  const valid = {
    label: 'home',
    full_name: 'John Doe',
    phone: '9876543210',
    address_line_1: '123 Main St',
    city: 'Mumbai',
    state: 'Maharashtra',
    postal_code: '400001',
    country: 'India',
  };

  it('accepts valid address', () => {
    const r = addressSchema.safeParse(valid);
    expect(r.success).toBe(true);
  });

  it('rejects invalid postal code (not 6 digits)', () => {
    const r = addressSchema.safeParse({ ...valid, postal_code: '4000' });
    expect(r.success).toBe(false);
  });

  it('rejects invalid phone (not starting with 6-9)', () => {
    const r = addressSchema.safeParse({ ...valid, phone: '1234567890' });
    expect(r.success).toBe(false);
  });

  it('rejects invalid label', () => {
    const r = addressSchema.safeParse({ ...valid, label: 'garage' });
    expect(r.success).toBe(false);
  });
});

describe('productSchema', () => {
  it('accepts valid product', () => {
    const r = productSchema.safeParse({
      title: 'Cotton T-Shirt',
      category_id: '550e8400-e29b-41d4-a716-446655440000',
      base_price: 999,
      gst_rate: 5,
    });
    expect(r.success).toBe(true);
  });

  it('rejects zero price', () => {
    const r = productSchema.safeParse({
      title: 'Test',
      category_id: '550e8400-e29b-41d4-a716-446655440000',
      base_price: 0,
      gst_rate: 5,
    });
    expect(r.success).toBe(false);
  });

  it('coerces string price to number', () => {
    const r = productSchema.safeParse({
      title: 'Test',
      category_id: '550e8400-e29b-41d4-a716-446655440000',
      base_price: '999.50',
      gst_rate: '12',
    });
    expect(r.success).toBe(true);
    if (r.success) {
      expect(r.data.base_price).toBe(999.5);
      expect(r.data.gst_rate).toBe(12);
    }
  });
});

describe('couponSchema', () => {
  const valid = {
    code: 'SAVE200',
    type: 'flat',
    value: 200,
    starts_at: '2026-01-01T00:00:00Z',
    expires_at: '2026-12-31T23:59:59Z',
  };

  it('accepts valid coupon', () => {
    const r = couponSchema.safeParse(valid);
    expect(r.success).toBe(true);
  });

  it('rejects lowercase code', () => {
    const r = couponSchema.safeParse({ ...valid, code: 'save200' });
    expect(r.success).toBe(false);
  });

  it('rejects expiry before start', () => {
    const r = couponSchema.safeParse({
      ...valid,
      starts_at: '2026-12-31T23:59:59Z',
      expires_at: '2026-01-01T00:00:00Z',
    });
    expect(r.success).toBe(false);
  });
});

describe('categorySchema', () => {
  it('accepts valid category', () => {
    const r = categorySchema.safeParse({
      name: 'T-Shirts',
      slug: 'men-tshirts',
      gender: 'men',
      age_group: 'adult',
    });
    expect(r.success).toBe(true);
  });

  it('rejects slug with uppercase', () => {
    const r = categorySchema.safeParse({
      name: 'T-Shirts',
      slug: 'Men-Tshirts',
      gender: 'men',
      age_group: 'adult',
    });
    expect(r.success).toBe(false);
  });
});

describe('reviewSchema', () => {
  it('accepts valid review', () => {
    const r = reviewSchema.safeParse({ rating: 4, comment: 'Great product' });
    expect(r.success).toBe(true);
  });

  it('rejects rating > 5', () => {
    const r = reviewSchema.safeParse({ rating: 6 });
    expect(r.success).toBe(false);
  });

  it('rejects rating 0', () => {
    const r = reviewSchema.safeParse({ rating: 0 });
    expect(r.success).toBe(false);
  });
});

describe('changePasswordSchema', () => {
  it('accepts matching passwords', () => {
    const r = changePasswordSchema.safeParse({
      current_password: 'old',
      new_password: 'NewP@ss123',
      confirm_password: 'NewP@ss123',
    });
    expect(r.success).toBe(true);
  });

  it('rejects mismatch', () => {
    const r = changePasswordSchema.safeParse({
      current_password: 'old',
      new_password: 'NewP@ss123',
      confirm_password: 'DiffP@ss123',
    });
    expect(r.success).toBe(false);
  });
});

describe('validateForm helper', () => {
  it('returns success true with parsed data', () => {
    const result = validateForm(loginSchema, { email: 'a@b.com', password: 'x' });
    expect(result.success).toBe(true);
    expect(result.data).toEqual({ email: 'a@b.com', password: 'x' });
    expect(result.errors).toEqual({});
  });

  it('returns errors map on failure', () => {
    const result = validateForm(loginSchema, { email: 'bad', password: '' });
    expect(result.success).toBe(false);
    expect(result.errors.email).toBeTruthy();
    expect(result.errors.password).toBeTruthy();
  });
});
