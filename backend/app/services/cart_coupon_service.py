"""
Cart & Coupon Service — Phase 6.
Server-side cart, guest merge, stock check, coupon validation.
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Cart,
    CartItem,
    Coupon,
    CouponUsage,
    Product,
    ProductImage,
    ProductVariant,
)


class CartCouponError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ══════════════════════════════════════════
# CART SERVICE
# ══════════════════════════════════════════

class CartService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_or_create_cart(self, user_id) -> Cart:
        result = await self.db.execute(
            select(Cart).where(Cart.user_id == user_id)
        )
        cart = result.scalar_one_or_none()
        if not cart:
            cart = Cart(user_id=user_id)
            self.db.add(cart)
            await self.db.flush()
        return cart

    async def get_cart(self, user_id) -> dict:
        """Get full cart with enriched item details."""
        cart = await self._get_or_create_cart(user_id)

        result = await self.db.execute(
            select(CartItem).where(CartItem.cart_id == cart.id)
        )
        items = list(result.scalars().all())

        enriched = []
        subtotal = Decimal("0")

        for item in items:
            # Get variant + product
            v_result = await self.db.execute(
                select(ProductVariant, Product)
                .join(Product, ProductVariant.product_id == Product.id)
                .where(ProductVariant.id == item.product_variant_id)
            )
            row = v_result.one_or_none()
            if not row:
                continue
            variant, product = row

            # Skip deleted/inactive
            if variant.deleted_at or product.deleted_at or not product.is_active:
                continue

            # Get primary image
            img_result = await self.db.execute(
                select(ProductImage)
                .where(
                    ProductImage.product_id == product.id,
                    ProductImage.is_primary == True,
                )
                .limit(1)
            )
            img = img_result.scalar_one_or_none()

            unit_price = variant.price_override or product.sale_price or product.base_price
            line_total = unit_price * item.quantity
            subtotal += line_total
            in_stock = variant.stock_quantity >= item.quantity

            enriched.append({
                "id": item.id,
                "variant_id": item.product_variant_id,
                "quantity": item.quantity,
                "product_id": product.id,
                "product_title": product.title,
                "product_slug": product.slug,
                "brand": product.brand,
                "size": variant.size,
                "color": variant.color,
                "color_hex": variant.color_hex,
                "sku": variant.sku,
                "unit_price": unit_price,
                "sale_price": product.sale_price,
                "line_total": line_total,
                "stock_quantity": variant.stock_quantity,
                "in_stock": in_stock,
                "image_url": (
                    img.thumbnail_url or img.medium_url or img.original_url
                ) if img else None,
            })

        return {
            "items": enriched,
            "item_count": sum(i["quantity"] for i in enriched),
            "subtotal": subtotal,
            "currency": "INR",
        }

    async def add_item(self, user_id, variant_id, quantity: int) -> dict:
        """Add item to cart. Merges if same variant exists."""
        # Verify variant exists and in stock
        v_result = await self.db.execute(
            select(ProductVariant).where(
                ProductVariant.id == variant_id,
                ProductVariant.deleted_at.is_(None),
                ProductVariant.is_active == True,
            )
        )
        variant = v_result.scalar_one_or_none()
        if not variant:
            raise CartCouponError("Product variant not found.", 404)
        if variant.stock_quantity < quantity:
            raise CartCouponError(
                f"Only {variant.stock_quantity} items available.", 400
            )

        cart = await self._get_or_create_cart(user_id)

        # Check if variant already in cart
        existing = await self.db.execute(
            select(CartItem).where(
                CartItem.cart_id == cart.id,
                CartItem.product_variant_id == variant_id,
            )
        )
        cart_item = existing.scalar_one_or_none()

        if cart_item:
            new_qty = cart_item.quantity + quantity
            if new_qty > variant.stock_quantity:
                raise CartCouponError(
                    f"Only {variant.stock_quantity} items available. You have {cart_item.quantity} in cart.", 400
                )
            cart_item.quantity = new_qty
        else:
            cart_item = CartItem(
                cart_id=cart.id,
                product_variant_id=variant_id,
                quantity=quantity,
            )
            self.db.add(cart_item)

        cart.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return await self.get_cart(user_id)

    async def update_item(self, user_id, variant_id, quantity: int) -> dict:
        """Update cart item quantity."""
        cart = await self._get_or_create_cart(user_id)

        result = await self.db.execute(
            select(CartItem).where(
                CartItem.cart_id == cart.id,
                CartItem.product_variant_id == variant_id,
            )
        )
        cart_item = result.scalar_one_or_none()
        if not cart_item:
            raise CartCouponError("Item not in cart.", 404)

        # Stock check
        v_result = await self.db.execute(
            select(ProductVariant).where(ProductVariant.id == variant_id)
        )
        variant = v_result.scalar_one_or_none()
        if variant and quantity > variant.stock_quantity:
            raise CartCouponError(
                f"Only {variant.stock_quantity} items available.", 400
            )

        cart_item.quantity = quantity
        cart.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return await self.get_cart(user_id)

    async def remove_item(self, user_id, variant_id) -> dict:
        """Remove item from cart."""
        cart = await self._get_or_create_cart(user_id)

        result = await self.db.execute(
            select(CartItem).where(
                CartItem.cart_id == cart.id,
                CartItem.product_variant_id == variant_id,
            )
        )
        cart_item = result.scalar_one_or_none()
        if not cart_item:
            raise CartCouponError("Item not in cart.", 404)

        await self.db.delete(cart_item)
        cart.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return await self.get_cart(user_id)

    async def clear_cart(self, user_id) -> None:
        """Remove all items from cart."""
        cart = await self._get_or_create_cart(user_id)
        result = await self.db.execute(
            select(CartItem).where(CartItem.cart_id == cart.id)
        )
        for item in result.scalars().all():
            await self.db.delete(item)

    async def merge_guest_cart(self, user_id, guest_items: list) -> dict:
        """
        Merge guest localStorage cart into server-side cart on login.
        guest_items = [{variant_id, quantity}, ...]
        """
        for item in guest_items:
            try:
                await self.add_item(user_id, item.variant_id, item.quantity)
            except CartCouponError:
                # Skip items that fail (out of stock, etc.)
                continue
        return await self.get_cart(user_id)

    async def get_item_count(self, user_id) -> int:
        """Get total items in cart (for badge)."""
        cart_result = await self.db.execute(
            select(Cart).where(Cart.user_id == user_id)
        )
        cart = cart_result.scalar_one_or_none()
        if not cart:
            return 0

        result = await self.db.execute(
            select(func.sum(CartItem.quantity)).where(CartItem.cart_id == cart.id)
        )
        return result.scalar() or 0


# ══════════════════════════════════════════
# COUPON SERVICE
# ══════════════════════════════════════════

class CouponService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Admin CRUD ──

    async def list_coupons(self, active_only: bool = False) -> list:
        query = select(Coupon).where(Coupon.deleted_at.is_(None))
        if active_only:
            query = query.where(Coupon.is_active == True)
        query = query.order_by(Coupon.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_coupon(self, data) -> Coupon:
        existing = await self.db.execute(
            select(Coupon).where(Coupon.code == data.code.upper())
        )
        if existing.scalar_one_or_none():
            raise CartCouponError(f"Coupon code '{data.code}' already exists.", 409)

        coupon = Coupon(
            code=data.code.upper(),
            description=data.description,
            type=data.type,
            value=data.value,
            min_order_value=data.min_order_value,
            max_discount=data.max_discount,
            usage_limit=data.usage_limit,
            per_user_limit=data.per_user_limit,
            applicable_categories=data.applicable_categories,
            starts_at=data.starts_at,
            expires_at=data.expires_at,
            is_active=data.is_active,
        )
        self.db.add(coupon)
        await self.db.flush()
        return coupon

    async def update_coupon(self, coupon_id, data) -> Coupon:
        result = await self.db.execute(
            select(Coupon).where(Coupon.id == coupon_id, Coupon.deleted_at.is_(None))
        )
        coupon = result.scalar_one_or_none()
        if not coupon:
            raise CartCouponError("Coupon not found.", 404)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(coupon, key, value)
        await self.db.flush()
        return coupon

    async def delete_coupon(self, coupon_id) -> None:
        result = await self.db.execute(
            select(Coupon).where(Coupon.id == coupon_id, Coupon.deleted_at.is_(None))
        )
        coupon = result.scalar_one_or_none()
        if not coupon:
            raise CartCouponError("Coupon not found.", 404)
        coupon.soft_delete()

    # ── Apply coupon (customer-facing) ──

    async def apply_coupon(self, user_id, code: str, cart_subtotal: Decimal) -> dict:
        """
        Validate and calculate coupon discount.
        Returns: {valid, message, coupon_id, discount_amount, ...}
        """
        now = datetime.now(timezone.utc)

        result = await self.db.execute(
            select(Coupon).where(
                Coupon.code == code.upper(),
                Coupon.deleted_at.is_(None),
            )
        )
        coupon = result.scalar_one_or_none()

        if not coupon:
            return {"valid": False, "message": "Invalid coupon code."}

        if not coupon.is_active:
            return {"valid": False, "message": "Coupon is not active."}

        if now < coupon.starts_at:
            return {"valid": False, "message": "Coupon is not yet valid."}

        if now > coupon.expires_at:
            return {"valid": False, "message": "Coupon has expired."}

        if coupon.min_order_value and cart_subtotal < coupon.min_order_value:
            return {
                "valid": False,
                "message": f"Minimum order value is ₹{coupon.min_order_value}.",
            }

        # Check global usage limit
        if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
            return {"valid": False, "message": "Coupon usage limit reached."}

        # Check per-user usage limit
        user_usage_result = await self.db.execute(
            select(func.count(CouponUsage.id)).where(
                CouponUsage.coupon_id == coupon.id,
                CouponUsage.user_id == user_id,
            )
        )
        user_usage = user_usage_result.scalar()
        if user_usage >= coupon.per_user_limit:
            return {"valid": False, "message": "You have already used this coupon."}

        # Calculate discount
        if coupon.type == "flat":
            discount = coupon.value
        else:  # percent
            discount = cart_subtotal * coupon.value / Decimal("100")

        # Apply max discount cap
        if coupon.max_discount and discount > coupon.max_discount:
            discount = coupon.max_discount

        # Discount cannot exceed subtotal
        if discount > cart_subtotal:
            discount = cart_subtotal

        return {
            "valid": True,
            "message": f"Coupon applied! You save ₹{discount}.",
            "coupon_id": coupon.id,
            "discount_amount": discount,
            "coupon_code": coupon.code,
            "coupon_type": coupon.type,
        }

    async def record_usage(self, coupon_id, user_id, order_id) -> None:
        """Record coupon usage after successful order."""
        usage = CouponUsage(
            coupon_id=coupon_id,
            user_id=user_id,
            order_id=order_id,
        )
        self.db.add(usage)

        # Increment used_count
        result = await self.db.execute(
            select(Coupon).where(Coupon.id == coupon_id)
        )
        coupon = result.scalar_one_or_none()
        if coupon:
            coupon.used_count = (coupon.used_count or 0) + 1
        await self.db.flush()
