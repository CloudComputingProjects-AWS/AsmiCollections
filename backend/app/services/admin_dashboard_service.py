"""
Admin Dashboard & Reports Service â€” Aggregation and analytics layer.
Phase 11 â€” V2.5 Blueprint

Provides:
  - Dashboard KPIs (revenue, orders, alerts)
  - Revenue trend charts
  - Sales reports (by date/category/product)
  - Coupon performance
  - Low stock alerts
  - Top products
  - Audit log querying
  - User management
  - CSV/PDF export
"""

import csv
import io
import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, case, cast, func, or_, select, update, Date, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    AdminActivityLog,
    Coupon,
    CouponUsage,
    CreditNote,
    Invoice,
    Order,
    OrderItem,
    Product,
    ProductVariant,
    Refund,
    Return,
    Review,
    User,
)

logger = logging.getLogger(__name__)


class DashboardServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AdminDashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Dashboard KPIs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def get_dashboard_stats(self) -> dict:
        """Get top-level KPI metrics for admin dashboard."""

        # Revenue & order counts
        revenue_result = await self.db.execute(
            select(
                func.coalesce(func.sum(Order.grand_total), 0).label("total_revenue"),
                func.count(Order.id).label("total_orders"),
            ).where(
                Order.order_status.notin_(["cancelled"]),
                Order.payment_status == "paid",
            )
        )
        rev_row = revenue_result.one()

        total_revenue = Decimal(str(rev_row.total_revenue))
        total_orders = rev_row.total_orders
        avg_order_value = (
            (total_revenue / total_orders).quantize(Decimal("0.01"))
            if total_orders > 0
            else Decimal("0")
        )

        # Order status counts
        status_result = await self.db.execute(
            select(Order.order_status, func.count(Order.id)).group_by(Order.order_status)
        )
        status_counts = {row[0]: row[1] for row in status_result.all()}

        # Customer count
        cust_result = await self.db.execute(
            select(func.count(User.id)).where(
                User.role == "customer", User.is_active == True, User.deleted_at.is_(None)
            )
        )
        total_customers = cust_result.scalar() or 0

        # Low stock variants (stock < 10)
        low_stock_result = await self.db.execute(
            select(func.count(ProductVariant.id)).where(
                ProductVariant.stock_quantity < 10,
                ProductVariant.is_active == True,
                ProductVariant.deleted_at.is_(None),
            )
        )
        low_stock_variants = low_stock_result.scalar() or 0

        # Pending reviews
        pending_reviews_result = await self.db.execute(
            select(func.count(Review.id)).where(Review.is_approved == False)
        )
        pending_reviews = pending_reviews_result.scalar() or 0

        # Failed payments
        failed_payments_result = await self.db.execute(
            select(func.count(Order.id)).where(Order.payment_status == "failed")
        )
        failed_payments = failed_payments_result.scalar() or 0

        # Pending returns
        pending_returns_result = await self.db.execute(
            select(func.count(Return.id)).where(Return.status == "requested")
        )
        pending_returns = pending_returns_result.scalar() or 0

        return {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "avg_order_value": avg_order_value,
            "total_customers": total_customers,
            "pending_orders": status_counts.get("placed", 0),
            "processing_orders": status_counts.get("processing", 0),
            "shipped_orders": status_counts.get("shipped", 0),
            "delivered_orders": status_counts.get("delivered", 0),
            "cancelled_orders": status_counts.get("cancelled", 0),
            "return_requested_count": status_counts.get("return_requested", 0),
            "pending_returns": pending_returns,
            "failed_payments": failed_payments,
            "low_stock_variants": low_stock_variants,
            "pending_reviews": pending_reviews,
        }

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Revenue Chart â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def get_revenue_trend(self, period: str = "30d") -> list[dict]:
        """Get revenue trend data for chart."""
        days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}.get(period, 30)
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        result = await self.db.execute(
            select(
                cast(Order.created_at, Date).label("order_date"),
                func.coalesce(func.sum(Order.grand_total), 0).label("revenue"),
                func.count(Order.id).label("order_count"),
            )
            .where(
                Order.created_at >= start_date,
                Order.order_status.notin_(["cancelled"]),
                Order.payment_status == "paid",
            )
            .group_by(cast(Order.created_at, Date))
            .order_by(cast(Order.created_at, Date))
        )

        return [
            {
                "date": str(row.order_date),
                "revenue": Decimal(str(row.revenue)),
                "order_count": row.order_count,
            }
            for row in result.all()
        ]

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Top Products â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def get_top_products(self, limit: int = 10) -> list[dict]:
        """Get top selling products by units sold."""
        result = await self.db.execute(
            select(
                OrderItem.product_variant_id,
                func.max(OrderItem.product_title_snapshot).label("title"),
                func.sum(OrderItem.quantity).label("total_sold"),
                func.sum(OrderItem.line_total).label("total_revenue"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                Order.order_status.notin_(["cancelled"]),
                Order.payment_status == "paid",
            )
            .group_by(OrderItem.product_variant_id)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(limit)
        )

        return [
            {
                "product_id": row.product_variant_id,
                "title": row.title,
                "total_sold": row.total_sold,
                "total_revenue": Decimal(str(row.total_revenue)),
            }
            for row in result.all()
        ]

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Low Stock Alerts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def get_low_stock_variants(
        self, threshold: int = 10, page: int = 1, page_size: int = 50
    ) -> tuple[list[dict], int]:
        """Get variants with stock below threshold."""
        base_condition = and_(
            ProductVariant.stock_quantity < threshold,
            ProductVariant.is_active == True,
            ProductVariant.deleted_at.is_(None),
        )

        count_result = await self.db.execute(
            select(func.count(ProductVariant.id)).where(base_condition)
        )
        total = count_result.scalar() or 0

        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(
                ProductVariant.id,
                ProductVariant.sku,
                ProductVariant.size,
                ProductVariant.color,
                ProductVariant.stock_quantity,
                Product.title,
            )
            .join(Product, Product.id == ProductVariant.product_id)
            .where(base_condition)
            .order_by(ProductVariant.stock_quantity.asc())
            .offset(offset)
            .limit(page_size)
        )

        variants = [
            {
                "variant_id": row.id,
                "product_title": row.title,
                "sku": row.sku,
                "size": row.size,
                "color": row.color,
                "stock_quantity": row.stock_quantity,
            }
            for row in result.all()
        ]
        return variants, total

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Sales Report â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def get_sales_report(
        self,
        from_date: date | None = None,
        to_date: date | None = None,
        category_id: UUID | None = None,
        product_id: UUID | None = None,
        group_by: str = "day",
    ) -> dict:
        """Generate sales report grouped by time period."""
        if not from_date:
            from_date = date.today() - timedelta(days=30)
        if not to_date:
            to_date = date.today()

        # Date grouping expression
        if group_by == "month":
            date_expr = func.to_char(Order.created_at, "YYYY-MM").label("period")
        elif group_by == "week":
            date_expr = func.to_char(Order.created_at, "IYYY-IW").label("period")
        else:
            date_expr = cast(Order.created_at, Date).label("period")

        query = (
            select(
                date_expr,
                func.count(func.distinct(Order.id)).label("order_count"),
                func.coalesce(func.sum(Order.grand_total), 0).label("total_revenue"),
                func.coalesce(func.sum(Order.tax_amount), 0).label("total_tax"),
                func.coalesce(func.sum(Order.discount_amount), 0).label("total_discount"),
                func.coalesce(func.sum(OrderItem.quantity), 0).label("units_sold"),
            )
            .join(OrderItem, OrderItem.order_id == Order.id)
            .where(
                Order.created_at >= datetime.combine(from_date, datetime.min.time(), tzinfo=timezone.utc),
                Order.created_at <= datetime.combine(to_date, datetime.max.time(), tzinfo=timezone.utc),
                Order.order_status.notin_(["cancelled"]),
                Order.payment_status == "paid",
            )
        )

        if category_id:
            query = query.join(
                ProductVariant,
                ProductVariant.id == OrderItem.product_variant_id
            ).join(
                Product,
                Product.id == ProductVariant.product_id
            ).where(Product.category_id == category_id)

        query = query.group_by("period").order_by("period")

        result = await self.db.execute(query)
        rows = []
        total_revenue = Decimal("0")
        total_orders = 0
        total_units = 0

        for row in result.all():
            revenue = Decimal(str(row.total_revenue))
            count = row.order_count
            rows.append({
                "period": str(row.period),
                "order_count": count,
                "total_revenue": revenue,
                "total_tax": Decimal(str(row.total_tax)),
                "total_discount": Decimal(str(row.total_discount)),
                "avg_order_value": (revenue / count).quantize(Decimal("0.01")) if count else Decimal("0"),
                "units_sold": row.units_sold,
            })
            total_revenue += revenue
            total_orders += count
            total_units += row.units_sold

        return {
            "rows": rows,
            "summary": {
                "total_revenue": total_revenue,
                "total_orders": total_orders,
                "total_units": total_units,
                "avg_order_value": (
                    (total_revenue / total_orders).quantize(Decimal("0.01"))
                    if total_orders else Decimal("0")
                ),
            },
            "from_date": str(from_date),
            "to_date": str(to_date),
        }

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Coupon Performance â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def get_coupon_performance(self) -> list[dict]:
        """Get coupon usage statistics."""
        result = await self.db.execute(
            select(
                Coupon.id,
                Coupon.code,
                Coupon.type,
                Coupon.value,
                Coupon.is_active,
                func.count(CouponUsage.id).label("times_used"),
                func.coalesce(func.sum(Order.discount_amount), 0).label("total_discount_given"),
                func.coalesce(func.sum(Order.grand_total), 0).label("total_order_value"),
            )
            .outerjoin(CouponUsage, CouponUsage.coupon_id == Coupon.id)
            .outerjoin(Order, Order.coupon_id == Coupon.id)
            .where(Coupon.deleted_at.is_(None))
            .group_by(Coupon.id, Coupon.code, Coupon.type, Coupon.value, Coupon.is_active)
            .order_by(func.count(CouponUsage.id).desc())
        )

        return [
            {
                "coupon_id": row.id,
                "code": row.code,
                "type": row.type,
                "value": Decimal(str(row.value)),
                "times_used": row.times_used,
                "total_discount_given": Decimal(str(row.total_discount_given)),
                "total_order_value": Decimal(str(row.total_order_value)),
                "is_active": row.is_active,
            }
            for row in result.all()
        ]

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Audit Logs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def get_audit_logs(
        self,
        page: int = 1,
        page_size: int = 50,
        admin_id: UUID | None = None,
        action: str | None = None,
        target_type: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        search: str | None = None,
    ) -> tuple[list[dict], int]:
        """Query audit logs with filters."""
        query = (
            select(
                AdminActivityLog,
                User.email.label("admin_email"),
                User.first_name.label("admin_first_name"),
                User.last_name.label("admin_last_name"),
            )
            .join(User, User.id == AdminActivityLog.admin_id)
        )
        count_query = select(func.count(AdminActivityLog.id))

        conditions = []
        if admin_id:
            conditions.append(AdminActivityLog.admin_id == admin_id)
        if action:
            conditions.append(AdminActivityLog.action == action)
        if target_type:
            conditions.append(AdminActivityLog.target_type == target_type)
        if from_date:
            conditions.append(
                AdminActivityLog.created_at >= datetime.combine(from_date, datetime.min.time())
            )
        if to_date:
            conditions.append(
                AdminActivityLog.created_at <= datetime.combine(to_date, datetime.max.time())
            )
        if search:
            conditions.append(
                or_(
                    AdminActivityLog.action.ilike(f"%{search}%"),
                    AdminActivityLog.target_type.ilike(f"%{search}%"),
                    cast(AdminActivityLog.details, String).ilike(f"%{search}%"),
                )
            )

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(AdminActivityLog.created_at.desc()).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        logs = []
        for row in result.all():
            log = row[0]  # AdminActivityLog
            logs.append({
                "id": log.id,
                "admin_id": log.admin_id,
                "admin_email": row.admin_email,
                "admin_name": f"{row.admin_first_name or ''} {row.admin_last_name or ''}".strip(),
                "action": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "details": log.details,
                "ip_address": str(log.ip_address) if log.ip_address else None,
                "created_at": log.created_at,
            })

        return logs, total

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ User Management â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


    async def archive_audit_logs(self, months: int = 12) -> tuple[str | None, int]:
        """Export audit logs older than N months to CSV, then delete them."""
        import csv
        import io
        from datetime import timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)

        count_q = select(func.count(AdminActivityLog.id)).where(
            AdminActivityLog.created_at < cutoff
        )
        count_result = await self.db.execute(count_q)
        old_count = count_result.scalar() or 0

        if old_count == 0:
            return None, 0

        query = (
            select(
                AdminActivityLog,
                User.email.label("admin_email"),
            )
            .join(User, User.id == AdminActivityLog.admin_id)
            .where(AdminActivityLog.created_at < cutoff)
            .order_by(AdminActivityLog.created_at.asc())
        )
        result = await self.db.execute(query)
        rows = result.all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID", "Admin Email", "Action", "Target Type", "Target ID",
            "Details", "IP Address", "Created At"
        ])
        for row in rows:
            log = row[0]
            writer.writerow([
                str(log.id),
                row.admin_email,
                log.action,
                log.target_type,
                str(log.target_id) if log.target_id else "",
                str(log.details) if log.details else "",
                str(log.ip_address) if log.ip_address else "",
                log.created_at.isoformat() if log.created_at else "",
            ])

        csv_content = output.getvalue()
        output.close()

        from sqlalchemy import delete as sa_delete
        delete_stmt = sa_delete(AdminActivityLog).where(
            AdminActivityLog.created_at < cutoff
        )
        await self.db.execute(delete_stmt)
        await self.db.commit()

        return csv_content, old_count

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 50,
        role: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> tuple[list, int]:
        """List users with filtering."""
        query = select(User).where(User.deleted_at.is_(None))
        count_query = select(func.count(User.id)).where(User.deleted_at.is_(None))

        conditions = []
        if role:
            conditions.append(User.role == role)
        if is_active is not None:
            conditions.append(User.is_active == is_active)
        if search:
            conditions.append(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.first_name.ilike(f"%{search}%"),
                    User.last_name.ilike(f"%{search}%"),
                )
            )

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(User.created_at.desc()).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        users = result.scalars().all()
        return users, total

    async def update_user_role(self, user_id: UUID, new_role: str, admin_id: UUID) -> User:
        """Assign a new role to a user."""
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise DashboardServiceError("User not found", 404)

        if user.id == admin_id:
            raise DashboardServiceError("Cannot change your own role")

        old_role = user.role
        user.role = new_role
        user.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

        logger.info(f"User {user.email} role changed: {old_role} â†’ {new_role} by {admin_id}")
        return user

    async def update_user_status(self, user_id: UUID, is_active: bool, admin_id: UUID) -> User:
        """Enable or disable a user account."""
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise DashboardServiceError("User not found", 404)

        if user.id == admin_id:
            raise DashboardServiceError("Cannot disable your own account")

        user.is_active = is_active
        user.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

        logger.info(f"User {user.email} {'enabled' if is_active else 'disabled'} by {admin_id}")
        return user

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ CSV Export â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def export_sales_csv(
        self,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> str:
        """Generate CSV string for sales report."""
        report = await self.get_sales_report(from_date=from_date, to_date=to_date)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Period", "Orders", "Revenue", "Tax", "Discount",
            "Avg Order Value", "Units Sold",
        ])
        for row in report["rows"]:
            writer.writerow([
                row["period"], row["order_count"], row["total_revenue"],
                row["total_tax"], row["total_discount"],
                row["avg_order_value"], row["units_sold"],
            ])
        # Summary row
        s = report["summary"]
        writer.writerow([])
        writer.writerow(["TOTAL", s["total_orders"], s["total_revenue"],
                         "", "", s["avg_order_value"], s["total_units"]])

        return output.getvalue()

    async def export_orders_csv(
        self,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> str:
        """Generate CSV of orders."""
        query = select(Order).where(
            Order.order_status.notin_(["cancelled"]),
        )
        if from_date:
            query = query.where(
                Order.created_at >= datetime.combine(from_date, datetime.min.time(), tzinfo=timezone.utc)
            )
        if to_date:
            query = query.where(
                Order.created_at <= datetime.combine(to_date, datetime.max.time(), tzinfo=timezone.utc)
            )
        query = query.order_by(Order.created_at.desc())

        result = await self.db.execute(query)
        orders = result.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Order Number", "Date", "Status", "Payment Status",
            "Subtotal", "Tax", "Shipping", "Discount", "Grand Total",
            "Currency", "Payment Method",
        ])
        for o in orders:
            writer.writerow([
                o.order_number,
                str(o.created_at.date()) if o.created_at else "",
                o.order_status, o.payment_status,
                o.subtotal, o.tax_amount, o.shipping_fee,
                o.discount_amount, o.grand_total,
                o.currency, o.payment_method,
            ])

        return output.getvalue()
