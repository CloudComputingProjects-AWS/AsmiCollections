"""
A compatibility wrapper so the repo has one canonical path
"""

from app.core.encryption import (
    EncryptedText,
    decrypt_pii,
    encrypt_pii,
    encrypt_pii_if_needed,
    generate_encryption_key,
    is_encrypted_pii,
)

PII_FIELDS = {
    "users": ["phone"],
    "user_addresses": ["phone", "address_line_1", "address_line_2"],
}

