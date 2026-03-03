"""
Pydantic schemas for Admin Dashboard, Reports, Audit Logs & User Management.
Phase 11 â€” V2.5 Blueprint
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# DASHBOARD OVERVIEW
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class DashboardStats(BaseModel):
    """Top-level KPIs for admin dashboard."""
    total_revenue: Decimal = Decimal("0")
    total_orders: int = 0
    avg_order_value: Decimal = Decimal("0")
    total_customers: int = 0
    pending_orders: int = 0
    processing_orders: int = 0
    shipped_orders: int = 0
    delivered_orders: int = 0
    cancelled_orders: int = 0
    return_requested_count: int = 0
    pending_returns: int = 0
    failed_payments: int = 0
    low_stock_variants: int = 0
    pending_reviews: int = 0


class RevenueDataPoint(BaseModel):
    """Single data point for revenue chart."""
    date: str
    revenue: Decimal
    order_count: int


class DashboardChartData(BaseModel):
    """Chart data for dashboard."""
    revenue_trend: list[RevenueDataPoint] = []
    period: str = "30d"  # '7d', '30d', '90d', '1y'


class TopProduct(BaseModel):
    """Top selling product."""
    product_id: UUID
    title: str
    total_sold: int
    total_revenue: Decimal


class LowStockVariant(BaseModel):
    """Low stock alert item."""
    variant_id: UUID
    product_title: str
    sku: str
    size: str | None = None
    color: str | None = None
    stock_quantity: int


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SALES REPORT
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class SalesReportParams(BaseModel):
    """Query parameters for sales report."""
    from_date: date | None = None
    to_date: date | None = None
    category_id: UUID | None = None
    product_id: UUID | None = None
    group_by: str = "day"  # 'day', 'week', 'month'


class SalesReportRow(BaseModel):
    """Single row in sales report."""
    period: str
    order_count: int
    total_revenue: Decimal
    total_tax: Decimal
    total_discount: Decimal
    avg_order_value: Decimal
    units_sold: int


class SalesReportResponse(BaseModel):
    """Full sales report."""
    rows: list[SalesReportRow]
    summary: dict
    from_date: str | None = None
    to_date: str | None = None


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# COUPON PERFORMANCE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class CouponPerformanceRow(BaseModel):
    """Coupon usage stats."""
    coupon_id: UUID
    code: str
    type: str
    value: Decimal
    times_used: int
    total_discount_given: Decimal
    total_order_value: Decimal
    is_active: bool


class CouponPerformanceResponse(BaseModel):
    coupons: list[CouponPerformanceRow]
    total: int


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# AUDIT LOG
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class AuditLogEntry(BaseModel):
    id: UUID
    admin_id: UUID
    admin_email: str | None = None
    admin_name: str | None = None
    action: str
    target_type: str
    target_id: UUID | None = None
    details: dict | None = None
    ip_address: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    logs: list[AuditLogEntry]
    total: int
    page: int
    page_size: int


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# USER MANAGEMENT
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class UserListItem(BaseModel):
    id: UUID
    email: str
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    role: str
    is_active: bool
    email_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    users: list[UserListItem]
    total: int
    page: int
    page_size: int


class UserRoleUpdate(BaseModel):
    role: str = Field(..., pattern="^(customer|product_manager|order_manager|finance_manager|admin)$")


class UserStatusUpdate(BaseModel):
    is_active: bool


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# EXPORT
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class ExportRequest(BaseModel):
    """Request to export report data."""
    report_type: str = Field(..., pattern="^(sales|gst|invoices|credit_notes|coupons|orders)$")
    format: str = Field(default="csv", pattern="^(csv|pdf)$")
    from_date: date | None = None
    to_date: date | None = None
