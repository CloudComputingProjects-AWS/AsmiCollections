"""
OpenAPI Documentation Enhancement â€” Phase 13.

Provides rich API documentation metadata for Swagger UI at /docs.
Import and apply in main.py to enhance auto-generated docs.

Usage in main.py:
    from app.core.openapi_config import custom_openapi
    app.openapi = lambda: custom_openapi(app)
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


API_TAGS_METADATA = [
    {
        "name": "Auth",
        "description": (
            "User authentication: register, login, logout, refresh tokens, "
            "email verification, password reset. JWT in httpOnly cookies."
        ),
    },
    {
        "name": "2FA (TOTP)",
        "description": "Two-Factor Authentication for admin users using TOTP.",
    },
    {
        "name": "Admin â€” Product Management",
        "description": (
            "Product CRUD, categories, variants, attributes, inventory, "
            "size guides, bulk upload. Requires ProductManager role."
        ),
    },
    {
        "name": "Admin â€” Image Pipeline",
        "description": (
            "Product image upload via S3 pre-signed URLs, processing callbacks, "
            "reordering. Images auto-processed to WebP via Lambda."
        ),
    },
    {
        "name": "Public Catalog",
        "description": (
            "Customer-facing product browsing: listings, filters (size, color, "
            "price, apparel attributes), search, product detail, categories."
        ),
    },
    {
        "name": "Wishlist",
        "description": "Save/remove products to wishlist. Requires login.",
    },
    {
        "name": "Reviews",
        "description": (
            "Product reviews: submit, list, moderation. "
            "Verified purchase badge for authenticated buyers."
        ),
    },
    {
        "name": "Cart",
        "description": (
            "Shopping cart: add/update/remove items, guest cart merge on login, "
            "real-time stock check, coupon application."
        ),
    },
    {
        "name": "Coupons",
        "description": "Admin coupon management: create, edit, deactivate.",
    },
    {
        "name": "Checkout & Orders",
        "description": (
            "Checkout flow: address selection, GST tax calculation "
            "(CGST/SGST/IGST), stock reservation, order placement. "
            "Order state machine enforced."
        ),
    },
    {
        "name": "Payments",
        "description": (
            "Payment processing: Razorpay (India), Stripe (Global). "
            "Webhook handlers with idempotency. FX rate locking."
        ),
    },
    {
        "name": "Invoices & Credit Notes",
        "description": (
            "GST-compliant invoice generation (PDF), credit notes on refund, "
            "sequential numbering per financial year, admin reports."
        ),
    },
    {
        "name": "Shipping",
        "description": (
            "Shipment creation, tracking, courier integration "
            "(Shiprocket/Delhivery for India, FedEx/DHL global)."
        ),
    },
    {
        "name": "Returns & Refunds",
        "description": (
            "Return requests, approval/rejection, refund processing, "
            "restock on return received. Credit note auto-generated."
        ),
    },
    {
        "name": "Admin â€” Dashboard & Reports",
        "description": (
            "Revenue dashboard, sales reports, GST summary, "
            "coupon performance, audit logs, user management."
        ),
    },
    {
        "name": "Privacy & Consent",
        "description": (
            "DPDP Act 2023 + GDPR compliance: consent management, "
            "account deletion (30-day grace), data export, cookie consent."
        ),
    },
]


def custom_openapi(app: FastAPI) -> dict:
    """Generate enhanced OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Ashmi E-Commerce Apparel Portal API",
        version="2.5.0",
        summary="Production-Ready E-Commerce API â€” India + Global",
        description=(
            "## Overview\n\n"
            "Full-featured e-commerce API for apparel retail, supporting:\n\n"
            "- **Multi-role RBAC** (5 roles: admin, product_manager, "
            "order_manager, finance_manager, customer)\n"
            "- **GST-compliant invoicing** (CGST/SGST/IGST, HSN codes)\n"
            "- **Order state machine** (12 statuses, enforced transitions)\n"
            "- **Dual payment gateways** (Razorpay for India, Stripe for global)\n"
            "- **Image processing pipeline** (S3 â†’ Lambda â†’ WebP)\n"
            "- **Privacy compliance** (DPDP Act 2023, GDPR)\n\n"
            "## Authentication\n\n"
            "JWT Bearer tokens in httpOnly cookies. Admin routes require 2FA (TOTP).\n\n"
            "## Base URL\n\n"
            "`/api/v1/`"
        ),
        routes=app.routes,
        tags=API_TAGS_METADATA,
    )

    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT access token",
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema
