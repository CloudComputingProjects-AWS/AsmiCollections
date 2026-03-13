"""
Admin Dashboard, Reports, Audit Logs & User Management API Endpoints â€” Phase 11
V2.5 Blueprint

Routes:
  Dashboard:
    GET  /api/v1/admin/dashboard/stats           â†’ KPIs
    GET  /api/v1/admin/dashboard/revenue-trend    â†’ Revenue chart data
    GET  /api/v1/admin/dashboard/top-products     â†’ Best sellers
    GET  /api/v1/admin/dashboard/low-stock        â†’ Low stock alerts

  Reports:
    GET  /api/v1/admin/reports/sales              â†’ Sales report
    GET  /api/v1/admin/reports/coupon-performance  â†’ Coupon stats

  Exports:
    GET  /api/v1/admin/exports/sales              â†’ Sales CSV
    GET  /api/v1/admin/exports/orders             â†’ Orders CSV

  Audit Logs:
    GET  /api/v1/admin/audit-logs                 â†’ Searchable audit log

  User Management:
    GET  /api/v1/admin/users                      â†’ List users
    GET  /api/v1/admin/users/:id                  â†’ User detail
    PUT  /api/v1/admin/users/:id/role             â†’ Assign role
    PUT  /api/v1/admin/users/:id/status           â†’ Enable/disable
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_role
from app.models.models import User
from app.schemas.admin_dashboard_schemas import (
    AuditLogListResponse,
    CouponPerformanceResponse,
    DashboardChartData,
    DashboardStats,
    ExportRequest,
    SalesReportResponse,
    UserListItem,
    UserListResponse,
    UserRoleUpdate,
    UserStatusUpdate,
)
from app.services.admin_dashboard_service import (
    AdminDashboardService,
    DashboardServiceError,
)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# DASHBOARD
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

dashboard_router = APIRouter(
    prefix="/admin/dashboard",
    tags=["Admin Dashboard"],
)
admin_dep = require_role("admin")


@dashboard_router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    user: User = Depends(admin_dep),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard KPIs: revenue, orders, alerts."""
    service = AdminDashboardService(db)
    stats = await service.get_dashboard_stats()
    return DashboardStats(**stats)


@dashboard_router.get("/revenue-trend", response_model=DashboardChartData)
async def get_revenue_trend(
    period: str = Query("30d", pattern="^(7d|30d|90d|1y)$"),
    user: User = Depends(admin_dep),
    db: AsyncSession = Depends(get_db),
):
    """Get revenue trend data for charts."""
    service = AdminDashboardService(db)
    trend = await service.get_revenue_trend(period)
    return DashboardChartData(revenue_trend=trend, period=period)


@dashboard_router.get("/top-products")
async def get_top_products(
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(admin_dep),
    db: AsyncSession = Depends(get_db),
):
    """Get top selling products."""
    service = AdminDashboardService(db)
    products = await service.get_top_products(limit)
    return {"products": products}


@dashboard_router.get("/low-stock")
async def get_low_stock(
    threshold: int = Query(10, ge=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user: User = Depends(admin_dep),
    db: AsyncSession = Depends(get_db),
):
    """Get low stock variant alerts."""
    service = AdminDashboardService(db)
    variants, total = await service.get_low_stock_variants(threshold, page, page_size)
    return {"variants": variants, "total": total, "page": page, "page_size": page_size}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# REPORTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

reports_router = APIRouter(
    prefix="/admin/reports",
    tags=["Admin Reports"],
)
finance_dep = require_role("finance_manager", "admin")


@reports_router.get("/sales", response_model=SalesReportResponse)
async def get_sales_report(
    from_date: date | None = None,
    to_date: date | None = None,
    category_id: UUID | None = None,
    product_id: UUID | None = None,
    group_by: str = Query("day", pattern="^(day|week|month)$"),
    user: User = Depends(finance_dep),
    db: AsyncSession = Depends(get_db),
):
    """Generate sales report with filters."""
    service = AdminDashboardService(db)
    report = await service.get_sales_report(
        from_date=from_date, to_date=to_date,
        category_id=category_id, product_id=product_id,
        group_by=group_by,
    )
    return report


@reports_router.get("/coupon-performance", response_model=CouponPerformanceResponse)
async def get_coupon_performance(
    user: User = Depends(finance_dep),
    db: AsyncSession = Depends(get_db),
):
    """Get coupon usage statistics."""
    service = AdminDashboardService(db)
    coupons = await service.get_coupon_performance()
    return CouponPerformanceResponse(coupons=coupons, total=len(coupons))


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# EXPORTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

exports_router = APIRouter(
    prefix="/admin/exports",
    tags=["Admin Exports"],
)


@exports_router.get("/sales")
async def export_sales_csv(
    from_date: date | None = None,
    to_date: date | None = None,
    user: User = Depends(finance_dep),
    db: AsyncSession = Depends(get_db),
):
    """Download sales report as CSV."""
    service = AdminDashboardService(db)
    csv_content = await service.export_sales_csv(from_date, to_date)

    filename = f"sales_report_{from_date or 'all'}_{to_date or 'all'}.csv"
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@exports_router.get("/orders")
async def export_orders_csv(
    from_date: date | None = None,
    to_date: date | None = None,
    user: User = Depends(finance_dep),
    db: AsyncSession = Depends(get_db),
):
    """Download orders as CSV."""
    service = AdminDashboardService(db)
    csv_content = await service.export_orders_csv(from_date, to_date)

    filename = f"orders_{from_date or 'all'}_{to_date or 'all'}.csv"
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# AUDIT LOGS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

audit_router = APIRouter(
    prefix="/admin/audit-logs",
    tags=["Admin Audit Logs"],
)
# admin_dep already defined above as require_role("admin")


@audit_router.get("", response_model=AuditLogListResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    admin_id: UUID | None = None,
    action: str | None = None,
    target_type: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    search: str | None = None,
    user: User = Depends(admin_dep),
    db: AsyncSession = Depends(get_db),
):
    """Search audit logs with filters."""
    service = AdminDashboardService(db)
    logs, total = await service.get_audit_logs(
        page=page, page_size=page_size,
        admin_id=admin_id, action=action,
        target_type=target_type,
        from_date=from_date, to_date=to_date,
        search=search,
    )
    return AuditLogListResponse(
        logs=logs, total=total, page=page, page_size=page_size,
    )




@audit_router.post("/archive")
async def archive_old_logs(
    months: int = Query(12, ge=1, le=60, description="Archive logs older than N months"),
    confirm: bool = Query(False, description="Set to true to actually delete after export"),
    user: User = Depends(admin_dep),
    db: AsyncSession = Depends(get_db),
):
    """
    Export audit logs older than N months as CSV download.
    If confirm=true, also deletes the archived logs from the database.
    Step 1: Call with confirm=false to preview count.
    Step 2: Call with confirm=true to export CSV and purge.
    """
    import io
    import csv
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import select, delete as sa_delete
    from app.models.models import AdminActivityLog as ALog

    cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)

    service = AdminDashboardService(db)

    # Count old logs
    from sqlalchemy import func as sqlfunc
    count_q = select(sqlfunc.count(ALog.id)).where(ALog.created_at < cutoff)
    count_result = await db.execute(count_q)
    old_count = count_result.scalar() or 0

    if old_count == 0:
        return {"count": 0, "message": "No logs older than the specified period"}

    if not confirm:
        return {"count": old_count, "message": f"{old_count} logs older than {months} months found. Call with confirm=true to export and purge."}

    # Fetch all old logs with admin email
    query = (
        select(ALog, User.email.label("admin_email"))
        .join(User, User.id == ALog.admin_id)
        .where(ALog.created_at < cutoff)
        .order_by(ALog.created_at.asc())
    )
    result = await db.execute(query)
    rows = result.all()

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Admin Email", "Action", "Target Type", "Target ID", "Details", "IP Address", "Created At"])
    for row in rows:
        log = row[0]
        writer.writerow([
            str(log.id), row.admin_email, log.action, log.target_type,
            str(log.target_id) if log.target_id else "",
            str(log.details) if log.details else "",
            str(log.ip_address) if log.ip_address else "",
            log.created_at.isoformat() if log.created_at else "",
        ])
    csv_bytes = output.getvalue().encode("utf-8")
    output.close()

    # Delete archived logs
    delete_stmt = sa_delete(ALog).where(ALog.created_at < cutoff)
    await db.execute(delete_stmt)
    await db.commit()

    filename = f"audit_logs_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# USER MANAGEMENT
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

user_mgmt_router = APIRouter(
    prefix="/admin/users",
    tags=["Admin User Management"],
)


@user_mgmt_router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    role: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    user: User = Depends(admin_dep),
    db: AsyncSession = Depends(get_db),
):
    """List all users with filters."""
    service = AdminDashboardService(db)
    users, total = await service.list_users(
        page=page, page_size=page_size,
        role=role, is_active=is_active, search=search,
    )
    return UserListResponse(
        users=[UserListItem.model_validate(u) for u in users],
        total=total, page=page, page_size=page_size,
    )


@user_mgmt_router.get("/{user_id}", response_model=UserListItem)
async def get_user_detail(
    user_id: UUID,
    user: User = Depends(admin_dep),
    db: AsyncSession = Depends(get_db),
):
    """Get user details."""
    from sqlalchemy import select as sa_select
    from app.models.models import User as UserModel
    result = await db.execute(
        sa_select(UserModel).where(UserModel.id == user_id, UserModel.deleted_at.is_(None))
    )
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserListItem.model_validate(target_user)


@user_mgmt_router.put("/{user_id}/role", response_model=UserListItem)
async def update_user_role(
    user_id: UUID,
    data: UserRoleUpdate,
    user: User = Depends(admin_dep),
    db: AsyncSession = Depends(get_db),
):
    """Assign role to a user. Admin only."""
    service = AdminDashboardService(db)
    try:
        updated = await service.update_user_role(user_id, data.role, user.id)
        await db.commit()
        return UserListItem.model_validate(updated)
    except DashboardServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@user_mgmt_router.put("/{user_id}/status", response_model=UserListItem)
async def update_user_status(
    user_id: UUID,
    data: UserStatusUpdate,
    user: User = Depends(admin_dep),
    db: AsyncSession = Depends(get_db),
):
    """Enable or disable a user account. Admin only."""
    service = AdminDashboardService(db)
    try:
        updated = await service.update_user_status(user_id, data.is_active, user.id)
        await db.commit()
        return UserListItem.model_validate(updated)
    except DashboardServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
