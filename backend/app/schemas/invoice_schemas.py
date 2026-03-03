"""
Pydantic schemas for Invoice & Credit Note endpoints.
Phase 9 — V2.5 Blueprint
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


# ──────────────── Invoice Line Item ────────────────

class InvoiceLineItemResponse(BaseModel):
    id: UUID
    order_item_id: UUID | None = None
    invoice_date: str
    invoice_number: str | None = None
    quantity: int
    unit_price: Decimal
    taxable_amount: Decimal
    cgst_rate: Decimal = Decimal("0")
    cgst_amount: Decimal = Decimal("0")
    sgst_rate: Decimal = Decimal("0")
    sgst_amount: Decimal = Decimal("0")
    igst_rate: Decimal = Decimal("0")
    igst_amount: Decimal = Decimal("0")
    total_amount: Decimal

    model_config = {"from_attributes": True}


# ──────────────── Invoice Response ────────────────

class InvoiceResponse(BaseModel):
    id: UUID
    order_id: UUID
    invoice_number: str
    invoice_type: str

    # Seller
    seller_name: str
    seller_gstin: str | None = None
    seller_address: str
    seller_state: str | None = None
    seller_state_code: str | None = None

    # Buyer
    buyer_name: str
    buyer_address: str
    buyer_gstin: str | None = None
    buyer_state: str | None = None
    buyer_state_code: str | None = None

    # Amounts
    subtotal: Decimal
    cgst_amount: Decimal = Decimal("0")
    sgst_amount: Decimal = Decimal("0")
    igst_amount: Decimal = Decimal("0")
    shipping_fee: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    grand_total: Decimal
    currency: str

    # Supply
    place_of_supply: str | None = None
    supply_type: str | None = None

    # Document
    pdf_url: str | None = None
    generated_at: datetime | None = None
    created_at: datetime

    line_items: list[InvoiceLineItemResponse] = []

    model_config = {"from_attributes": True}


class InvoiceSummaryResponse(BaseModel):
    """Lightweight invoice response for listings."""
    id: UUID
    order_id: UUID
    invoice_number: str
    invoice_type: str
    buyer_name: str
    grand_total: Decimal
    currency: str
    supply_type: str | None = None
    pdf_url: str | None = None
    generated_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InvoiceListResponse(BaseModel):
    invoices: list[InvoiceSummaryResponse]
    total: int
    page: int
    page_size: int


# ──────────────── Credit Note Response ────────────────

class CreditNoteResponse(BaseModel):
    id: UUID
    invoice_id: UUID
    return_id: UUID | None = None
    refund_id: UUID | None = None
    credit_note_number: str
    reason: str

    subtotal: Decimal
    cgst_amount: Decimal = Decimal("0")
    sgst_amount: Decimal = Decimal("0")
    igst_amount: Decimal = Decimal("0")
    total_amount: Decimal

    pdf_url: str | None = None
    issued_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CreditNoteSummaryResponse(BaseModel):
    id: UUID
    invoice_id: UUID
    credit_note_number: str
    reason: str
    total_amount: Decimal
    pdf_url: str | None = None
    issued_at: datetime | None = None

    model_config = {"from_attributes": True}


class CreditNoteListResponse(BaseModel):
    credit_notes: list[CreditNoteSummaryResponse]
    total: int
    page: int
    page_size: int


# ──────────────── GST Summary Report ────────────────

class GSTInvoiceItem(BaseModel):
    invoice_number: str
    invoice_date: str
    supply_type: str
    total_taxable_amount: Decimal
    cgst_amount: Decimal = Decimal("0")
    sgst_amount: Decimal = Decimal("0")
    igst_amount: Decimal = Decimal("0")
    total_tax: Decimal
    total_amount: Decimal


class GSTSummaryResponse(BaseModel):
    """Invoice-wise GST summary report for a date range."""
    financial_year: str
    from_date: datetime
    to_date: datetime
    invoices: list[GSTInvoiceItem]
    total_taxable: Decimal
    total_cgst: Decimal
    total_sgst: Decimal
    total_igst: Decimal
    total_tax: Decimal
    total_invoice_value: Decimal
    invoice_count: int
    credit_note_count: int


# ──────────────── Query Parameters ────────────────

class InvoiceFilterParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    invoice_type: str | None = None
    supply_type: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    search: str | None = None  # invoice number or buyer name


class GSTReportParams(BaseModel):
    financial_year: str = Field(..., pattern=r"^\d{4}-\d{2}$")  # e.g., '2025-26'
    from_date: datetime | None = None
    to_date: datetime | None = None
