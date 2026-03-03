"""
Invoice & Credit Note API Endpoints â€” Phase 9
V2.5 Blueprint Section 9

Routes:
  Customer:
    GET  /api/v1/orders/:id/invoice           â†’ Download invoice PDF
    GET  /api/v1/orders/:id/invoice/preview    â†’ View invoice data (JSON)

  Admin (FinanceManager):
    GET  /api/v1/admin/invoices               â†’ List all invoices
    GET  /api/v1/admin/invoices/:id/download   â†’ Download any invoice PDF
    POST /api/v1/admin/invoices/:id/regenerate â†’ Regenerate failed PDF
    GET  /api/v1/admin/credit-notes            â†’ List credit notes
    GET  /api/v1/admin/reports/gst-summary     â†’ HSN-wise GST report
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_role
from app.models.models import User
from app.schemas.invoice_schemas import (
    CreditNoteListResponse,
    CreditNoteResponse,
    CreditNoteSummaryResponse,
    GSTReportParams,
    GSTSummaryResponse,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceSummaryResponse,
)
from app.services.invoice_service import InvoiceService, InvoiceServiceError

router = APIRouter(tags=["Invoices"])


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# CUSTOMER ENDPOINTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


@router.get("/orders/{order_id}/invoice/preview")
async def preview_invoice(
    order_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """View invoice data for an order (JSON). Customer must own the order."""
    service = InvoiceService(db)
    invoice = await service.get_invoice_by_order(order_id)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found for this order")

    # Verify order ownership (unless admin)
    from sqlalchemy import select
    from app.models.models import Order
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != user.id and user.role == "customer":
        raise HTTPException(status_code=403, detail="Not authorized to view this invoice")

    return InvoiceResponse.model_validate(invoice)


@router.get("/orders/{order_id}/invoice")
async def download_invoice(
    order_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download invoice PDF for an order."""
    service = InvoiceService(db)
    invoice = await service.get_invoice_by_order(order_id)

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found for this order")

    # Verify ownership
    from sqlalchemy import select
    from app.models.models import Order
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != user.id and user.role == "customer":
        raise HTTPException(status_code=403, detail="Not authorized")

    if not invoice.pdf_url:
        raise HTTPException(
            status_code=404,
            detail="Invoice PDF not yet generated. Please try again later."
        )

    # If it's an S3/CDN URL, redirect
    if invoice.pdf_url.startswith("http"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=invoice.pdf_url)

    # If local file, serve it directly
    from pathlib import Path
    pdf_path = Path(invoice.pdf_url)
    if pdf_path.exists():
        return Response(
            content=pdf_path.read_bytes(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{invoice.invoice_number}.pdf"'
            },
        )

    raise HTTPException(status_code=404, detail="Invoice PDF file not found")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ADMIN ENDPOINTS â€” INVOICES
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


@router.get("/admin/invoices")
async def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    invoice_type: str | None = None,
    supply_type: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    search: str | None = None,
    user: User = Depends(require_role("finance_manager", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """List all invoices with filtering (FinanceManager/Admin)."""
    service = InvoiceService(db)
    invoices, total = await service.list_invoices(
        page=page,
        page_size=page_size,
        invoice_type=invoice_type,
        supply_type=supply_type,
        from_date=from_date,
        to_date=to_date,
        search=search,
    )
    return InvoiceListResponse(
        invoices=[InvoiceSummaryResponse.model_validate(inv) for inv in invoices],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/admin/invoices/{invoice_id}")
async def get_invoice_detail(
    invoice_id: UUID,
    user: User = Depends(require_role("finance_manager", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed invoice with line items (Admin)."""
    service = InvoiceService(db)
    invoice = await service.get_invoice_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return InvoiceResponse.model_validate(invoice)


@router.get("/admin/invoices/{invoice_id}/download")
async def admin_download_invoice(
    invoice_id: UUID,
    user: User = Depends(require_role("finance_manager", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """Download any invoice PDF (Admin)."""
    service = InvoiceService(db)
    invoice = await service.get_invoice_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if not invoice.pdf_url:
        raise HTTPException(status_code=404, detail="PDF not generated")

    if invoice.pdf_url.startswith("http"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=invoice.pdf_url)

    from pathlib import Path
    pdf_path = Path(invoice.pdf_url)
    if pdf_path.exists():
        return Response(
            content=pdf_path.read_bytes(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{invoice.invoice_number}.pdf"'
            },
        )

    raise HTTPException(status_code=404, detail="PDF file not found")


@router.post("/admin/invoices/{invoice_id}/regenerate")
async def regenerate_invoice_pdf(
    invoice_id: UUID,
    user: User = Depends(require_role("finance_manager", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """Regenerate a failed or missing invoice PDF (Admin)."""
    service = InvoiceService(db)
    try:
        pdf_url = await service.regenerate_invoice_pdf(invoice_id)
        await db.commit()
        return {"message": "PDF regenerated", "pdf_url": pdf_url}
    except InvoiceServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ADMIN ENDPOINTS â€” CREDIT NOTES
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


@router.get("/admin/credit-notes")
async def list_credit_notes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    user: User = Depends(require_role("finance_manager", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """List credit notes (FinanceManager/Admin)."""
    service = InvoiceService(db)
    credit_notes, total = await service.list_credit_notes(
        page=page,
        page_size=page_size,
        from_date=from_date,
        to_date=to_date,
    )
    return CreditNoteListResponse(
        credit_notes=[CreditNoteSummaryResponse.model_validate(cn) for cn in credit_notes],
        total=total,
        page=page,
        page_size=page_size,
    )


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ADMIN ENDPOINTS â€” GST REPORTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


@router.get("/admin/reports/gst-summary")
async def gst_summary_report(
    financial_year: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    user: User = Depends(require_role("finance_manager", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    HSN-wise GST summary report for a financial year.
    Used for GST return filing (GSTR-1, GSTR-3B).

    Example: GET /admin/reports/gst-summary?financial_year=2025-26
    """
    service = InvoiceService(db)
    summary = await service.generate_gst_summary(
        financial_year=financial_year,
        from_date=from_date,
        to_date=to_date,
    )
    return GSTSummaryResponse(**summary)
