"""
Invoice Sequence Service — Atomic, gap-free invoice/credit-note numbering.
Phase 9 — V2.5 Blueprint

Uses SELECT FOR UPDATE + atomic increment to guarantee sequential,
gap-free numbering per financial year (GST requirement).

India Financial Year: April to March (e.g., FY 2025-26 = Apr 2025 → Mar 2026)
"""

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def get_current_financial_year() -> str:
    """
    Returns the current Indian financial year string.
    April–March cycle. E.g., if today is Feb 2026 → '2025-26'.
    """
    now = datetime.now(timezone.utc)
    year = now.year
    month = now.month
    if month >= 4:
        return f"{year}-{str(year + 1)[2:]}"
    else:
        return f"{year - 1}-{str(year)[2:]}"


async def get_next_invoice_number(
    db: AsyncSession,
    document_type: str = "invoice",
    financial_year: str | None = None,
) -> str:
    """
    Atomically generates the next invoice or credit note number.

    Returns:
        'INV-2026-00042' for invoices
        'CN-2026-00003'  for credit notes

    Uses UPDATE ... RETURNING for atomicity. Row-level lock ensures
    no two concurrent transactions get the same number.
    """
    if financial_year is None:
        financial_year = get_current_financial_year()

    # Atomic increment with row-level lock
    result = await db.execute(
        text("""
            UPDATE invoice_sequences
            SET last_number = last_number + 1
            WHERE financial_year = :fy AND document_type = :doc_type
            RETURNING last_number
        """),
        {"fy": financial_year, "doc_type": document_type},
    )
    row = result.fetchone()

    if row is None:
        # Sequence row doesn't exist — create it (first use of this FY)
        await db.execute(
            text("""
                INSERT INTO invoice_sequences (id, financial_year, document_type, last_number)
                VALUES (gen_random_uuid(), :fy, :doc_type, 1)
                ON CONFLICT (financial_year, document_type)
                DO UPDATE SET last_number = invoice_sequences.last_number + 1
            """),
            {"fy": financial_year, "doc_type": document_type},
        )
        result = await db.execute(
            text("""
                SELECT last_number FROM invoice_sequences
                WHERE financial_year = :fy AND document_type = :doc_type
            """),
            {"fy": financial_year, "doc_type": document_type},
        )
        row = result.fetchone()

    seq_number = row[0]

    # Extract calendar year from FY for the prefix
    # FY '2025-26' → use '2026' (current year in most cases)
    fy_parts = financial_year.split("-")
    year_suffix = fy_parts[0] if len(fy_parts) == 2 else financial_year[:4]
    # Use the start year + 1 for April-onwards convention, or just use actual year
    now = datetime.now(timezone.utc)
    display_year = str(now.year)

    if document_type == "invoice":
        return f"INV-{display_year}-{seq_number:05d}"
    elif document_type == "credit_note":
        return f"CN-{display_year}-{seq_number:05d}"
    else:
        return f"DOC-{display_year}-{seq_number:05d}"
