"""
PDF Generator — Renders invoice & credit note PDFs using PyMuPDF.
Phase 9 — V2.5 Blueprint (Rewritten S11)

Uses PyMuPDF (fitz) for direct PDF generation with precise layout control.
Uploads to S3 if configured, otherwise saves locally.

Replaces previous weasyprint/xhtml2pdf HTML-based approach.
"""

import io
import logging
import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# ———————————— Constants ————————————

CURRENCY_SYMBOLS = {
    "INR": "\u20b9",
    "USD": "$",
    "EUR": "\u20ac",
    "GBP": "\u00a3",
}

# Colors
COLOR_DARK = (0.173, 0.243, 0.314)      # #2c3e50
COLOR_WHITE = (1, 1, 1)
COLOR_BLACK = (0.1, 0.1, 0.1)
COLOR_GRAY = (0.4, 0.4, 0.4)
COLOR_LIGHT_GRAY = (0.96, 0.96, 0.96)   # #f5f5f5
COLOR_HEADER_BG = (0.973, 0.976, 0.98)  # #f8f9fa
COLOR_SUPPLY_BG = (0.941, 0.957, 0.973) # #f0f4f8
COLOR_GREEN = (0.153, 0.682, 0.376)     # #27ae60
COLOR_RED = (0.753, 0.224, 0.169)       # #c0392b
COLOR_RED_BG = (0.992, 0.949, 0.949)    # #fdf2f2
COLOR_YELLOW_BG = (1.0, 0.976, 0.902)   # #fff9e6
COLOR_BORDER = (0.8, 0.8, 0.8)

# Page dimensions (A4)
PAGE_W = 595.28
PAGE_H = 841.89
MARGIN_L = 40
MARGIN_R = 40
MARGIN_T = 40
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R

# Font sizes
FS_TITLE = 14
FS_HEADING = 10
FS_NORMAL = 9
FS_SMALL = 8
FS_TINY = 7


def _fmt(value) -> str:
    """Format decimal to comma-separated string with 2 decimal places."""
    if value is None:
        return "0.00"
    v = Decimal(str(value))
    return f"{v:,.2f}"


def _get_symbol(currency: str) -> str:
    return CURRENCY_SYMBOLS.get(currency or "INR", "\u20b9")


def _supply_display(supply_type: str) -> str:
    return {
        "intra_state": "Intra-State",
        "inter_state": "Inter-State",
        "export": "Export",
    }.get(supply_type or "", supply_type or "")


# ———————————— Invoice PDF ————————————

def _draw_invoice_pdf(data: dict) -> bytes:
    """Build a complete invoice PDF using PyMuPDF and return bytes."""
    doc = fitz.open()
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    y = MARGIN_T
    sym = _get_symbol(data.get("currency", "INR"))
    supply_type = data.get("supply_type", "")
    is_intra = supply_type == "intra_state"

    # ── Header ──
    header_h = 36
    page.draw_rect(fitz.Rect(MARGIN_L, y, PAGE_W - MARGIN_R, y + header_h),
                   color=None, fill=COLOR_HEADER_BG)
    page.draw_rect(fitz.Rect(MARGIN_L, y, PAGE_W - MARGIN_R, y + header_h),
                   color=COLOR_DARK, width=0.5)
    title = "TAX INVOICE" if data.get("invoice_type") == "tax_invoice" else "PROFORMA INVOICE"
    page.insert_text(fitz.Point(PAGE_W / 2 - len(title) * 3.5, y + 23),
                     title, fontsize=FS_TITLE, fontname="helv",
                     color=COLOR_BLACK)
    y += header_h

    # ── Invoice Meta ──
    meta_h = 40
    page.draw_rect(fitz.Rect(MARGIN_L, y, PAGE_W - MARGIN_R, y + meta_h),
                   color=COLOR_BORDER, fill=COLOR_LIGHT_GRAY, width=0.3)
    page.insert_text(fitz.Point(MARGIN_L + 8, y + 14),
                     f"Invoice No: {data.get('invoice_number', '')}",
                     fontsize=FS_NORMAL, fontname="hebo", color=COLOR_BLACK)
    page.insert_text(fitz.Point(MARGIN_L + 8, y + 28),
                     f"Order No: {data.get('order_number', '')}",
                     fontsize=FS_NORMAL, fontname="helv", color=COLOR_BLACK)
    page.insert_text(fitz.Point(PAGE_W - MARGIN_R - 180, y + 14),
                     f"Date: {data.get('invoice_date', '')}",
                     fontsize=FS_NORMAL, fontname="hebo", color=COLOR_BLACK)
    page.insert_text(fitz.Point(PAGE_W - MARGIN_R - 180, y + 28),
                     f"Payment: {data.get('payment_method', 'N/A')}",
                     fontsize=FS_NORMAL, fontname="helv", color=COLOR_BLACK)
    y += meta_h

    # ── Seller / Buyer ──
    party_h = 72
    mid_x = MARGIN_L + CONTENT_W / 2
    page.draw_rect(fitz.Rect(MARGIN_L, y, PAGE_W - MARGIN_R, y + party_h),
                   color=COLOR_BORDER, width=0.3)
    page.draw_line(fitz.Point(mid_x, y), fitz.Point(mid_x, y + party_h),
                   color=COLOR_BORDER, width=0.3)

    # Seller
    sy = y + 12
    page.insert_text(fitz.Point(MARGIN_L + 8, sy), "SOLD BY",
                     fontsize=FS_TINY, fontname="hebo", color=COLOR_GRAY)
    sy += 12
    page.insert_text(fitz.Point(MARGIN_L + 8, sy),
                     data.get("seller_name", ""), fontsize=FS_NORMAL, fontname="hebo", color=COLOR_BLACK)
    sy += 12
    gstin = data.get("seller_gstin", "")
    if gstin:
        page.insert_text(fitz.Point(MARGIN_L + 8, sy),
                         f"GSTIN: {gstin}", fontsize=FS_SMALL, fontname="helv", color=COLOR_BLACK)
        sy += 11
    addr = data.get("seller_address", "")
    if addr:
        # Wrap address if too long
        for line in _wrap_text(addr, 42):
            page.insert_text(fitz.Point(MARGIN_L + 8, sy),
                             line, fontsize=FS_SMALL, fontname="helv", color=COLOR_BLACK)
            sy += 10
    sstate = data.get("seller_state", "")
    scode = data.get("seller_state_code", "")
    if sstate:
        page.insert_text(fitz.Point(MARGIN_L + 8, sy),
                         f"{sstate}" + (f" ({scode})" if scode else ""),
                         fontsize=FS_SMALL, fontname="helv", color=COLOR_BLACK)

    # Buyer
    by_ = y + 12
    page.insert_text(fitz.Point(mid_x + 8, by_), "BILL TO / SHIP TO",
                     fontsize=FS_TINY, fontname="hebo", color=COLOR_GRAY)
    by_ += 12
    page.insert_text(fitz.Point(mid_x + 8, by_),
                     data.get("buyer_name", ""), fontsize=FS_NORMAL, fontname="hebo", color=COLOR_BLACK)
    by_ += 12
    bgstin = data.get("buyer_gstin", "")
    if bgstin:
        page.insert_text(fitz.Point(mid_x + 8, by_),
                         f"GSTIN: {bgstin}", fontsize=FS_SMALL, fontname="helv", color=COLOR_BLACK)
        by_ += 11
    baddr = data.get("buyer_address", "")
    if baddr:
        for line in _wrap_text(baddr, 42):
            page.insert_text(fitz.Point(mid_x + 8, by_),
                             line, fontsize=FS_SMALL, fontname="helv", color=COLOR_BLACK)
            by_ += 10
    bstate = data.get("buyer_state", "")
    bcode = data.get("buyer_state_code", "")
    if bstate:
        page.insert_text(fitz.Point(mid_x + 8, by_),
                         f"{bstate}" + (f" ({bcode})" if bcode else ""),
                         fontsize=FS_SMALL, fontname="helv", color=COLOR_BLACK)

    y += party_h

    # ── Supply Info ──
    supply_h = 22
    page.draw_rect(fitz.Rect(MARGIN_L, y, PAGE_W - MARGIN_R, y + supply_h),
                   color=COLOR_BORDER, fill=COLOR_SUPPLY_BG, width=0.3)
    page.insert_text(fitz.Point(MARGIN_L + 8, y + 14),
                     f"Place of Supply: {data.get('place_of_supply', 'N/A')}",
                     fontsize=FS_SMALL, fontname="hebo", color=COLOR_BLACK)
    page.insert_text(fitz.Point(MARGIN_L + 280, y + 14),
                     f"Supply Type: {_supply_display(supply_type)}",
                     fontsize=FS_SMALL, fontname="hebo", color=COLOR_BLACK)
    y += supply_h

    # ── Line Items Table ──
    line_items = data.get("line_items", [])

    # Column definitions: (label, x_start, width, align)
    # Adjust columns based on intra vs inter state
    if is_intra:
        cols = [
            ("#",       MARGIN_L,       24,  "center"),
            ("Description", MARGIN_L + 24, 150, "left"),
            ("HSN",     MARGIN_L + 174,  45,  "left"),
            ("Qty",     MARGIN_L + 219,  30,  "right"),
            (f"Rate({sym})", MARGIN_L + 249, 65, "right"),
            ("CGST",    MARGIN_L + 314,  60,  "right"),
            ("SGST",    MARGIN_L + 374,  60,  "right"),
            (f"Total({sym})", MARGIN_L + 434, 81, "right"),
        ]
    else:
        cols = [
            ("#",       MARGIN_L,       24,  "center"),
            ("Description", MARGIN_L + 24, 165, "left"),
            ("HSN",     MARGIN_L + 189,  50,  "left"),
            ("Qty",     MARGIN_L + 239,  30,  "right"),
            (f"Rate({sym})", MARGIN_L + 269, 70, "right"),
            ("IGST",    MARGIN_L + 339,  75,  "right"),
            (f"Total({sym})", MARGIN_L + 414, 101, "right"),
        ]

    # Table header
    th_h = 22
    page.draw_rect(fitz.Rect(MARGIN_L, y, PAGE_W - MARGIN_R, y + th_h),
                   color=None, fill=COLOR_DARK)
    for label, cx, cw, align in cols:
        tx = cx + 4 if align == "left" else (cx + cw - 4 if align == "right" else cx + cw / 2 - len(label) * 2)
        page.insert_text(fitz.Point(tx, y + 15),
                         label, fontsize=FS_TINY, fontname="hebo", color=COLOR_WHITE)
    y += th_h

    # Table rows
    for idx, item in enumerate(line_items):
        row_h = 28
        # Check if we need a new page
        if y + row_h > PAGE_H - 160:
            page = doc.new_page(width=PAGE_W, height=PAGE_H)
            y = MARGIN_T

        # Alternating row background
        if idx % 2 == 1:
            page.draw_rect(fitz.Rect(MARGIN_L, y, PAGE_W - MARGIN_R, y + row_h),
                           color=None, fill=COLOR_LIGHT_GRAY)

        # Row border
        page.draw_line(fitz.Point(MARGIN_L, y + row_h), fitz.Point(PAGE_W - MARGIN_R, y + row_h),
                       color=(0.93, 0.93, 0.93), width=0.3)

        row_y_text = y + 11
        row_y_sub = y + 22

        # # column
        page.insert_text(fitz.Point(cols[0][1] + 8, row_y_text),
                         str(idx + 1), fontsize=FS_SMALL, fontname="helv", color=COLOR_BLACK)

        # Description (may need wrapping)
        desc = item.get("description", "")
        desc_lines = _wrap_text(desc, 26)
        for i, dl in enumerate(desc_lines[:2]):  # Max 2 lines
            page.insert_text(fitz.Point(cols[1][1] + 4, row_y_text + i * 10),
                             dl, fontsize=FS_SMALL, fontname="helv", color=COLOR_BLACK)

        # HSN
        page.insert_text(fitz.Point(cols[2][1] + 4, row_y_text),
                         str(item.get("hsn_code", "")),
                         fontsize=FS_SMALL, fontname="helv", color=COLOR_BLACK)

        # Qty
        page.insert_text(fitz.Point(cols[3][1] + cols[3][2] - 4 - len(str(item.get("quantity", 0))) * 4, row_y_text),
                         str(item.get("quantity", 0)),
                         fontsize=FS_SMALL, fontname="helv", color=COLOR_BLACK)

        # Rate
        rate_str = _fmt(item.get("unit_price", 0))
        page.insert_text(fitz.Point(cols[4][1] + cols[4][2] - 4 - len(rate_str) * 4, row_y_text),
                         rate_str, fontsize=FS_SMALL, fontname="cour", color=COLOR_BLACK)

        if is_intra:
            # CGST: rate% + amount
            cgst_r = f"{item.get('cgst_rate', 0)}%"
            cgst_a = _fmt(item.get("cgst_amount", 0))
            page.insert_text(fitz.Point(cols[5][1] + cols[5][2] - 4 - len(cgst_r) * 4, row_y_text),
                             cgst_r, fontsize=FS_TINY, fontname="helv", color=COLOR_GRAY)
            page.insert_text(fitz.Point(cols[5][1] + cols[5][2] - 4 - len(cgst_a) * 4, row_y_sub),
                             cgst_a, fontsize=FS_SMALL, fontname="cour", color=COLOR_BLACK)
            # SGST: rate% + amount
            sgst_r = f"{item.get('sgst_rate', 0)}%"
            sgst_a = _fmt(item.get("sgst_amount", 0))
            page.insert_text(fitz.Point(cols[6][1] + cols[6][2] - 4 - len(sgst_r) * 4, row_y_text),
                             sgst_r, fontsize=FS_TINY, fontname="helv", color=COLOR_GRAY)
            page.insert_text(fitz.Point(cols[6][1] + cols[6][2] - 4 - len(sgst_a) * 4, row_y_sub),
                             sgst_a, fontsize=FS_SMALL, fontname="cour", color=COLOR_BLACK)
            # Total
            total_str = _fmt(item.get("total_amount", 0))
            page.insert_text(fitz.Point(cols[7][1] + cols[7][2] - 4 - len(total_str) * 4.5, row_y_text),
                             total_str, fontsize=FS_NORMAL, fontname="hebo", color=COLOR_BLACK)
        else:
            # IGST: rate% + amount
            igst_r = f"{item.get('igst_rate', 0)}%"
            igst_a = _fmt(item.get("igst_amount", 0))
            page.insert_text(fitz.Point(cols[5][1] + cols[5][2] - 4 - len(igst_r) * 4, row_y_text),
                             igst_r, fontsize=FS_TINY, fontname="helv", color=COLOR_GRAY)
            page.insert_text(fitz.Point(cols[5][1] + cols[5][2] - 4 - len(igst_a) * 4, row_y_sub),
                             igst_a, fontsize=FS_SMALL, fontname="cour", color=COLOR_BLACK)
            # Total
            total_str = _fmt(item.get("total_amount", 0))
            page.insert_text(fitz.Point(cols[6][1] + cols[6][2] - 4 - len(total_str) * 4.5, row_y_text),
                             total_str, fontsize=FS_NORMAL, fontname="hebo", color=COLOR_BLACK)

        y += row_h

    # ── Totals Section ──
    y += 4
    page.draw_line(fitz.Point(MARGIN_L, y), fitz.Point(PAGE_W - MARGIN_R, y),
                   color=COLOR_DARK, width=1.5)
    y += 8

    totals_x_label = PAGE_W - MARGIN_R - 220
    totals_x_value = PAGE_W - MARGIN_R - 8

    def _draw_total_row(label, value, bold=False, color=COLOR_BLACK):
        nonlocal y
        fn = "hebo" if bold else "helv"
        fs = FS_NORMAL + 2 if bold else FS_NORMAL
        page.insert_text(fitz.Point(totals_x_label, y),
                         label, fontsize=fs, fontname=fn, color=color)
        val_str = value if isinstance(value, str) else _fmt(value)
        page.insert_text(fitz.Point(totals_x_value - len(val_str) * 4.5, y),
                         val_str, fontsize=fs, fontname="cour" if not bold else "cobo", color=color)
        y += 16 if bold else 14

    _draw_total_row("Subtotal:", data.get("subtotal", 0))

    if is_intra:
        _draw_total_row("CGST:", data.get("cgst_amount", 0))
        _draw_total_row("SGST:", data.get("sgst_amount", 0))
    elif supply_type == "inter_state":
        _draw_total_row("IGST:", data.get("igst_amount", 0))

    shipping = data.get("shipping_fee", 0)
    if shipping and Decimal(str(shipping)) > 0:
        _draw_total_row("Shipping:", shipping)

    discount = data.get("discount_amount", 0)
    if discount and Decimal(str(discount)) > 0:
        coupon = data.get("coupon_code", "")
        label = f"Discount ({coupon}):" if coupon else "Discount:"
        _draw_total_row(label, f"-{_fmt(discount)}", color=COLOR_GREEN)

    y += 2
    page.draw_line(fitz.Point(totals_x_label - 10, y), fitz.Point(PAGE_W - MARGIN_R, y),
                   color=COLOR_DARK, width=0.8)
    y += 10
    _draw_total_row("GRAND TOTAL:", f"{sym}{_fmt(data.get('grand_total', 0))}", bold=True)

    # ── Amount in Words ──
    y += 4
    page.draw_line(fitz.Point(MARGIN_L, y), fitz.Point(PAGE_W - MARGIN_R, y),
                   color=COLOR_BORDER, width=0.3)
    y += 14
    page.insert_text(fitz.Point(MARGIN_L + 8, y),
                     f"Amount in words: {data.get('amount_in_words', '')}",
                     fontsize=FS_SMALL, fontname="hebi", color=COLOR_GRAY)

    # ── Footer ──
    y += 18
    page.draw_line(fitz.Point(MARGIN_L, y), fitz.Point(PAGE_W - MARGIN_R, y),
                   color=COLOR_BORDER, width=0.3)
    y += 12
    payment_method = data.get("payment_method", "")
    txn_id = data.get("payment_txn_id", "")
    footer_text = ""
    if payment_method:
        footer_text += f"Payment Method: {payment_method}"
    if txn_id:
        footer_text += f"  |  Txn ID: {txn_id}"
    if footer_text:
        page.insert_text(fitz.Point(MARGIN_L + 8, y),
                         footer_text, fontsize=FS_SMALL, fontname="helv", color=COLOR_GRAY)
    y += 16
    page.insert_text(fitz.Point(PAGE_W / 2 - 100, y),
                     "This is a computer-generated invoice. No signature required.",
                     fontsize=FS_TINY, fontname="helv", color=(0.6, 0.6, 0.6))

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# ———————————— Credit Note PDF ————————————

def _draw_credit_note_pdf(data: dict) -> bytes:
    """Build a complete credit note PDF using PyMuPDF and return bytes."""
    doc = fitz.open()
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    y = MARGIN_T
    sym = _get_symbol(data.get("currency", "INR"))

    # ── Header ──
    header_h = 36
    page.draw_rect(fitz.Rect(MARGIN_L, y, PAGE_W - MARGIN_R, y + header_h),
                   color=None, fill=COLOR_RED_BG)
    page.draw_rect(fitz.Rect(MARGIN_L, y, PAGE_W - MARGIN_R, y + header_h),
                   color=COLOR_RED, width=0.8)
    page.insert_text(fitz.Point(PAGE_W / 2 - 45, y + 24),
                     "CREDIT NOTE", fontsize=FS_TITLE, fontname="hebo", color=COLOR_RED)
    y += header_h

    # ── Meta ──
    meta_h = 40
    page.draw_rect(fitz.Rect(MARGIN_L, y, PAGE_W - MARGIN_R, y + meta_h),
                   color=COLOR_BORDER, fill=COLOR_LIGHT_GRAY, width=0.3)
    page.insert_text(fitz.Point(MARGIN_L + 8, y + 14),
                     f"Credit Note No: {data.get('credit_note_number', '')}",
                     fontsize=FS_NORMAL, fontname="hebo", color=COLOR_BLACK)
    page.insert_text(fitz.Point(MARGIN_L + 8, y + 28),
                     f"Against Invoice: {data.get('original_invoice_number', '')}",
                     fontsize=FS_NORMAL, fontname="helv", color=COLOR_BLACK)
    page.insert_text(fitz.Point(PAGE_W - MARGIN_R - 180, y + 14),
                     f"Date: {data.get('issued_date', '')}",
                     fontsize=FS_NORMAL, fontname="hebo", color=COLOR_BLACK)
    page.insert_text(fitz.Point(PAGE_W - MARGIN_R - 180, y + 28),
                     f"Order No: {data.get('order_number', '')}",
                     fontsize=FS_NORMAL, fontname="helv", color=COLOR_BLACK)
    y += meta_h

    # ── Seller ──
    sec_h = 50
    page.draw_rect(fitz.Rect(MARGIN_L, y, PAGE_W - MARGIN_R, y + sec_h),
                   color=COLOR_BORDER, width=0.3)
    sy = y + 12
    page.insert_text(fitz.Point(MARGIN_L + 8, sy), "SELLER",
                     fontsize=FS_TINY, fontname="hebo", color=COLOR_GRAY)
    sy += 12
    page.insert_text(fitz.Point(MARGIN_L + 8, sy),
                     data.get("seller_name", ""), fontsize=FS_NORMAL, fontname="hebo", color=COLOR_BLACK)
    sy += 12
    if data.get("seller_gstin"):
        page.insert_text(fitz.Point(MARGIN_L + 8, sy),
                         f"GSTIN: {data['seller_gstin']}", fontsize=FS_SMALL, fontname="helv", color=COLOR_BLACK)
        sy += 11
    if data.get("seller_address"):
        page.insert_text(fitz.Point(MARGIN_L + 8, sy),
                         data["seller_address"], fontsize=FS_SMALL, fontname="helv", color=COLOR_BLACK)
    y += sec_h

    # ── Buyer ──
    page.draw_rect(fitz.Rect(MARGIN_L, y, PAGE_W - MARGIN_R, y + sec_h),
                   color=COLOR_BORDER, width=0.3)
    by_ = y + 12
    page.insert_text(fitz.Point(MARGIN_L + 8, by_), "BUYER",
                     fontsize=FS_TINY, fontname="hebo", color=COLOR_GRAY)
    by_ += 12
    page.insert_text(fitz.Point(MARGIN_L + 8, by_),
                     data.get("buyer_name", ""), fontsize=FS_NORMAL, fontname="hebo", color=COLOR_BLACK)
    by_ += 12
    if data.get("buyer_gstin"):
        page.insert_text(fitz.Point(MARGIN_L + 8, by_),
                         f"GSTIN: {data['buyer_gstin']}", fontsize=FS_SMALL, fontname="helv", color=COLOR_BLACK)
        by_ += 11
    if data.get("buyer_address"):
        page.insert_text(fitz.Point(MARGIN_L + 8, by_),
                         data["buyer_address"], fontsize=FS_SMALL, fontname="helv", color=COLOR_BLACK)
    y += sec_h

    # ── Reason ──
    reason_h = 28
    page.draw_rect(fitz.Rect(MARGIN_L, y, PAGE_W - MARGIN_R, y + reason_h),
                   color=COLOR_BORDER, fill=COLOR_YELLOW_BG, width=0.3)
    page.insert_text(fitz.Point(MARGIN_L + 8, y + 18),
                     f"Reason: {data.get('reason', '')}",
                     fontsize=FS_NORMAL, fontname="hebo", color=COLOR_BLACK)
    y += reason_h

    # ── Totals ──
    y += 4
    page.draw_line(fitz.Point(MARGIN_L, y), fitz.Point(PAGE_W - MARGIN_R, y),
                   color=COLOR_DARK, width=1.5)
    y += 12

    totals_x_label = PAGE_W - MARGIN_R - 220
    totals_x_value = PAGE_W - MARGIN_R - 8

    def _draw_row(label, value, bold=False, color=COLOR_BLACK):
        nonlocal y
        fn = "hebo" if bold else "helv"
        fs = FS_NORMAL + 2 if bold else FS_NORMAL
        page.insert_text(fitz.Point(totals_x_label, y),
                         label, fontsize=fs, fontname=fn, color=color)
        val_str = value if isinstance(value, str) else _fmt(value)
        page.insert_text(fitz.Point(totals_x_value - len(val_str) * 4.5, y),
                         val_str, fontsize=fs, fontname="cour" if not bold else "cobo", color=color)
        y += 16 if bold else 14

    _draw_row("Subtotal:", data.get("subtotal", 0))

    cgst = data.get("cgst_amount", 0)
    sgst = data.get("sgst_amount", 0)
    igst = data.get("igst_amount", 0)
    if cgst and Decimal(str(cgst)) > 0:
        _draw_row("CGST:", cgst)
        _draw_row("SGST:", sgst)
    if igst and Decimal(str(igst)) > 0:
        _draw_row("IGST:", igst)

    y += 2
    page.draw_line(fitz.Point(totals_x_label - 10, y), fitz.Point(PAGE_W - MARGIN_R, y),
                   color=COLOR_RED, width=0.8)
    y += 10
    _draw_row("CREDIT AMOUNT:", f"{sym}{_fmt(data.get('total_amount', 0))}", bold=True, color=COLOR_RED)

    # ── Amount in Words ──
    y += 6
    page.draw_line(fitz.Point(MARGIN_L, y), fitz.Point(PAGE_W - MARGIN_R, y),
                   color=COLOR_BORDER, width=0.3)
    y += 14
    page.insert_text(fitz.Point(MARGIN_L + 8, y),
                     f"Amount in words: {data.get('amount_in_words', '')}",
                     fontsize=FS_SMALL, fontname="hebi", color=COLOR_GRAY)

    # ── Footer ──
    y += 18
    page.insert_text(fitz.Point(PAGE_W / 2 - 110, y),
                     "This is a computer-generated credit note. No signature required.",
                     fontsize=FS_TINY, fontname="helv", color=(0.6, 0.6, 0.6))

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# ———————————— Text Wrapping Helper ————————————

def _wrap_text(text: str, max_chars: int) -> list[str]:
    """Simple word-wrap by character count."""
    if not text:
        return []
    words = text.split()
    lines = []
    current = ""
    for w in words:
        if current and len(current) + 1 + len(w) > max_chars:
            lines.append(current)
            current = w
        else:
            current = f"{current} {w}".strip() if current else w
    if current:
        lines.append(current)
    return lines


# ———————————— Public API (same signatures as before) ————————————

def render_invoice_html(data: dict) -> str:
    """
    Kept for backward compatibility with invoice_service.py call chain.
    Returns a sentinel string — actual PDF is built in html_to_pdf().
    Data is stashed in the returned string as a marker.
    """
    # Stash data for html_to_pdf to pick up
    import json
    # We encode data to JSON, wrapping Decimals as strings
    def _default(o):
        if isinstance(o, Decimal):
            return str(o)
        if hasattr(o, 'isoformat'):
            return o.isoformat()
        return str(o)
    return "__INVOICE_PDF__" + json.dumps(data, default=_default)


def render_credit_note_html(data: dict) -> str:
    """Same backward-compat wrapper for credit notes."""
    import json
    def _default(o):
        if isinstance(o, Decimal):
            return str(o)
        if hasattr(o, 'isoformat'):
            return o.isoformat()
        return str(o)
    return "__CREDIT_NOTE_PDF__" + json.dumps(data, default=_default)


def html_to_pdf(html_content: str) -> bytes:
    """
    Convert to PDF. Detects whether this is an invoice or credit note
    from the sentinel prefix, then generates via PyMuPDF.
    """
    import json
    from decimal import Decimal as D

    if html_content.startswith("__INVOICE_PDF__"):
        raw = html_content[len("__INVOICE_PDF__"):]
        data = json.loads(raw, parse_float=lambda x: D(x))
        logger.info("PDF generated via PyMuPDF (invoice)")
        return _draw_invoice_pdf(data)

    if html_content.startswith("__CREDIT_NOTE_PDF__"):
        raw = html_content[len("__CREDIT_NOTE_PDF__"):]
        data = json.loads(raw, parse_float=lambda x: D(x))
        logger.info("PDF generated via PyMuPDF (credit note)")
        return _draw_credit_note_pdf(data)

    # Fallback: should not happen in normal flow
    raise RuntimeError(
        "html_to_pdf received unexpected content. "
        "Expected __INVOICE_PDF__ or __CREDIT_NOTE_PDF__ prefix."
    )


async def upload_pdf_to_s3(
    pdf_bytes: bytes,
    s3_key: str,
    bucket: str | None = None,
    content_type: str = "application/pdf",
) -> str:
    """
    Upload PDF to S3 and return the URL.
    Uses sync boto3 via asyncio.to_thread (boto3 is already installed).
    If S3 is not configured, saves to local /tmp and returns local path.
    """
    import asyncio

    if bucket is None:
        bucket = os.getenv("S3_BUCKET_NAME", "")

    if not bucket:
        # Local fallback: save to filesystem
        local_dir = Path("/tmp/invoices")
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / s3_key.replace("/", "_")
        local_path.write_bytes(pdf_bytes)
        logger.info(f"PDF saved locally: {local_path}")
        return str(local_path)

    try:
        import boto3

        def _sync_upload():
            s3 = boto3.client(
                "s3",
                region_name=os.getenv("AWS_REGION", "ap-south-1"),
            )
            s3.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=pdf_bytes,
                ContentType=content_type,
                CacheControl="max-age=31536000",
            )

        await asyncio.to_thread(_sync_upload)

        cdn_domain = os.getenv("CLOUDFRONT_DOMAIN", "")
        if cdn_domain:
            url = f"https://{cdn_domain}/{s3_key}"
        else:
            url = f"https://{bucket}.s3.amazonaws.com/{s3_key}"

        logger.info(f"PDF uploaded to S3: {url}")
        return url

    except Exception as e:
        logger.error(f"S3 upload failed: {e}, saving locally")
        local_dir = Path("/tmp/invoices")
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / s3_key.replace("/", "_")
        local_path.write_bytes(pdf_bytes)
        return str(local_path)
