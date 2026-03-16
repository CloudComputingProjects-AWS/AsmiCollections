"""
Order Service â€” Phase 7.
Checkout, GST tax engine, stock reservation, order state machine.
"""
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    Cart, CartItem, Coupon, CouponUsage, InventoryReservation,
    Order, OrderItem, OrderStatusHistory, Product, ProductImage,
    ProductVariant, UserAddress,
)
from app.services.store_settings_service import StoreSettingsService
from app.services.cart_coupon_service import CouponService

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ORDER STATE MACHINE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

ORDER_TRANSITIONS = {
    "placed":           ["confirmed", "cancelled"],
    "confirmed":        ["processing", "delivered", "cancelled"],
    "processing":       ["shipped", "cancelled"],
    "shipped":          ["out_for_delivery"],
    "out_for_delivery": ["delivered"],
    "delivered":        ["return_requested"],
    "return_requested": ["return_approved", "return_rejected"],
    "return_approved":  ["return_received"],
    "return_received":  ["refunded"],
    "cancelled":        [],
    "refunded":         [],
    "return_rejected":  [],
}

def can_transition(current: str, new: str) -> bool:
    return new in ORDER_TRANSITIONS.get(current, [])


class OrderServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # TAX ENGINE
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    def calculate_tax(
        self, base_amount: Decimal, gst_rate: Decimal,
        seller_state: str, buyer_state: str, buyer_country: str = "India"
    ) -> dict:
        """
        GST tax calculation:
        - Intra-state (same state): CGST + SGST (each = gst_rate/2)
        - Inter-state (different state, India): IGST (= gst_rate)
        - Export: zero-rated
        """
        if buyer_country != "India":
            return {"cgst": Decimal("0"), "sgst": Decimal("0"), "igst": Decimal("0"),
                    "total_tax": Decimal("0"), "supply_type": "export"}

        # GST-inclusive back-calculation: base = inclusive / (1 + rate/100), tax = inclusive - base
        base_exclusive = (base_amount / (1 + gst_rate / Decimal("100"))).quantize(Decimal("0.01"))
        total_tax = (base_amount - base_exclusive).quantize(Decimal("0.01"))

        if seller_state.lower() == buyer_state.lower():
            half = (total_tax / 2).quantize(Decimal("0.01"))
            return {"cgst": half, "sgst": total_tax - half, "igst": Decimal("0"),
                    "total_tax": total_tax, "supply_type": "intra_state"}
        else:
            return {"cgst": Decimal("0"), "sgst": Decimal("0"), "igst": total_tax,
                    "total_tax": total_tax, "supply_type": "inter_state"}

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # ORDER SUMMARY (pre-checkout preview)
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    async def get_order_summary(self, user_id, shipping_address_id, coupon_code: str | None = None) -> dict:
        """Build order summary with tax breakdown before placing order."""
        address = await self._get_address(user_id, shipping_address_id)
        cart_items = await self._get_cart_items(user_id)
        if not cart_items:
            raise OrderServiceError("Cart is empty.", 400)

        seller_state = await self._get_seller_state()
        items_detail, subtotal, tax_data = await self._calc_items_tax(cart_items, seller_state, address.state, address.country)

        discount = Decimal("0")
        if coupon_code:
            discount = await self._calc_discount(user_id, coupon_code, subtotal)

        # Dynamic shipping fee from store_settings
        settings_svc = StoreSettingsService(self.db)
        ship_config = await settings_svc.get_shipping_config()
        threshold = Decimal(str(ship_config.get("free_shipping_threshold", 0)))
        base_fee = Decimal(str(ship_config.get("shipping_fee", 0)))
        shipping_fee = Decimal("0") if subtotal >= threshold else base_fee
        grand_total = subtotal + shipping_fee - discount  # Tax already inside subtotal (GST-inclusive)

        return {
            "items": items_detail,
            "subtotal": subtotal,
            "tax_breakdown": tax_data["breakdowns"],
            "total_tax": tax_data["total_tax"],
            "shipping_fee": shipping_fee,
            "discount_amount": discount,
            "grand_total": grand_total,
            "currency": "INR",
        }

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # CHECKOUT â€” PLACE ORDER
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    async def place_order(self, user_id, data) -> Order:
        """
        Full checkout:
        1. Validate address & cart
        2. Lock variants (SELECT FOR UPDATE)
        3. Create inventory reservations
        4. Calculate tax
        5. Create order + items with snapshots
        6. Record status history
        7. Clear cart
        """
        address = await self._get_address(user_id, data.shipping_address_id)
        billing_address = address
        if data.billing_address_id and data.billing_address_id != data.shipping_address_id:
            billing_address = await self._get_address(user_id, data.billing_address_id)

        cart_items = await self._get_cart_items(user_id)
        if not cart_items:
            raise OrderServiceError("Cart is empty.", 400)

        seller_state = await self._get_seller_state()

        # Lock variants and check stock
        for ci, variant, product in cart_items:
            locked = await self.db.execute(
                select(ProductVariant)
                .where(ProductVariant.id == variant.id)
                .with_for_update()
            )
            v = locked.scalar_one()
            if v.stock_quantity < ci.quantity:
                raise OrderServiceError(
                    f"'{product.title}' ({variant.size}/{variant.color}) â€” only {v.stock_quantity} left.", 400
                )

        # Create reservations
        for ci, variant, product in cart_items:
            reservation = InventoryReservation(
                variant_id=variant.id, user_id=user_id,
                reserved_qty=ci.quantity, status="held",
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
            )
            self.db.add(reservation)

        # Calculate tax
        items_detail, subtotal, tax_data = await self._calc_items_tax(cart_items, seller_state, address.state, address.country)

        # Coupon discount
        discount = Decimal("0")
        coupon_id = None
        if data.coupon_code:
            discount = await self._calc_discount(user_id, data.coupon_code, subtotal)
            coupon_result = await self.db.execute(
                select(Coupon).where(Coupon.code == data.coupon_code.upper())
            )
            coupon = coupon_result.scalar_one_or_none()
            if coupon:
                coupon_id = coupon.id

        # Dynamic shipping fee from store_settings (same as get_order_summary)
        settings_svc = StoreSettingsService(self.db)
        ship_config = await settings_svc.get_shipping_config()
        threshold = Decimal(str(ship_config.get("free_shipping_threshold", 0)))
        base_fee = Decimal(str(ship_config.get("shipping_fee", 0)))
        shipping_fee = Decimal("0") if subtotal >= threshold else base_fee
        grand_total = subtotal + shipping_fee - discount  # Tax already inside subtotal (GST-inclusive)

        # Generate order number
        order_number = f"ORD-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # Create order
        order = Order(
            user_id=user_id,
            order_number=order_number,
            subtotal=subtotal,
            tax_amount=tax_data["total_tax"],
            cgst_amount=tax_data["total_cgst"],
            sgst_amount=tax_data["total_sgst"],
            igst_amount=tax_data["total_igst"],
            shipping_fee=shipping_fee,
            discount_amount=discount,
            grand_total=grand_total,
            currency=data.currency,
            shipping_address_id=data.shipping_address_id,
            billing_address_id=data.billing_address_id or data.shipping_address_id,
            # customer_gst_number removed (B2C only)
            shipping_name=address.full_name,
            shipping_address_text=f"{address.address_line_1}, {address.address_line_2 or ''}".strip(", "),
            shipping_city=address.city,
            shipping_state=address.state,
            shipping_postal_code=address.postal_code,
            shipping_country=address.country,
            payment_method=data.payment_method,
            payment_gateway=data.payment_gateway,
            payment_status="pending",
            coupon_id=coupon_id,
            coupon_code_snapshot=data.coupon_code.upper() if data.coupon_code else None,
            order_status="placed",
            notes=data.notes,
        )
        self.db.add(order)
        await self.db.flush()

        # Create order items with snapshots
        for ci, variant, product in cart_items:
            img_result = await self.db.execute(
                select(ProductImage).where(
                    ProductImage.product_id == product.id, ProductImage.is_primary == True
                ).limit(1)
            )
            img = img_result.scalar_one_or_none()

            unit_price = variant.price_override or product.sale_price or product.base_price
            tax_info = self.calculate_tax(unit_price * ci.quantity, product.gst_rate or Decimal("0"), seller_state, address.state, address.country)

            oi = OrderItem(
                order_id=order.id,
                product_variant_id=variant.id,
                product_title_snapshot=product.title,
                brand_snapshot=product.brand,
                size_snapshot=variant.size,
                color_snapshot=variant.color,
                sku_snapshot=variant.sku,
                image_url_snapshot=(img.thumbnail_url or img.original_url) if img else None,
                hsn_code_snapshot=product.hsn_code,
                attributes_snapshot=product.attributes,
                quantity=ci.quantity,
                unit_price=unit_price,
                tax_rate=product.gst_rate or Decimal("0"),
                tax_amount=tax_info["total_tax"],
                line_total=unit_price * ci.quantity,  # GST-inclusive, tax already inside
            )
            self.db.add(oi)

        # Record initial status history
        history = OrderStatusHistory(
            order_id=order.id, from_status=None,
            to_status="placed", change_reason="Order placed by customer",
        )
        self.db.add(history)

        # Record coupon usage
        if coupon_id:
            usage = CouponUsage(coupon_id=coupon_id, user_id=user_id, order_id=order.id)
            self.db.add(usage)
            await self.db.execute(
                update(Coupon).where(Coupon.id == coupon_id).values(used_count=Coupon.used_count + 1)
            )

        await self._clear_cart(user_id)

        await self.db.flush()
        return order

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # STATE MACHINE TRANSITION
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    async def transition_order(self, order_id, new_status: str, changed_by=None, reason: str = None) -> Order:
        result = await self.db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise OrderServiceError("Order not found.", 404)

        if not can_transition(order.order_status, new_status):
            raise OrderServiceError(
                f"Illegal transition: {order.order_status} â†’ {new_status}", 400
            )

        old_status = order.order_status
        order.order_status = new_status
        order.updated_at = datetime.now(timezone.utc)

        # Side effects
        if new_status == "confirmed":
            await self._adjust_stock(order_id, -1)
            await self._release_reservations(order_id)
        elif new_status == "cancelled":
            if old_status in ("confirmed", "processing"):
                await self._adjust_stock(order_id, +1)
            await self._release_reservations(order_id)
            order.payment_status = "refund_pending" if order.payment_status == "paid" else "cancelled"

        # Record history
        history = OrderStatusHistory(
            order_id=order.id, from_status=old_status,
            to_status=new_status, changed_by=changed_by, change_reason=reason,
        )
        self.db.add(history)
        await self.db.flush()
        return order

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # ORDER QUERIES
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    async def get_order(self, order_id, user_id=None) -> Order:
        query = select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        if user_id:
            query = query.where(Order.user_id == user_id)
        result = await self.db.execute(query)
        order = result.scalar_one_or_none()
        if not order:
            raise OrderServiceError("Order not found.", 404)
        return order

    async def list_user_orders(self, user_id, page=1, page_size=10) -> tuple[list, int]:
        query = select(Order).where(Order.user_id == user_id).options(selectinload(Order.items))
        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_q)).scalar()
        query = query.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().unique().all()), total

    async def get_order_timeline(self, order_id, user_id=None) -> dict:
        order = await self.get_order(order_id, user_id)
        result = await self.db.execute(
            select(OrderStatusHistory).where(OrderStatusHistory.order_id == order_id)
            .order_by(OrderStatusHistory.created_at.asc())
        )
        history = list(result.scalars().all())
        return {
            "order_id": order.id, "order_number": order.order_number,
            "current_status": order.order_status, "history": history,
        }

    async def admin_list_orders(self, status=None, page=1, page_size=20) -> tuple[list, int]:
        query = select(Order).options(selectinload(Order.items))
        if status:
            query = query.where(Order.order_status == status)
        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_q)).scalar()
        query = query.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().unique().all()), total

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # HELPERS
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    async def _get_seller_state(self) -> str:
        """DRY: fetch seller state from store settings.
        Replaces duplicated StoreSettingsService calls in get_order_summary and place_order.
        """
        return await StoreSettingsService.get_seller_state_static(self.db)

    async def _clear_cart(self, user_id):
        """SRP: cart-clearing logic extracted from place_order."""
        cart_result = await self.db.execute(select(Cart).where(Cart.user_id == user_id))
        cart = cart_result.scalar_one_or_none()
        if cart:
            await self.db.execute(
                CartItem.__table__.delete().where(CartItem.cart_id == cart.id)
            )

    async def _get_address(self, user_id, address_id) -> UserAddress:
        result = await self.db.execute(
            select(UserAddress).where(
                UserAddress.id == address_id, UserAddress.user_id == user_id,
                UserAddress.deleted_at.is_(None),
            )
        )
        addr = result.scalar_one_or_none()
        if not addr:
            raise OrderServiceError("Address not found.", 404)
        return addr

    async def _get_cart_items(self, user_id) -> list:
        cart_result = await self.db.execute(select(Cart).where(Cart.user_id == user_id))
        cart = cart_result.scalar_one_or_none()
        if not cart:
            return []
        items_result = await self.db.execute(select(CartItem).where(CartItem.cart_id == cart.id))
        cart_items = list(items_result.scalars().all())
        result = []
        for ci in cart_items:
            v_result = await self.db.execute(
                select(ProductVariant, Product).join(Product, ProductVariant.product_id == Product.id)
                .where(ProductVariant.id == ci.product_variant_id)
            )
            row = v_result.one_or_none()
            if row:
                result.append((ci, row[0], row[1]))
        return result

    async def _calc_items_tax(self, cart_items, seller_state, buyer_state, buyer_country):
        items_detail = []
        subtotal = Decimal("0")
        total_cgst = total_sgst = total_igst = total_tax = Decimal("0")
        breakdowns = []
        for ci, variant, product in cart_items:
            unit_price = variant.price_override or product.sale_price or product.base_price
            line_subtotal = unit_price * ci.quantity
            subtotal += line_subtotal
            tax = self.calculate_tax(line_subtotal, product.gst_rate or Decimal("0"), seller_state, buyer_state, buyer_country)
            total_cgst += tax["cgst"]
            total_sgst += tax["sgst"]
            total_igst += tax["igst"]
            total_tax += tax["total_tax"]
            breakdowns.append({"hsn_code": product.hsn_code, "taxable_amount": line_subtotal,
                "cgst_rate": (product.gst_rate or Decimal("0")) / 2 if tax["cgst"] > 0 else Decimal("0"),
                "cgst_amount": tax["cgst"], "sgst_rate": (product.gst_rate or Decimal("0")) / 2 if tax["sgst"] > 0 else Decimal("0"),
                "sgst_amount": tax["sgst"], "igst_rate": product.gst_rate or Decimal("0") if tax["igst"] > 0 else Decimal("0"),
                "igst_amount": tax["igst"], "total_tax": tax["total_tax"]})
            items_detail.append({
                "title": product.title,
                "sku": variant.sku,
                "size": variant.size,
                "color": variant.color,
                "qty": ci.quantity,
                "unit_price": str(unit_price),
                "line_total": str(line_subtotal),
            })
        return items_detail, subtotal, {"total_tax": total_tax, "total_cgst": total_cgst, "total_sgst": total_sgst, "total_igst": total_igst, "breakdowns": breakdowns}

    async def _calc_discount(self, user_id, coupon_code, subtotal) -> Decimal:
        svc = CouponService(self.db)
        result = await svc.apply_coupon(user_id, coupon_code, subtotal)
        return result.get("discount_amount", Decimal("0")) if result.get("valid") else Decimal("0")

    async def _adjust_stock(self, order_id, delta_sign: int):
        """Adjust stock for all items in an order.
        DRY: replaces _deduct_stock (delta_sign=-1) and _restore_stock (delta_sign=+1).
        """
        result = await self.db.execute(select(OrderItem).where(OrderItem.order_id == order_id))
        for oi in result.scalars().all():
            if oi.product_variant_id:
                await self.db.execute(
                    update(ProductVariant).where(ProductVariant.id == oi.product_variant_id)
                    .values(stock_quantity=ProductVariant.stock_quantity + (oi.quantity * delta_sign))
                )

    async def _release_reservations(self, order_id):
        await self.db.execute(
            update(InventoryReservation).where(InventoryReservation.order_id == order_id)
            .values(status="released")
        )
