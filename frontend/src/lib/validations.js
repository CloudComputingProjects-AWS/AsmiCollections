// ============================================
// Phase 13F — File 1/12: Zod Frontend Validation Schemas
// Mirrors backend Pydantic schemas for consistency
// npm install zod (if not already installed)
// ============================================
import { z } from 'zod';

// ---- Shared field validators ----
const emailField = z.string().email('Valid email address required');
const passwordField = z.string()
  .min(8, 'Minimum 8 characters')
  .max(128, 'Maximum 128 characters')
  .regex(/[A-Z]/, 'At least one uppercase letter')
  .regex(/[a-z]/, 'At least one lowercase letter')
  .regex(/[0-9]/, 'At least one digit')
  .regex(/[^A-Za-z0-9]/, 'At least one special character');
const phoneField = z.string()
  .regex(/^[6-9]\d{9}$/, 'Valid 10-digit Indian mobile required')
  .optional().or(z.literal(''));
const uuidField = z.string().uuid('Invalid ID');
const postalField = z.string().regex(/^\d{6}$/, 'Valid 6-digit PIN code required');

// ============================================
// AUTH SCHEMAS
// ============================================
export const registerSchema = z.object({
  email: emailField,
  password: passwordField,
  confirm_password: z.string(),
  first_name: z.string().min(1, 'First name is required').max(100),
  last_name: z.string().max(100).optional().or(z.literal('')),
  phone: phoneField,
  consent_terms: z.literal(true, {
    errorMap: () => ({ message: 'You must accept the Terms of Service' }),
  }),
  consent_privacy: z.literal(true, {
    errorMap: () => ({ message: 'You must accept the Privacy Policy' }),
  }),
  consent_marketing_email: z.boolean().optional(),
  consent_marketing_sms: z.boolean().optional(),
}).refine((d) => d.password === d.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
});

export const loginSchema = z.object({
  email: emailField,
  password: z.string().min(1, 'Password is required'),
  totp_code: z.string().length(6, '6-digit code required').regex(/^\d+$/, 'Digits only').optional().or(z.literal('')),
});

export const forgotPasswordSchema = z.object({ email: emailField });

export const resetPasswordSchema = z.object({
  password: passwordField,
  confirm_password: z.string(),
}).refine((d) => d.password === d.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
});

export const changePasswordSchema = z.object({
  current_password: z.string().min(1, 'Current password is required'),
  new_password: passwordField,
  confirm_password: z.string(),
}).refine((d) => d.new_password === d.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
});

// ============================================
// PROFILE & ADDRESS SCHEMAS
// ============================================
export const profileSchema = z.object({
  first_name: z.string().min(1, 'First name is required').max(100),
  last_name: z.string().max(100).optional().or(z.literal('')),
  phone: phoneField,
});

export const addressSchema = z.object({
  label: z.enum(['home', 'office', 'other'], { errorMap: () => ({ message: 'Select address type' }) }),
  full_name: z.string().min(1, 'Full name is required').max(200),
  phone: z.string().regex(/^[6-9]\d{9}$/, 'Valid 10-digit mobile required'),
  address_line_1: z.string().min(1, 'Address line 1 is required').max(500),
  address_line_2: z.string().max(500).optional().or(z.literal('')),
  city: z.string().min(1, 'City is required').max(100),
  state: z.string().min(1, 'State is required').max(100),
  postal_code: postalField,
  country: z.string().min(1, 'Country is required').max(100),
  is_default: z.boolean().optional(),
});

// ============================================
// CHECKOUT SCHEMA
// ============================================
export const checkoutSchema = z.object({
  shipping_address_id: uuidField,
  billing_address_id: uuidField.optional(),
  payment_method: z.enum(['razorpay', 'stripe'], { errorMap: () => ({ message: 'Select payment method' }) }),
  coupon_code: z.string().max(50).optional().or(z.literal('')),
  notes: z.string().max(500).optional().or(z.literal('')),
});

// ============================================
// ADMIN: PRODUCT SCHEMAS
// ============================================
export const productSchema = z.object({
  title: z.string().min(1, 'Product title is required').max(500),
  description: z.string().optional().or(z.literal('')),
  category_id: uuidField,
  brand: z.string().max(200).optional().or(z.literal('')),
  base_price: z.coerce.number().min(0.01, 'Price must be > 0'),
  sale_price: z.coerce.number().min(0).optional().nullable(),
  hsn_code: z.string().max(20).optional().or(z.literal('')),
  gst_rate: z.coerce.number().min(0).max(28),
  tags: z.array(z.string()).optional(),
  attributes: z.record(z.string(), z.any()).optional(),
  is_active: z.boolean().optional(),
  is_featured: z.boolean().optional(),
  meta_title: z.string().max(200).optional().or(z.literal('')),
  meta_description: z.string().max(500).optional().or(z.literal('')),
});

export const variantSchema = z.object({
  size: z.string().max(20).optional().or(z.literal('')),
  color: z.string().max(50).optional().or(z.literal('')),
  color_hex: z.string().regex(/^#[0-9A-Fa-f]{6}$/, 'Invalid hex color').optional().or(z.literal('')),
  sku: z.string().min(1, 'SKU is required').max(100),
  stock_quantity: z.coerce.number().int().min(0, 'Stock cannot be negative'),
  price_override: z.coerce.number().min(0).optional().nullable(),
  weight_grams: z.coerce.number().int().min(0).optional().nullable(),
});

// ============================================
// ADMIN: CATEGORY SCHEMA
// ============================================
export const categorySchema = z.object({
  name: z.string().min(1, 'Category name is required').max(100),
  slug: z.string().min(1, 'Slug is required').max(100)
    .regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/, 'Lowercase with hyphens only'),
  gender: z.enum(['men', 'women', 'boys', 'girls', 'unisex'], { errorMap: () => ({ message: 'Select gender' }) }),
  age_group: z.enum(['infant', 'kids', 'teen', 'adult', 'senior'], { errorMap: () => ({ message: 'Select age group' }) }),
  parent_category_id: uuidField.optional().nullable(),
  description: z.string().max(1000).optional().or(z.literal('')),
  sort_order: z.coerce.number().int().min(0).optional(),
  is_active: z.boolean().optional(),
});

// ============================================
// ADMIN: COUPON SCHEMA
// ============================================
export const couponSchema = z.object({
  code: z.string().min(1, 'Coupon code is required').max(50)
    .regex(/^[A-Z0-9]+$/, 'Uppercase alphanumeric only'),
  description: z.string().max(500).optional().or(z.literal('')),
  type: z.enum(['flat', 'percent'], { errorMap: () => ({ message: 'Select discount type' }) }),
  value: z.coerce.number().min(0.01, 'Value must be > 0'),
  min_order_value: z.coerce.number().min(0).optional(),
  max_discount: z.coerce.number().min(0).optional().nullable(),
  usage_limit: z.coerce.number().int().min(1).optional().nullable(),
  per_user_limit: z.coerce.number().int().min(1).optional(),
  starts_at: z.string().min(1, 'Start date is required'),
  expires_at: z.string().min(1, 'Expiry date is required'),
  is_active: z.boolean().optional(),
}).refine((d) => new Date(d.expires_at) > new Date(d.starts_at), {
  message: 'Expiry must be after start date',
  path: ['expires_at'],
});

// ============================================
// ADMIN: ATTRIBUTE DEFINITION SCHEMA
// ============================================
export const attributeDefSchema = z.object({
  attribute_key: z.string().min(1, 'Key is required').max(50)
    .regex(/^[a-z_]+$/, 'Lowercase with underscores only'),
  display_name: z.string().min(1, 'Display name is required').max(100),
  input_type: z.enum(['text', 'select', 'multiselect'], { errorMap: () => ({ message: 'Select input type' }) }),
  options: z.array(z.string()).optional(),
  is_filterable: z.boolean().optional(),
  is_required: z.boolean().optional(),
  sort_order: z.coerce.number().int().min(0).optional(),
});

// ============================================
// REVIEW SCHEMA
// ============================================
export const reviewSchema = z.object({
  rating: z.coerce.number().int().min(1, 'Rating is required').max(5),
  title: z.string().max(200).optional().or(z.literal('')),
  comment: z.string().max(2000).optional().or(z.literal('')),
  fit_feedback: z.enum(['true_to_size', 'runs_small', 'runs_large', '']).optional(),
});

// ============================================
// VALIDATION HELPER — use in any form
// ============================================
/**
 * Usage:
 *   import { validateForm, loginSchema } from '../lib/validations';
 *   const { success, data, errors } = validateForm(loginSchema, formData);
 *   if (!success) { setErrors(errors); return; }
 *   // proceed with data
 */
export function validateForm(schema, data) {
  const result = schema.safeParse(data);
  if (result.success) {
    return { success: true, data: result.data, errors: {} };
  }
  const errors = {};
  result.error.issues.forEach((issue) => {
    const path = issue.path.join('.');
    if (!errors[path]) errors[path] = issue.message;
  });
  return { success: false, data: null, errors };
}
