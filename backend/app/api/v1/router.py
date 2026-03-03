"""
API v1 router — aggregates all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.totp import router as totp_router
from app.api.v1.endpoints.admin_products import router as admin_products_router
from app.api.v1.endpoints.admin_images import router as admin_images_router
from app.api.v1.endpoints.catalog import router as catalog_router
from app.api.v1.endpoints.wishlist_reviews import (
    review_router,
    admin_review_router,
)
from app.api.v1.endpoints.cart_coupons import (
    cart_router,
    coupon_router,
    admin_coupon_router,
)

api_v1_router = APIRouter(prefix="/api/v1")

# Phase 1: Auth
api_v1_router.include_router(auth_router)

# Phase 2: Admin 2FA
api_v1_router.include_router(totp_router)

# Phase 2: Admin Product Management
api_v1_router.include_router(admin_products_router)

# Phase 3: Image Pipeline
api_v1_router.include_router(admin_images_router)

# Phase 4: Public Catalog
api_v1_router.include_router(catalog_router)

# Phase 5: Wishlist & Reviews
api_v1_router.include_router(review_router)
api_v1_router.include_router(admin_review_router)

# Phase 6: Cart & Coupons
api_v1_router.include_router(cart_router)
api_v1_router.include_router(coupon_router)
api_v1_router.include_router(admin_coupon_router)

# Phase 7: Checkout & Orders
from app.api.v1.endpoints.orders import (
    address_router,
    checkout_router,
    order_router,
    admin_order_router,
)
api_v1_router.include_router(address_router)
api_v1_router.include_router(checkout_router)
api_v1_router.include_router(order_router)
api_v1_router.include_router(admin_order_router)


# Phase 9: Invoice & Credit Notes
from app.api.v1.endpoints.invoices import router as invoice_router
api_v1_router.include_router(invoice_router)

# Phase 10: Shipping, Returns & Refunds
from app.api.v1.endpoints.shipping_returns import (
    customer_returns_router,
    admin_shipping_router,
    admin_returns_router,
    admin_refunds_router,
)
api_v1_router.include_router(customer_returns_router)
api_v1_router.include_router(admin_shipping_router)
api_v1_router.include_router(admin_returns_router)
api_v1_router.include_router(admin_refunds_router)

# Phase 11: Admin Dashboard, Reports, Audit Logs & User Management
from app.api.v1.endpoints.admin_dashboard import (
    dashboard_router,
    reports_router,
    exports_router,
    audit_router,
    user_mgmt_router,
)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(exports_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(user_mgmt_router)

from app.api.v1.endpoints.privacy import router as privacy_router
api_v1_router.include_router(privacy_router)

# Phase F3: User Profile (change password, profile, addresses)
from app.api.v1.endpoints.user import router as user_profile_router
api_v1_router.include_router(user_profile_router)

# Phase 13H: Store Settings
from app.api.v1.endpoints.admin_settings import router as admin_settings_router
api_v1_router.include_router(admin_settings_router)
