"""
Number to Indian Rupees words converter.
Used in GST invoice PDF: "Amount in words: Four Thousand Six Hundred Ninety-Seven Rupees Only"
"""

from decimal import Decimal

_ONES = [
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
    "Seventeen", "Eighteen", "Nineteen",
]

_TENS = [
    "", "", "Twenty", "Thirty", "Forty", "Fifty",
    "Sixty", "Seventy", "Eighty", "Ninety",
]


def _two_digit_words(n: int) -> str:
    if n < 20:
        return _ONES[n]
    ten, one = divmod(n, 10)
    return f"{_TENS[ten]} {_ONES[one]}".strip()


def _indian_number_words(n: int) -> str:
    """Convert integer to Indian numbering words (lakhs/crores)."""
    if n == 0:
        return "Zero"

    parts = []

    # Crores (10,000,000+)
    if n >= 10_000_000:
        crores = n // 10_000_000
        parts.append(f"{_indian_number_words(crores)} Crore")
        n %= 10_000_000

    # Lakhs (100,000+)
    if n >= 100_000:
        lakhs = n // 100_000
        parts.append(f"{_two_digit_words(lakhs)} Lakh")
        n %= 100_000

    # Thousands (1,000+)
    if n >= 1_000:
        thousands = n // 1_000
        parts.append(f"{_two_digit_words(thousands)} Thousand")
        n %= 1_000

    # Hundreds
    if n >= 100:
        hundreds = n // 100
        parts.append(f"{_ONES[hundreds]} Hundred")
        n %= 100

    # Tens and ones
    if n > 0:
        parts.append(_two_digit_words(n))

    return " ".join(parts)


def amount_in_words(amount: Decimal | float | int, currency: str = "INR") -> str:
    """
    Convert numeric amount to words for invoice display.

    Examples:
        amount_in_words(4697)    → "Four Thousand Six Hundred Ninety Seven Rupees Only"
        amount_in_words(4697.50) → "Four Thousand Six Hundred Ninety Seven Rupees and Fifty Paise Only"
        amount_in_words(100, "USD") → "One Hundred Dollars Only"
    """
    amt = Decimal(str(amount))
    rupees = int(amt)
    paise = int((amt - rupees) * 100)

    if currency == "INR":
        main_unit = "Rupees"
        sub_unit = "Paise"
    elif currency == "USD":
        main_unit = "Dollars"
        sub_unit = "Cents"
    elif currency == "EUR":
        main_unit = "Euros"
        sub_unit = "Cents"
    elif currency == "GBP":
        main_unit = "Pounds"
        sub_unit = "Pence"
    else:
        main_unit = currency
        sub_unit = f"sub-{currency}"

    words = _indian_number_words(rupees)

    if paise > 0:
        paise_words = _two_digit_words(paise)
        return f"{words} {main_unit} and {paise_words} {sub_unit} Only"
    else:
        return f"{words} {main_unit} Only"
