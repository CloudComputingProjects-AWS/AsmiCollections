"""
SQLAlchemy Models — V2.5 Complete Schema (30 tables).
Maps 1:1 to the blueprint database design.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, INET, JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.utils.soft_delete import SoftDeleteMixin


def utcnow():
    return datetime.now(timezone.utc)


def new_uuid():
    return uuid.uuid4()


# ════════════════════════════════════════════════
# SECTION A: CORE USER TABLES
# ════════════════════════════════════════════════


class User(Base, SoftDeleteMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    email_verified = Column(Boolean, default=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    country_code = Column(String(5))
    role = Column(String(20), default="customer", nullable=False)
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime(timezone=True))
    deletion_requested_at = Column(DateTime(timezone=True))
    deletion_scheduled_at = Column(DateTime(timezone=True))
    totp_secret = Column(String(64))
    totp_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    addresses = relationship("UserAddress", back_populates="user", lazy="selectin")
    consents = relationship("UserConsent", back_populates="user", lazy="selectin")
    cart = relationship("Cart", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="user", lazy="dynamic")
    reviews = relationship("Review", back_populates="user")


class UserAddress(Base, SoftDeleteMixin):
    __tablename__ = "user_addresses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    label = Column(String(20), nullable=False)
    full_name = Column(String(200))
    phone = Column(String(20))
    address_line_1 = Column(String(500), nullable=False)
    address_line_2 = Column(String(500))
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False)
    is_default = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="addresses")


class UserConsent(Base):
    __tablename__ = "user_consents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    consent_type = Column(String(30), nullable=False)
    granted = Column(Boolean, nullable=False)
    granted_at = Column(DateTime(timezone=True))
    revoked_at = Column(DateTime(timezone=True))
    ip_address = Column(INET)
    user_agent = Column(Text)
    version = Column(String(20))
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="consents")


class AccountDeletionRequest(Base):
    __tablename__ = "account_deletion_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reason = Column(Text)
    status = Column(String(20), default="pending")
    requested_at = Column(DateTime(timezone=True), default=utcnow)
    grace_ends_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    anonymized_fields = Column(JSONB)


# ════════════════════════════════════════════════
# SECTION B: AUTH & SECURITY TABLES
# ════════════════════════════════════════════════


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(500), nullable=False)
    family_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow)


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(500), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True))


# ════════════════════════════════════════════════
# SECTION C: PRODUCT & CATALOG TABLES
# ════════════════════════════════════════════════


class Category(Base, SoftDeleteMixin):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    gender = Column(String(10), nullable=False)
    age_group = Column(String(10), nullable=False)
    parent_category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    image_url = Column(String(1000))
    description = Column(Text)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("idx_categories_gender_age", "gender", "age_group"),
    )

    products = relationship("Product", back_populates="category")


class Product(Base, SoftDeleteMixin):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    title = Column(String(500), nullable=False)
    slug = Column(String(500), unique=True, nullable=False)
    description = Column(Text)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False, index=True)
    brand = Column(String(200))
    base_price = Column(Numeric(12, 2), nullable=False)
    sale_price = Column(Numeric(12, 2))
    base_currency = Column(String(3), default="INR")
    hsn_code = Column(String(20))
    gst_rate = Column(Numeric(4, 2), default=0)
    tags = Column(ARRAY(Text))
    attributes = Column(JSONB, default={})
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    meta_title = Column(String(200))
    meta_description = Column(String(500))
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("idx_products_active", "is_active", postgresql_where=Column("deleted_at").is_(None)),
    )

    category = relationship("Category", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product", lazy="selectin")
    images = relationship("ProductImage", back_populates="product", lazy="selectin")
    reviews = relationship("Review", back_populates="product")


class AttributeDefinition(Base):
    __tablename__ = "attribute_definitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    attribute_key = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    input_type = Column(String(20), nullable=False)
    options = Column(ARRAY(Text))
    is_filterable = Column(Boolean, default=False)
    is_required = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    category_ids = Column(ARRAY(UUID(as_uuid=True)))
    created_at = Column(DateTime(timezone=True), default=utcnow)


class ProductVariant(Base, SoftDeleteMixin):
    __tablename__ = "product_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    size = Column(String(20))
    color = Column(String(50))
    color_hex = Column(String(7))
    sku = Column(String(100), unique=True, nullable=False, index=True)
    stock_quantity = Column(Integer, nullable=False, default=0)
    price_override = Column(Numeric(12, 2))
    weight_grams = Column(Integer)
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow)

    product = relationship("Product", back_populates="variants")


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    original_url = Column(String(1000), nullable=False)
    processed_url = Column(String(1000))
    thumbnail_url = Column(String(1000))
    medium_url = Column(String(1000))
    alt_text = Column(String(300))
    is_primary = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    processing_status = Column(String(20), default="pending")
    created_at = Column(DateTime(timezone=True), default=utcnow)

    product = relationship("Product", back_populates="images")


class SizeGuide(Base):
    __tablename__ = "size_guides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    size_label = Column(String(10))
    chest_cm = Column(Numeric(5, 1))
    waist_cm = Column(Numeric(5, 1))
    hip_cm = Column(Numeric(5, 1))
    length_cm = Column(Numeric(5, 1))


# ════════════════════════════════════════════════
# SECTION D: INVENTORY RESERVATION
# ════════════════════════════════════════════════


class InventoryReservation(Base):
    __tablename__ = "inventory_reservations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reserved_qty = Column(Integer, nullable=False)
    status = Column(String(20), default="held")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)


# ════════════════════════════════════════════════
# SECTION E: CART TABLES
# ════════════════════════════════════════════════


class Cart(Base):
    __tablename__ = "carts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="cart")
    items = relationship("CartItem", back_populates="cart", lazy="selectin")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    product_variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    added_at = Column(DateTime(timezone=True), default=utcnow)

    cart = relationship("Cart", back_populates="items")

    __table_args__ = (
        UniqueConstraint("cart_id", "product_variant_id"),
        CheckConstraint("quantity > 0", name="ck_cart_item_qty_positive"),
    )


# ════════════════════════════════════════════════
# SECTION F: COUPONS & DISCOUNTS
# ════════════════════════════════════════════════


class Coupon(Base, SoftDeleteMixin):
    __tablename__ = "coupons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(500))
    type = Column(String(10), nullable=False)
    value = Column(Numeric(12, 2), nullable=False)
    min_order_value = Column(Numeric(12, 2), default=0)
    max_discount = Column(Numeric(12, 2))
    usage_limit = Column(Integer)
    used_count = Column(Integer, default=0)
    per_user_limit = Column(Integer, default=1)
    applicable_categories = Column(ARRAY(UUID(as_uuid=True)))
    starts_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow)


class CouponUsage(Base):
    __tablename__ = "coupon_usages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    coupon_id = Column(UUID(as_uuid=True), ForeignKey("coupons.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True))
    used_at = Column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        UniqueConstraint("coupon_id", "user_id", "order_id"),
    )


# ════════════════════════════════════════════════
# SECTION G: ORDERS
# ════════════════════════════════════════════════


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    from_status = Column(String(20))
    to_status = Column(String(20), nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    change_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    order_number = Column(String(30), unique=True, nullable=False, index=True)
    subtotal = Column(Numeric(12, 2), nullable=False)
    tax_amount = Column(Numeric(12, 2), nullable=False, default=0)
    cgst_amount = Column(Numeric(12, 2), default=0)
    sgst_amount = Column(Numeric(12, 2), default=0)
    igst_amount = Column(Numeric(12, 2), default=0)
    shipping_fee = Column(Numeric(12, 2), default=0)
    discount_amount = Column(Numeric(12, 2), default=0)
    grand_total = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    fx_rate_used = Column(Numeric(12, 6), default=1.0)
    fx_rate_source = Column(String(50))
    fx_locked_at = Column(DateTime(timezone=True))
    shipping_address_id = Column(UUID(as_uuid=True), ForeignKey("user_addresses.id"))
    billing_address_id = Column(UUID(as_uuid=True), ForeignKey("user_addresses.id"))
    shipping_name = Column(String(200))
    shipping_address_text = Column(Text)
    shipping_city = Column(String(100))
    shipping_state = Column(String(100))
    shipping_postal_code = Column(String(20))
    shipping_country = Column(String(100))
    payment_method = Column(String(20))
    payment_gateway = Column(String(20))
    payment_gateway_order_id = Column(String(200))
    payment_gateway_txn_id = Column(String(200))
    upi_vpa = Column(String(50), nullable=True)
    payment_status = Column(String(20), default="pending")
    coupon_id = Column(UUID(as_uuid=True), ForeignKey("coupons.id"))
    coupon_code_snapshot = Column(String(50))
    order_status = Column(String(20), default="placed", index=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", lazy="selectin")
    status_history = relationship("OrderStatusHistory", lazy="dynamic")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"))
    product_title_snapshot = Column(String(500), nullable=False)
    brand_snapshot = Column(String(200))
    size_snapshot = Column(String(20))
    color_snapshot = Column(String(50))
    sku_snapshot = Column(String(100), nullable=False)
    image_url_snapshot = Column(String(1000))
    hsn_code_snapshot = Column(String(20))
    attributes_snapshot = Column(JSONB)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    tax_rate = Column(Numeric(4, 2), default=0)
    tax_amount = Column(Numeric(12, 2), default=0)
    line_total = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    order = relationship("Order", back_populates="items")


# ════════════════════════════════════════════════
# SECTION H: INVOICES & CREDIT NOTES
# ════════════════════════════════════════════════


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    invoice_number = Column(String(30), unique=True, nullable=False, index=True)
    invoice_type = Column(String(20), nullable=False, default="tax_invoice")
    seller_name = Column(String(200), nullable=False)
    seller_gstin = Column(String(20))
    seller_address = Column(Text, nullable=False)
    seller_state = Column(String(100))
    seller_state_code = Column(String(5))
    buyer_name = Column(String(200), nullable=False)
    buyer_address = Column(Text, nullable=False)
    buyer_gstin = Column(String(20))
    buyer_state = Column(String(100))
    buyer_state_code = Column(String(5))
    subtotal = Column(Numeric(12, 2), nullable=False)
    cgst_amount = Column(Numeric(12, 2), default=0)
    sgst_amount = Column(Numeric(12, 2), default=0)
    igst_amount = Column(Numeric(12, 2), default=0)
    shipping_fee = Column(Numeric(12, 2), default=0)
    discount_amount = Column(Numeric(12, 2), default=0)
    grand_total = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    place_of_supply = Column(String(100))

    # Relationships
    line_items = relationship('InvoiceLineItem', back_populates='invoice', cascade='all, delete-orphan')
    order = relationship('Order', backref='invoices')
    supply_type = Column(String(20))
    pdf_url = Column(String(1000))
    generated_at = Column(DateTime(timezone=True), default=utcnow)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    order_item_id = Column(UUID(as_uuid=True), ForeignKey("order_items.id"))
    description = Column(String(500), nullable=False)
    hsn_code = Column(String(20))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    taxable_amount = Column(Numeric(12, 2), nullable=False)
    cgst_rate = Column(Numeric(4, 2), default=0)
    cgst_amount = Column(Numeric(12, 2), default=0)
    sgst_rate = Column(Numeric(4, 2), default=0)
    sgst_amount = Column(Numeric(12, 2), default=0)
    igst_rate = Column(Numeric(4, 2), default=0)
    igst_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(12, 2), nullable=False)

    # Relationships
    invoice = relationship('Invoice', back_populates='line_items')


class CreditNote(Base):
    __tablename__ = "credit_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)
    return_id = Column(UUID(as_uuid=True), ForeignKey("returns.id"))
    refund_id = Column(UUID(as_uuid=True), ForeignKey("refunds.id"))
    credit_note_number = Column(String(30), unique=True, nullable=False)
    reason = Column(Text, nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)
    cgst_amount = Column(Numeric(12, 2), default=0)
    sgst_amount = Column(Numeric(12, 2), default=0)
    igst_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(12, 2), nullable=False)
    pdf_url = Column(String(1000))
    issued_at = Column(DateTime(timezone=True), default=utcnow)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class InvoiceSequence(Base):
    __tablename__ = "invoice_sequences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    financial_year = Column(String(10), nullable=False)
    document_type = Column(String(20), nullable=False)
    last_number = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("financial_year", "document_type"),
    )


# ════════════════════════════════════════════════
# SECTION I: RETURNS & REFUNDS
# ════════════════════════════════════════════════


class Return(Base):
    __tablename__ = "returns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    order_item_id = Column(UUID(as_uuid=True), ForeignKey("order_items.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reason = Column(String(50), nullable=False)
    reason_detail = Column(Text)
    return_type = Column(String(10), nullable=False)
    status = Column(String(20), default="requested")
    quantity = Column(Integer, nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    admin_notes = Column(Text)
    pickup_date = Column(Date)
    received_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    return_id = Column(UUID(as_uuid=True), ForeignKey("returns.id"))
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    gateway_refund_id = Column(String(200))
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(String(20), default="initiated")
    refund_method = Column(String(20))
    initiated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow)


# ════════════════════════════════════════════════
# SECTION J: SHIPPING
# ════════════════════════════════════════════════


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    courier_partner = Column(String(50), nullable=False)
    tracking_number = Column(String(200), index=True)
    awb_number = Column(String(100))
    status = Column(String(30), default="created")
    estimated_delivery = Column(Date)
    shipped_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    weight_grams = Column(Integer)
    shipping_label_url = Column(String(1000))
    tracking_url = Column(String(1000))
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ════════════════════════════════════════════════
# SECTION K: REVIEWS & WISHLIST
# ════════════════════════════════════════════════


class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    order_item_id = Column(UUID(as_uuid=True), ForeignKey("order_items.id"))
    rating = Column(SmallInteger, nullable=False)
    title = Column(String(200))
    comment = Column(Text)
    fit_feedback = Column(String(20))
    is_verified = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")

    __table_args__ = (
        UniqueConstraint("user_id", "product_id"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
    )



# SECTION L: PAYMENT SAFETY & ADMIN AUDIT
# ════════════════════════════════════════════════


class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    gateway = Column(String(20), nullable=False)
    gateway_event_id = Column(String(200), unique=True, nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    payload_hash = Column(String(64))
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow)


class AdminActivityLog(Base):
    __tablename__ = "admin_activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    target_type = Column(String(30), nullable=False)
    target_id = Column(UUID(as_uuid=True))
    details = Column(JSONB)
    ip_address = Column(INET)
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    role = Column(String(20), nullable=False)
    resource = Column(String(30), nullable=False)
    action = Column(String(20), nullable=False)

    __table_args__ = (
        UniqueConstraint("role", "resource", "action"),
    )


# ════════════════════════════════════════════════
# SECTION M: STORE SETTINGS (Phase 13H)
# ════════════════════════════════════════════════


class StoreSetting(Base):
    __tablename__ = "store_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    setting_key = Column(String(50), unique=True, nullable=False)
    setting_value = Column(String(500))
    description = Column(String(500))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class StoreSettingsAudit(Base):
    __tablename__ = "store_settings_audit"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    setting_key = Column(String(50), nullable=False, index=True)
    old_value = Column(String(500))
    new_value = Column(String(500))
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    changed_at = Column(DateTime(timezone=True), default=utcnow, index=True)
