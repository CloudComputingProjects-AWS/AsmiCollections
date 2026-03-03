"""
Ashmi Store Ã¢â‚¬â€ Test Data Seed Script v3
=======================================
Verified against actual backend schemas on 2026-02-20.

Schema sources checked:
  - app/schemas/auth.py Ã¢â€ â€™ UserRegisterRequest, UserLoginRequest
  - app/schemas/product.py Ã¢â€ â€™ CategoryCreate, ProductCreate, ProductVariantInline, VariantCreate
  - app/schemas/cart_coupon.py Ã¢â€ â€™ CouponCreate
  - app/api/v1/endpoints/admin_products.py Ã¢â€ â€™ route prefixes, endpoint signatures
  - app/api/v1/endpoints/cart_coupons.py Ã¢â€ â€™ admin_coupon_router prefix="/admin/coupons"

Creates:
  - 1 test customer account
  - 8 attribute definitions
  - 5 parent + 14 subcategories = 19 categories
  - 20 products with ~100 variants
  - 2 coupons (WELCOME10, FLAT200)
"""

import json
import re
import sys
from datetime import datetime, timedelta, timezone

import requests

# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# CONFIGURATION
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

BASE_URL = "http://127.0.0.1:8000/api/v1"
ADMIN_EMAIL = "admin@yourstore.com"
ADMIN_PASSWORD = "Admin@123"
CUSTOMER_EMAIL = "pc_soumyendu@yahoo.co.in"
CUSTOMER_PASSWORD = "123India"

admin_token = None
customer_token = None


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# HELPERS
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

def ok(msg):
    print(f"  \u2705 {msg}")

def skip(msg):
    print(f"  \u23ed\ufe0f  {msg}")

def fail(msg):
    print(f"  \u274c {msg}")

def slugify(text):
    """Convert text to URL-safe slug matching pattern ^[a-z0-9-]+$"""
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def login(email, password):
    """Login and return (token, response_data) or (None, error_data)."""
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": password,
    })
    if resp.status_code == 200:
        data = resp.json()
        token = data.get("access_token") or data.get("token")
        if not token:
            token = resp.cookies.get("access_token")
        return token, data
    return None, resp.json()


def admin_headers():
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


def customer_headers():
    return {"Authorization": f"Bearer {customer_token}", "Content-Type": "application/json"}


def api_post(path, payload, headers=None):
    h = headers or admin_headers()
    resp = requests.post(f"{BASE_URL}{path}", json=payload, headers=h)
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, {"raw": resp.text[:500]}


def api_get(path, headers=None, params=None):
    h = headers or admin_headers()
    resp = requests.get(f"{BASE_URL}{path}", headers=h, params=params)
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, {"raw": resp.text[:500]}


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# STEP 1: Admin Login
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

def step1_admin_login():
    global admin_token
    print("\n[STEP 1] Logging in as admin...")
    token, data = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    if token:
        admin_token = token
        ok(f"Admin logged in (token: {token[:25]}...)")
    else:
        fail(f"Admin login failed: {data}")
        print("  Make sure you ran: python -m app.utils.seed")
        sys.exit(1)


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# STEP 2: Register Test Customer
# Schema: UserRegisterRequest
#   email: EmailStr (required)
#   password: str 8-128 (required)
#   first_name: str 1-100 (required)
#   last_name: str 1-100 (required)
#   phone: str|None
#   country_code: str|None
#   terms_accepted: bool (required, must be True)
#   privacy_accepted: bool (required, must be True)
#   marketing_email: bool = False
#   marketing_sms: bool = False
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

def step2_register_customer():
    global customer_token
    print("\n[STEP 2] Registering test customer...")

    payload = {
        "email": CUSTOMER_EMAIL,
        "password": CUSTOMER_PASSWORD,
        "first_name": "Test",
        "last_name": "Customer",
        "terms_accepted": True,
        "privacy_accepted": True,
        "marketing_email": False,
        "marketing_sms": False,
    }
    status, data = api_post("/auth/register", payload, headers={"Content-Type": "application/json"})

    if status in [200, 201]:
        ok(f"Customer registered: {CUSTOMER_EMAIL}")
    elif status in [400, 409]:
        skip(f"Customer already exists or validation issue: {data.get('detail', data)}")
    else:
        fail(f"Registration: {status} Ã¢â‚¬â€ {data}")

    # Login as customer
    token, _ = login(CUSTOMER_EMAIL, CUSTOMER_PASSWORD)
    if token:
        customer_token = token
        ok("Customer logged in")
    else:
        skip("Customer login failed Ã¢â‚¬â€ may need email verification")


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# STEP 3: Attribute Definitions
# Schema: AttributeDefinitionCreate
#   attribute_key: str max50 pattern ^[a-z_]+$ (required)
#   display_name: str max100 (required)
#   input_type: str pattern ^(text|select|multiselect)$ (required)
#   options: list[str]|None
#   is_filterable: bool = False
#   is_required: bool = False
#   sort_order: int = 0
#   category_ids: list[UUID]|None
# Route: POST /api/v1/admin/attribute-definitions
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

ATTRIBUTES = [
    {"attribute_key": "material", "display_name": "Material", "input_type": "select",
     "options": ["Cotton", "Polyester", "Silk", "Linen", "Denim", "Wool", "Rayon", "Chiffon", "Georgette", "Crepe", "Nylon", "Fleece"],
     "is_filterable": True, "is_required": False, "sort_order": 1},
    {"attribute_key": "fit", "display_name": "Fit", "input_type": "select",
     "options": ["Regular", "Slim", "Relaxed", "Oversized", "Tailored", "A-Line", "Straight"],
     "is_filterable": True, "is_required": False, "sort_order": 2},
    {"attribute_key": "sleeve", "display_name": "Sleeve", "input_type": "select",
     "options": ["Full Sleeve", "Half Sleeve", "Sleeveless", "3/4 Sleeve", "Cap Sleeve", "Rolled-Up", "Flutter"],
     "is_filterable": True, "is_required": False, "sort_order": 3},
    {"attribute_key": "neck", "display_name": "Neck Type", "input_type": "select",
     "options": ["Crew Neck", "V-Neck", "Round Neck", "Collar", "Mandarin", "Henley", "Hooded", "Boat Neck", "Square Neck"],
     "is_filterable": True, "is_required": False, "sort_order": 4},
    {"attribute_key": "pattern", "display_name": "Pattern", "input_type": "select",
     "options": ["Solid", "Striped", "Checked", "Printed", "Floral", "Graphic", "Abstract", "Polka Dot", "Embroidered", "Geometric"],
     "is_filterable": True, "is_required": False, "sort_order": 5},
    {"attribute_key": "occasion", "display_name": "Occasion", "input_type": "multiselect",
     "options": ["Casual", "Formal", "Party", "Lounge", "Sports", "Festive", "Office", "Beach", "Wedding"],
     "is_filterable": True, "is_required": False, "sort_order": 6},
    {"attribute_key": "season", "display_name": "Season", "input_type": "multiselect",
     "options": ["Summer", "Winter", "Monsoon", "All Season", "Spring"],
     "is_filterable": True, "is_required": False, "sort_order": 7},
    {"attribute_key": "wash_care", "display_name": "Wash Care", "input_type": "text",
     "options": None, "is_filterable": False, "is_required": False, "sort_order": 8},
]


def step3_seed_attributes():
    print("\n[STEP 3] Seeding attribute definitions...")
    status, existing = api_get("/admin/attribute-definitions")
    if status == 200 and isinstance(existing, list) and len(existing) >= 8:
        skip(f"{len(existing)} attributes already exist")
        return

    for attr in ATTRIBUTES:
        s, d = api_post("/admin/attribute-definitions", attr)
        if s in [200, 201]:
            ok(f"Attribute: {attr['display_name']}")
        elif s in [400, 409]:
            skip(f"Attribute exists: {attr['attribute_key']}")
        else:
            fail(f"Attribute '{attr['attribute_key']}': {s} Ã¢â‚¬â€ {d}")


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# STEP 4: Categories
# Schema: CategoryCreate
#   name: str max100 (required)
#   slug: str max100 pattern ^[a-z0-9-]+$ (required)
#   gender: str (REQUIRED Ã¢â‚¬â€ even for subcategories)
#   age_group: str (REQUIRED Ã¢â‚¬â€ even for subcategories)
#   parent_id: UUID|None
#   image_url: str|None
#   sort_order: int = 0
#   is_active: bool = True
# Route: POST /api/v1/admin/categories
#
# NOTE: CategoryCreate schema requires gender and age_group as mandatory
# fields on ALL categories including subcategories.
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

PARENT_CATEGORIES = [
    {"name": "Men", "slug": "men", "gender": "men", "age_group": "adult", "sort_order": 1},
    {"name": "Women", "slug": "women", "gender": "women", "age_group": "adult", "sort_order": 2},
    {"name": "Boys", "slug": "boys", "gender": "boys", "age_group": "kids", "sort_order": 3},
    {"name": "Girls", "slug": "girls", "gender": "girls", "age_group": "kids", "sort_order": 4},
    {"name": "Unisex", "slug": "unisex", "gender": "unisex", "age_group": "adult", "sort_order": 5},
]

SUBCATEGORIES = [
    {"parent_slug": "men", "name": "T-Shirts", "slug": "men-tshirts", "gender": "men", "age_group": "adult", "sort_order": 1},
    {"parent_slug": "men", "name": "Shirts", "slug": "men-shirts", "gender": "men", "age_group": "adult", "sort_order": 2},
    {"parent_slug": "men", "name": "Jeans", "slug": "men-jeans", "gender": "men", "age_group": "adult", "sort_order": 3},
    {"parent_slug": "men", "name": "Trousers", "slug": "men-trousers", "gender": "men", "age_group": "adult", "sort_order": 4},
    {"parent_slug": "women", "name": "Tops", "slug": "women-tops", "gender": "women", "age_group": "adult", "sort_order": 1},
    {"parent_slug": "women", "name": "Dresses", "slug": "women-dresses", "gender": "women", "age_group": "adult", "sort_order": 2},
    {"parent_slug": "women", "name": "Kurtis", "slug": "women-kurtis", "gender": "women", "age_group": "adult", "sort_order": 3},
    {"parent_slug": "women", "name": "Jeans", "slug": "women-jeans", "gender": "women", "age_group": "adult", "sort_order": 4},
    {"parent_slug": "boys", "name": "T-Shirts", "slug": "boys-tshirts", "gender": "boys", "age_group": "kids", "sort_order": 1},
    {"parent_slug": "boys", "name": "Shorts", "slug": "boys-shorts", "gender": "boys", "age_group": "kids", "sort_order": 2},
    {"parent_slug": "girls", "name": "Frocks", "slug": "girls-frocks", "gender": "girls", "age_group": "kids", "sort_order": 1},
    {"parent_slug": "girls", "name": "Tops", "slug": "girls-tops", "gender": "girls", "age_group": "kids", "sort_order": 2},
    {"parent_slug": "unisex", "name": "Hoodies", "slug": "unisex-hoodies", "gender": "unisex", "age_group": "adult", "sort_order": 1},
    {"parent_slug": "unisex", "name": "Jackets", "slug": "unisex-jackets", "gender": "unisex", "age_group": "adult", "sort_order": 2},
]


def step4_create_categories():
    print("\n[STEP 4] Creating categories...")
    parent_map = {}  # slug -> id

    # Create parents
    for cat in PARENT_CATEGORIES:
        payload = {
            "name": cat["name"],
            "slug": cat["slug"],
            "gender": cat["gender"],
            "age_group": cat["age_group"],
            "sort_order": cat["sort_order"],
        }
        s, d = api_post("/admin/categories", payload)
        if s in [200, 201]:
            parent_map[cat["slug"]] = d.get("id")
            ok(f"Category: {cat['name']}")
        elif s in [400, 409]:
            skip(f"Category exists: {cat['name']}")
        else:
            fail(f"Category '{cat['name']}': {s} Ã¢â‚¬â€ {d}")

    # Fetch all to build complete slug->id map (catches pre-existing)
    status, all_cats = api_get("/admin/categories")
    if status == 200 and isinstance(all_cats, list):
        for c in all_cats:
            slug = c.get("slug", "")
            if slug:
                parent_map[slug] = c.get("id")

    # Create subcategories
    for sub in SUBCATEGORIES:
        parent_id = parent_map.get(sub["parent_slug"])
        if not parent_id:
            fail(f"Parent '{sub['parent_slug']}' not found for {sub['name']}")
            continue
        payload = {
            "name": sub["name"],
            "slug": sub["slug"],
            "gender": sub["gender"],
            "age_group": sub["age_group"],
            "parent_id": str(parent_id),
            "sort_order": sub["sort_order"],
        }
        s, d = api_post("/admin/categories", payload)
        if s in [200, 201]:
            parent_map[sub["slug"]] = d.get("id")
            ok(f"  Subcategory: {sub['parent_slug']} -> {sub['name']}")
        elif s in [400, 409]:
            skip(f"  Subcategory exists: {sub['slug']}")
        else:
            fail(f"  Subcategory '{sub['name']}': {s} Ã¢â‚¬â€ {d}")

    return parent_map


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# STEP 5: Products with Variants
#
# Schema: ProductCreate
#   title: str max500 (required)
#   slug: str max500 pattern ^[a-z0-9-]+$ (REQUIRED)
#   description: str|None
#   category_id: UUID (REQUIRED)
#   brand: str|None max200
#   base_price: Decimal >0 (required)
#   sale_price: Decimal|None >=0
#   hsn_code: str|None max20
#   gst_rate: Decimal >=0 default 0
#   tags: list[str]|None
#   attributes: dict default {}
#   is_active: bool = True
#   is_featured: bool = False
#   meta_title: str|None max200
#   meta_description: str|None max500
#
# Schema: ProductVariantInline (for inline creation)
#   size: str|None max20
#   color: str|None max50
#   color_hex: str|None max7 pattern ^#[0-9A-Fa-f]{6}$
#   sku: str|None max100 (auto-gen if null)
#   stock_quantity: int >=0 default 0
#   price_override: Decimal|None >=0
#   weight_grams: int|None >=0
#   is_active: bool = True
#
# Route: POST /api/v1/admin/products
# Signature: create_product(data: ProductCreate, variants: list[ProductVariantInline] | None = None)
# FastAPI with 2 body params expects: {"data": {...}, "variants": [...]}
#
# Fallback: POST /api/v1/admin/variants
# Schema: VariantCreate (requires product_id: UUID in body)
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

PRODUCTS = [
    # Ã¢â€â‚¬Ã¢â€â‚¬ Men's T-Shirts Ã¢â€â‚¬Ã¢â€â‚¬
    {
        "title": "Classic Cotton Crew Neck T-Shirt",
        "description": "Premium 100% cotton crew neck t-shirt. Breathable and comfortable for everyday wear.",
        "brand": "Ashmi Basics", "base_price": 799, "sale_price": 599,
        "hsn_code": "6109", "gst_rate": 5, "category_slug": "men-tshirts",
        "is_active": True, "is_featured": True,
        "attributes": {"material": "Cotton", "fit": "Regular", "sleeve": "Half Sleeve", "neck": "Crew Neck", "pattern": "Solid", "occasion": ["Casual", "Lounge"], "season": ["All Season"], "wash_care": "Machine wash cold, tumble dry low"},
        "variants": [
            {"size": "S", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 50, "weight_grams": 180},
            {"size": "M", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 80, "weight_grams": 190},
            {"size": "L", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 60, "weight_grams": 200},
            {"size": "XL", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 40, "weight_grams": 210},
            {"size": "S", "color": "Black", "color_hex": "#000000", "stock_quantity": 45, "weight_grams": 180},
            {"size": "M", "color": "Black", "color_hex": "#000000", "stock_quantity": 75, "weight_grams": 190},
            {"size": "L", "color": "Black", "color_hex": "#000000", "stock_quantity": 55, "weight_grams": 200},
            {"size": "M", "color": "Navy", "color_hex": "#1B1F3B", "stock_quantity": 60, "weight_grams": 190},
            {"size": "L", "color": "Navy", "color_hex": "#1B1F3B", "stock_quantity": 45, "weight_grams": 200},
        ],
    },
    {
        "title": "Graphic Print Urban T-Shirt",
        "description": "Bold graphic print t-shirt with soft hand feel.",
        "brand": "Ashmi Street", "base_price": 999, "sale_price": 749,
        "hsn_code": "6109", "gst_rate": 5, "category_slug": "men-tshirts",
        "is_active": True, "is_featured": False,
        "attributes": {"material": "Cotton", "fit": "Regular", "sleeve": "Half Sleeve", "neck": "Round Neck", "pattern": "Graphic", "occasion": ["Casual"], "season": ["All Season"], "wash_care": "Machine wash cold, do not bleach"},
        "variants": [
            {"size": "S", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 35, "weight_grams": 185},
            {"size": "M", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 60, "weight_grams": 195},
            {"size": "L", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 50, "weight_grams": 205},
            {"size": "M", "color": "Charcoal", "color_hex": "#36454F", "stock_quantity": 40, "weight_grams": 195},
            {"size": "L", "color": "Charcoal", "color_hex": "#36454F", "stock_quantity": 35, "weight_grams": 205},
        ],
    },
    {
        "title": "Polo T-Shirt Classic",
        "description": "Classic polo t-shirt with contrast collar. Pique cotton fabric.",
        "brand": "Ashmi Basics", "base_price": 1199, "sale_price": 899,
        "hsn_code": "6109", "gst_rate": 12, "category_slug": "men-tshirts",
        "is_active": True, "is_featured": True,
        "attributes": {"material": "Cotton", "fit": "Regular", "sleeve": "Half Sleeve", "neck": "Collar", "pattern": "Solid", "occasion": ["Casual", "Office"], "season": ["All Season"], "wash_care": "Machine wash cold"},
        "variants": [
            {"size": "M", "color": "Navy", "color_hex": "#1B1F3B", "stock_quantity": 55, "weight_grams": 210},
            {"size": "L", "color": "Navy", "color_hex": "#1B1F3B", "stock_quantity": 45, "weight_grams": 220},
            {"size": "XL", "color": "Navy", "color_hex": "#1B1F3B", "stock_quantity": 30, "weight_grams": 230},
            {"size": "M", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 50, "weight_grams": 210},
            {"size": "L", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 40, "weight_grams": 220},
        ],
    },
    # Ã¢â€â‚¬Ã¢â€â‚¬ Men's Shirts Ã¢â€â‚¬Ã¢â€â‚¬
    {
        "title": "Oxford Button-Down Formal Shirt",
        "description": "Classic Oxford weave button-down shirt for office and formal occasions.",
        "brand": "Ashmi Formals", "base_price": 1899, "sale_price": 1499,
        "hsn_code": "6205", "gst_rate": 12, "category_slug": "men-shirts",
        "is_active": True, "is_featured": True,
        "attributes": {"material": "Cotton", "fit": "Slim", "sleeve": "Full Sleeve", "neck": "Collar", "pattern": "Solid", "occasion": ["Formal", "Office"], "season": ["All Season"], "wash_care": "Machine wash, iron on medium heat"},
        "variants": [
            {"size": "S", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 30, "weight_grams": 220},
            {"size": "M", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 50, "weight_grams": 235},
            {"size": "L", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 40, "weight_grams": 250},
            {"size": "M", "color": "Light Blue", "color_hex": "#ADD8E6", "stock_quantity": 45, "weight_grams": 235},
            {"size": "L", "color": "Light Blue", "color_hex": "#ADD8E6", "stock_quantity": 35, "weight_grams": 250},
        ],
    },
    {
        "title": "Check Pattern Casual Shirt",
        "description": "Comfortable checked shirt for casual outings.",
        "brand": "Ashmi Casual", "base_price": 1499, "sale_price": 1199,
        "hsn_code": "6205", "gst_rate": 12, "category_slug": "men-shirts",
        "is_active": True, "is_featured": False,
        "attributes": {"material": "Cotton", "fit": "Regular", "sleeve": "Full Sleeve", "neck": "Collar", "pattern": "Checked", "occasion": ["Casual"], "season": ["All Season"], "wash_care": "Machine wash cold"},
        "variants": [
            {"size": "M", "color": "Red", "color_hex": "#C41E3A", "stock_quantity": 40, "weight_grams": 230},
            {"size": "L", "color": "Red", "color_hex": "#C41E3A", "stock_quantity": 35, "weight_grams": 245},
            {"size": "M", "color": "Blue", "color_hex": "#4169E1", "stock_quantity": 45, "weight_grams": 230},
            {"size": "L", "color": "Blue", "color_hex": "#4169E1", "stock_quantity": 30, "weight_grams": 245},
        ],
    },
    {
        "title": "Linen Summer Shirt",
        "description": "Lightweight linen shirt perfect for hot Indian summers.",
        "brand": "Ashmi Casual", "base_price": 1799, "sale_price": 1399,
        "hsn_code": "6205", "gst_rate": 12, "category_slug": "men-shirts",
        "is_active": True, "is_featured": False,
        "attributes": {"material": "Linen", "fit": "Regular", "sleeve": "Full Sleeve", "neck": "Collar", "pattern": "Solid", "occasion": ["Casual", "Beach"], "season": ["Summer"], "wash_care": "Hand wash, line dry, iron on low"},
        "variants": [
            {"size": "M", "color": "Beige", "color_hex": "#F5F5DC", "stock_quantity": 30, "weight_grams": 180},
            {"size": "L", "color": "Beige", "color_hex": "#F5F5DC", "stock_quantity": 25, "weight_grams": 190},
            {"size": "M", "color": "Sky Blue", "color_hex": "#87CEEB", "stock_quantity": 35, "weight_grams": 180},
            {"size": "L", "color": "Sky Blue", "color_hex": "#87CEEB", "stock_quantity": 25, "weight_grams": 190},
        ],
    },
    # Ã¢â€â‚¬Ã¢â€â‚¬ Men's Jeans Ã¢â€â‚¬Ã¢â€â‚¬
    {
        "title": "Slim Fit Dark Wash Jeans",
        "description": "Classic slim fit jeans in dark wash. Stretch denim for comfort.",
        "brand": "Ashmi Denim", "base_price": 1999, "sale_price": 1599,
        "hsn_code": "6204", "gst_rate": 12, "category_slug": "men-jeans",
        "is_active": True, "is_featured": True,
        "attributes": {"material": "Denim", "fit": "Slim", "pattern": "Solid", "occasion": ["Casual"], "season": ["All Season"], "wash_care": "Machine wash cold, turn inside out"},
        "variants": [
            {"size": "30", "color": "Dark Blue", "color_hex": "#00008B", "stock_quantity": 40, "weight_grams": 450},
            {"size": "32", "color": "Dark Blue", "color_hex": "#00008B", "stock_quantity": 55, "weight_grams": 470},
            {"size": "34", "color": "Dark Blue", "color_hex": "#00008B", "stock_quantity": 45, "weight_grams": 490},
            {"size": "36", "color": "Dark Blue", "color_hex": "#00008B", "stock_quantity": 30, "weight_grams": 510},
            {"size": "32", "color": "Black", "color_hex": "#000000", "stock_quantity": 40, "weight_grams": 470},
            {"size": "34", "color": "Black", "color_hex": "#000000", "stock_quantity": 35, "weight_grams": 490},
        ],
    },
    # Ã¢â€â‚¬Ã¢â€â‚¬ Men's Trousers Ã¢â€â‚¬Ã¢â€â‚¬
    {
        "title": "Chino Stretch Trousers",
        "description": "Smart chino trousers with stretch for all-day comfort.",
        "brand": "Ashmi Formals", "base_price": 1699, "sale_price": 1299,
        "hsn_code": "6204", "gst_rate": 12, "category_slug": "men-trousers",
        "is_active": True, "is_featured": False,
        "attributes": {"material": "Cotton", "fit": "Slim", "pattern": "Solid", "occasion": ["Office", "Casual"], "season": ["All Season"], "wash_care": "Machine wash cold, tumble dry low"},
        "variants": [
            {"size": "30", "color": "Khaki", "color_hex": "#C3B091", "stock_quantity": 35, "weight_grams": 380},
            {"size": "32", "color": "Khaki", "color_hex": "#C3B091", "stock_quantity": 50, "weight_grams": 400},
            {"size": "34", "color": "Khaki", "color_hex": "#C3B091", "stock_quantity": 40, "weight_grams": 420},
            {"size": "32", "color": "Navy", "color_hex": "#1B1F3B", "stock_quantity": 45, "weight_grams": 400},
            {"size": "34", "color": "Navy", "color_hex": "#1B1F3B", "stock_quantity": 35, "weight_grams": 420},
        ],
    },
    # Ã¢â€â‚¬Ã¢â€â‚¬ Women's Tops Ã¢â€â‚¬Ã¢â€â‚¬
    {
        "title": "Floral Print Summer Top",
        "description": "Lightweight floral print top for summer.",
        "brand": "Ashmi Women", "base_price": 899, "sale_price": 699,
        "hsn_code": "6106", "gst_rate": 5, "category_slug": "women-tops",
        "is_active": True, "is_featured": True,
        "attributes": {"material": "Rayon", "fit": "Regular", "sleeve": "Cap Sleeve", "neck": "Round Neck", "pattern": "Floral", "occasion": ["Casual"], "season": ["Summer"], "wash_care": "Hand wash, line dry"},
        "variants": [
            {"size": "XS", "color": "Pink", "color_hex": "#FFB6C1", "stock_quantity": 30, "weight_grams": 120},
            {"size": "S", "color": "Pink", "color_hex": "#FFB6C1", "stock_quantity": 50, "weight_grams": 125},
            {"size": "M", "color": "Pink", "color_hex": "#FFB6C1", "stock_quantity": 45, "weight_grams": 130},
            {"size": "L", "color": "Pink", "color_hex": "#FFB6C1", "stock_quantity": 30, "weight_grams": 135},
            {"size": "S", "color": "Yellow", "color_hex": "#FFD700", "stock_quantity": 35, "weight_grams": 125},
            {"size": "M", "color": "Yellow", "color_hex": "#FFD700", "stock_quantity": 40, "weight_grams": 130},
        ],
    },
    {
        "title": "Striped Knit Crop Top",
        "description": "Trendy striped crop top in soft knit.",
        "brand": "Ashmi Street", "base_price": 799, "sale_price": 599,
        "hsn_code": "6106", "gst_rate": 5, "category_slug": "women-tops",
        "is_active": True, "is_featured": False,
        "attributes": {"material": "Cotton", "fit": "Regular", "sleeve": "Half Sleeve", "neck": "Round Neck", "pattern": "Striped", "occasion": ["Casual", "Party"], "season": ["Summer", "Spring"], "wash_care": "Hand wash cold"},
        "variants": [
            {"size": "XS", "color": "Black-White", "color_hex": "#000000", "stock_quantity": 25, "weight_grams": 110},
            {"size": "S", "color": "Black-White", "color_hex": "#000000", "stock_quantity": 40, "weight_grams": 115},
            {"size": "M", "color": "Black-White", "color_hex": "#000000", "stock_quantity": 35, "weight_grams": 120},
            {"size": "S", "color": "Red-White", "color_hex": "#C41E3A", "stock_quantity": 30, "weight_grams": 115},
            {"size": "M", "color": "Red-White", "color_hex": "#C41E3A", "stock_quantity": 25, "weight_grams": 120},
        ],
    },
    # Ã¢â€â‚¬Ã¢â€â‚¬ Women's Dresses Ã¢â€â‚¬Ã¢â€â‚¬
    {
        "title": "Elegant Midi Wrap Dress",
        "description": "Stunning midi wrap dress with self-tie belt.",
        "brand": "Ashmi Luxe", "base_price": 2499, "sale_price": 1999,
        "hsn_code": "6204", "gst_rate": 12, "category_slug": "women-dresses",
        "is_active": True, "is_featured": True,
        "attributes": {"material": "Georgette", "fit": "A-Line", "sleeve": "3/4 Sleeve", "neck": "V-Neck", "pattern": "Solid", "occasion": ["Party", "Festive"], "season": ["All Season"], "wash_care": "Dry clean recommended"},
        "variants": [
            {"size": "S", "color": "Burgundy", "color_hex": "#800020", "stock_quantity": 20, "weight_grams": 250},
            {"size": "M", "color": "Burgundy", "color_hex": "#800020", "stock_quantity": 30, "weight_grams": 260},
            {"size": "L", "color": "Burgundy", "color_hex": "#800020", "stock_quantity": 25, "weight_grams": 270},
            {"size": "M", "color": "Emerald", "color_hex": "#50C878", "stock_quantity": 25, "weight_grams": 260},
            {"size": "L", "color": "Emerald", "color_hex": "#50C878", "stock_quantity": 20, "weight_grams": 270},
        ],
    },
    # Ã¢â€â‚¬Ã¢â€â‚¬ Women's Kurtis Ã¢â€â‚¬Ã¢â€â‚¬
    {
        "title": "Embroidered Cotton Kurti",
        "description": "Beautiful hand-embroidered cotton kurti.",
        "brand": "Ashmi Ethnic", "base_price": 1299, "sale_price": 999,
        "hsn_code": "6211", "gst_rate": 12, "category_slug": "women-kurtis",
        "is_active": True, "is_featured": True,
        "attributes": {"material": "Cotton", "fit": "A-Line", "sleeve": "3/4 Sleeve", "neck": "Mandarin", "pattern": "Embroidered", "occasion": ["Casual", "Festive", "Office"], "season": ["All Season"], "wash_care": "Hand wash, do not wring"},
        "variants": [
            {"size": "S", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 30, "weight_grams": 200},
            {"size": "M", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 45, "weight_grams": 210},
            {"size": "L", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 35, "weight_grams": 220},
            {"size": "XL", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 25, "weight_grams": 230},
            {"size": "M", "color": "Yellow", "color_hex": "#FFD700", "stock_quantity": 30, "weight_grams": 210},
            {"size": "L", "color": "Yellow", "color_hex": "#FFD700", "stock_quantity": 25, "weight_grams": 220},
        ],
    },
    {
        "title": "Silk Blend Festive Kurti",
        "description": "Luxurious silk blend kurti with zari work.",
        "brand": "Ashmi Ethnic", "base_price": 2299, "sale_price": 1799,
        "hsn_code": "6211", "gst_rate": 12, "category_slug": "women-kurtis",
        "is_active": True, "is_featured": False,
        "attributes": {"material": "Silk", "fit": "Straight", "sleeve": "3/4 Sleeve", "neck": "V-Neck", "pattern": "Embroidered", "occasion": ["Festive", "Wedding"], "season": ["All Season"], "wash_care": "Dry clean only"},
        "variants": [
            {"size": "S", "color": "Maroon", "color_hex": "#800000", "stock_quantity": 15, "weight_grams": 280},
            {"size": "M", "color": "Maroon", "color_hex": "#800000", "stock_quantity": 25, "weight_grams": 290},
            {"size": "L", "color": "Maroon", "color_hex": "#800000", "stock_quantity": 20, "weight_grams": 300},
            {"size": "M", "color": "Royal Blue", "color_hex": "#4169E1", "stock_quantity": 20, "weight_grams": 290},
            {"size": "L", "color": "Royal Blue", "color_hex": "#4169E1", "stock_quantity": 15, "weight_grams": 300},
        ],
    },
    # Ã¢â€â‚¬Ã¢â€â‚¬ Women's Jeans Ã¢â€â‚¬Ã¢â€â‚¬
    {
        "title": "High-Rise Skinny Jeans",
        "description": "Flattering high-rise skinny jeans with super stretch.",
        "brand": "Ashmi Denim", "base_price": 1899, "sale_price": 1499,
        "hsn_code": "6204", "gst_rate": 12, "category_slug": "women-jeans",
        "is_active": True, "is_featured": False,
        "attributes": {"material": "Denim", "fit": "Slim", "pattern": "Solid", "occasion": ["Casual"], "season": ["All Season"], "wash_care": "Machine wash cold, turn inside out"},
        "variants": [
            {"size": "26", "color": "Medium Blue", "color_hex": "#0000CD", "stock_quantity": 30, "weight_grams": 400},
            {"size": "28", "color": "Medium Blue", "color_hex": "#0000CD", "stock_quantity": 45, "weight_grams": 420},
            {"size": "30", "color": "Medium Blue", "color_hex": "#0000CD", "stock_quantity": 40, "weight_grams": 440},
            {"size": "32", "color": "Medium Blue", "color_hex": "#0000CD", "stock_quantity": 30, "weight_grams": 460},
            {"size": "28", "color": "Black", "color_hex": "#000000", "stock_quantity": 35, "weight_grams": 420},
            {"size": "30", "color": "Black", "color_hex": "#000000", "stock_quantity": 30, "weight_grams": 440},
        ],
    },
    # Ã¢â€â‚¬Ã¢â€â‚¬ Boys Ã¢â€â‚¬Ã¢â€â‚¬
    {
        "title": "Dinosaur Print Kids T-Shirt",
        "description": "Fun dinosaur print t-shirt for boys. Soft cotton.",
        "brand": "Ashmi Kids", "base_price": 499, "sale_price": 399,
        "hsn_code": "6109", "gst_rate": 5, "category_slug": "boys-tshirts",
        "is_active": True, "is_featured": True,
        "attributes": {"material": "Cotton", "fit": "Regular", "sleeve": "Half Sleeve", "neck": "Round Neck", "pattern": "Printed", "occasion": ["Casual"], "season": ["All Season"], "wash_care": "Machine wash cold"},
        "variants": [
            {"size": "4-6", "color": "Green", "color_hex": "#228B22", "stock_quantity": 50, "weight_grams": 110},
            {"size": "7-9", "color": "Green", "color_hex": "#228B22", "stock_quantity": 45, "weight_grams": 120},
            {"size": "10-12", "color": "Green", "color_hex": "#228B22", "stock_quantity": 35, "weight_grams": 130},
            {"size": "13-15", "color": "Green", "color_hex": "#228B22", "stock_quantity": 30, "weight_grams": 140},
            {"size": "16+", "color": "Green", "color_hex": "#228B22", "stock_quantity": 25, "weight_grams": 150},
            {"size": "4-6", "color": "Blue", "color_hex": "#4169E1", "stock_quantity": 40, "weight_grams": 110},
            {"size": "7-9", "color": "Blue", "color_hex": "#4169E1", "stock_quantity": 35, "weight_grams": 120},
            {"size": "10-12", "color": "Blue", "color_hex": "#4169E1", "stock_quantity": 30, "weight_grams": 130},
            {"size": "13-15", "color": "Blue", "color_hex": "#4169E1", "stock_quantity": 25, "weight_grams": 140},
            {"size": "16+", "color": "Blue", "color_hex": "#4169E1", "stock_quantity": 20, "weight_grams": 150},
        ],
    },
    {
        "title": "Cargo Shorts for Boys",
        "description": "Durable cargo shorts with multiple pockets.",
        "brand": "Ashmi Kids", "base_price": 699, "sale_price": 549,
        "hsn_code": "6204", "gst_rate": 5, "category_slug": "boys-shorts",
        "is_active": True, "is_featured": False,
        "attributes": {"material": "Cotton", "fit": "Regular", "pattern": "Solid", "occasion": ["Casual"], "season": ["Summer"], "wash_care": "Machine wash cold"},
        "variants": [
            {"size": "4-6", "color": "Khaki", "color_hex": "#C3B091", "stock_quantity": 45, "weight_grams": 140},
            {"size": "7-9", "color": "Khaki", "color_hex": "#C3B091", "stock_quantity": 40, "weight_grams": 150},
            {"size": "10-12", "color": "Khaki", "color_hex": "#C3B091", "stock_quantity": 35, "weight_grams": 160},
            {"size": "13-15", "color": "Khaki", "color_hex": "#C3B091", "stock_quantity": 30, "weight_grams": 170},
            {"size": "16+", "color": "Khaki", "color_hex": "#C3B091", "stock_quantity": 25, "weight_grams": 180},
            {"size": "4-6", "color": "Navy", "color_hex": "#000080", "stock_quantity": 40, "weight_grams": 140},
            {"size": "7-9", "color": "Navy", "color_hex": "#000080", "stock_quantity": 35, "weight_grams": 150},
            {"size": "10-12", "color": "Navy", "color_hex": "#000080", "stock_quantity": 30, "weight_grams": 160},
            {"size": "13-15", "color": "Navy", "color_hex": "#000080", "stock_quantity": 25, "weight_grams": 170},
            {"size": "16+", "color": "Navy", "color_hex": "#000080", "stock_quantity": 20, "weight_grams": 180},
        ],
    },
    # Ã¢â€â‚¬Ã¢â€â‚¬ Girls Ã¢â€â‚¬Ã¢â€â‚¬
    {
        "title": "Polka Dot Party Frock",
        "description": "Adorable polka dot frock with bow detail.",
        "brand": "Ashmi Kids", "base_price": 999, "sale_price": 799,
        "hsn_code": "6204", "gst_rate": 5, "category_slug": "girls-frocks",
        "is_active": True, "is_featured": True,
        "attributes": {"material": "Cotton", "fit": "A-Line", "sleeve": "Sleeveless", "neck": "Round Neck", "pattern": "Polka Dot", "occasion": ["Party", "Festive"], "season": ["All Season"], "wash_care": "Hand wash, line dry"},
        "variants": [
            {"size": "4-6", "color": "Pink", "color_hex": "#FF69B4", "stock_quantity": 50, "weight_grams": 120},
            {"size": "7-9", "color": "Pink", "color_hex": "#FF69B4", "stock_quantity": 45, "weight_grams": 130},
            {"size": "10-12", "color": "Pink", "color_hex": "#FF69B4", "stock_quantity": 40, "weight_grams": 140},
            {"size": "13-15", "color": "Pink", "color_hex": "#FF69B4", "stock_quantity": 35, "weight_grams": 150},
            {"size": "16+", "color": "Pink", "color_hex": "#FF69B4", "stock_quantity": 30, "weight_grams": 160},
            {"size": "4-6", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 45, "weight_grams": 120},
            {"size": "7-9", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 40, "weight_grams": 130},
            {"size": "10-12", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 35, "weight_grams": 140},
            {"size": "13-15", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 30, "weight_grams": 150},
            {"size": "16+", "color": "White", "color_hex": "#FFFFFF", "stock_quantity": 25, "weight_grams": 160},
        ],
    },
    {
        "title": "Ruffle Sleeve Girls Top",
        "description": "Cute ruffle sleeve top for girls.",
        "brand": "Ashmi Kids", "base_price": 599, "sale_price": 449,
        "hsn_code": "6106", "gst_rate": 5, "category_slug": "girls-tops",
        "is_active": True, "is_featured": False,
        "attributes": {"material": "Cotton", "fit": "Regular", "sleeve": "Flutter", "neck": "Round Neck", "pattern": "Printed", "occasion": ["Casual"], "season": ["Summer", "Spring"], "wash_care": "Machine wash cold"},
        "variants": [
            {"size": "4-6", "color": "Lavender", "color_hex": "#E6E6FA", "stock_quantity": 45, "weight_grams": 100},
            {"size": "7-9", "color": "Lavender", "color_hex": "#E6E6FA", "stock_quantity": 40, "weight_grams": 110},
            {"size": "10-12", "color": "Lavender", "color_hex": "#E6E6FA", "stock_quantity": 35, "weight_grams": 120},
            {"size": "13-15", "color": "Lavender", "color_hex": "#E6E6FA", "stock_quantity": 30, "weight_grams": 130},
            {"size": "16+", "color": "Lavender", "color_hex": "#E6E6FA", "stock_quantity": 25, "weight_grams": 140},
            {"size": "4-6", "color": "Peach", "color_hex": "#FFDAB9", "stock_quantity": 40, "weight_grams": 100},
            {"size": "7-9", "color": "Peach", "color_hex": "#FFDAB9", "stock_quantity": 35, "weight_grams": 110},
            {"size": "10-12", "color": "Peach", "color_hex": "#FFDAB9", "stock_quantity": 30, "weight_grams": 120},
            {"size": "13-15", "color": "Peach", "color_hex": "#FFDAB9", "stock_quantity": 25, "weight_grams": 130},
            {"size": "16+", "color": "Peach", "color_hex": "#FFDAB9", "stock_quantity": 20, "weight_grams": 140},
        ],
    },
    # Ã¢â€â‚¬Ã¢â€â‚¬ Unisex Ã¢â€â‚¬Ã¢â€â‚¬
    {
        "title": "Oversized Fleece Hoodie",
        "description": "Ultra-soft fleece hoodie with kangaroo pocket.",
        "brand": "Ashmi Active", "base_price": 1999, "sale_price": 1599,
        "hsn_code": "6110", "gst_rate": 12, "category_slug": "unisex-hoodies",
        "is_active": True, "is_featured": True,
        "attributes": {"material": "Fleece", "fit": "Oversized", "sleeve": "Full Sleeve", "neck": "Hooded", "pattern": "Solid", "occasion": ["Casual", "Lounge", "Sports"], "season": ["Winter"], "wash_care": "Machine wash cold, do not bleach, tumble dry low"},
        "variants": [
            {"size": "S", "color": "Grey", "color_hex": "#808080", "stock_quantity": 35, "weight_grams": 450},
            {"size": "M", "color": "Grey", "color_hex": "#808080", "stock_quantity": 50, "weight_grams": 480},
            {"size": "L", "color": "Grey", "color_hex": "#808080", "stock_quantity": 45, "weight_grams": 510},
            {"size": "XL", "color": "Grey", "color_hex": "#808080", "stock_quantity": 30, "weight_grams": 540},
            {"size": "M", "color": "Black", "color_hex": "#000000", "stock_quantity": 45, "weight_grams": 480},
            {"size": "L", "color": "Black", "color_hex": "#000000", "stock_quantity": 40, "weight_grams": 510},
            {"size": "XL", "color": "Black", "color_hex": "#000000", "stock_quantity": 25, "weight_grams": 540},
        ],
    },
    {
        "title": "Lightweight Windbreaker Jacket",
        "description": "Water-resistant windbreaker jacket. Packable design.",
        "brand": "Ashmi Active", "base_price": 2499, "sale_price": 1999,
        "hsn_code": "6201", "gst_rate": 12, "category_slug": "unisex-jackets",
        "is_active": True, "is_featured": False,
        "attributes": {"material": "Nylon", "fit": "Regular", "sleeve": "Full Sleeve", "neck": "Hooded", "pattern": "Solid", "occasion": ["Sports", "Casual"], "season": ["Monsoon", "Winter"], "wash_care": "Machine wash cold, hang dry"},
        "variants": [
            {"size": "S", "color": "Navy", "color_hex": "#1B1F3B", "stock_quantity": 25, "weight_grams": 300},
            {"size": "M", "color": "Navy", "color_hex": "#1B1F3B", "stock_quantity": 40, "weight_grams": 320},
            {"size": "L", "color": "Navy", "color_hex": "#1B1F3B", "stock_quantity": 35, "weight_grams": 340},
            {"size": "XL", "color": "Navy", "color_hex": "#1B1F3B", "stock_quantity": 20, "weight_grams": 360},
            {"size": "M", "color": "Olive", "color_hex": "#808000", "stock_quantity": 30, "weight_grams": 320},
            {"size": "L", "color": "Olive", "color_hex": "#808000", "stock_quantity": 25, "weight_grams": 340},
        ],
    },
]


def step5_create_products():
    print("\n[STEP 5] Creating products with variants...")

    # Build slug->id map from all categories
    status, cats = api_get("/admin/categories")
    cat_map = {}
    if status == 200 and isinstance(cats, list):
        for c in cats:
            cat_map[c.get("slug", "")] = c.get("id")

    if not cat_map:
        fail("No categories found! Cannot create products.")
        return

    # Fetch ALL existing products to detect slug conflicts
    # GET /admin/products returns PaginatedResponse with .items
    existing_products = {}  # slug -> {id, variant_count}
    page = 1
    while True:
        s, resp = api_get("/admin/products", params={"page": page, "page_size": 100})
        if s == 200:
            items = resp.get("items", [])
            for p in items:
                existing_products[p.get("slug", "")] = {
                    "id": p.get("id"),
                    "variant_count": p.get("variant_count", 0),
                    "total_stock": p.get("total_stock", 0),
                }
            if len(items) < 100:
                break
            page += 1
        else:
            break

    if existing_products:
        print(f"  Found {len(existing_products)} existing products in DB")

    created = 0
    variants_added = 0
    skipped = 0

    for product in PRODUCTS:
        category_id = cat_map.get(product["category_slug"])
        if not category_id:
            fail(f"Category slug '{product['category_slug']}' not found Ã¢â‚¬â€ skipping {product['title']}")
            continue

        product_slug = slugify(product["title"])
        existing = existing_products.get(product_slug)

        # Ã¢â€â‚¬Ã¢â€â‚¬ Case 1: Product exists WITH variants Ã¢â€ â€™ skip entirely Ã¢â€â‚¬Ã¢â€â‚¬
        if existing and existing.get("variant_count", 0) > 0:
            skip(f"Product exists with {existing['variant_count']} variants: {product['title']}")
            skipped += 1
            continue

        # Ã¢â€â‚¬Ã¢â€â‚¬ Case 2: Product exists WITHOUT variants Ã¢â€ â€™ add variants Ã¢â€â‚¬Ã¢â€â‚¬
        if existing and existing.get("variant_count", 0) == 0:
            product_id = existing["id"]
            ok(f"Product exists, adding variants: {product['title']}")
            v_ok = 0
            for v in product.get("variants", []):
                variant_payload = {
                    "product_id": str(product_id),
                    "size": v.get("size"),
                    "color": v.get("color"),
                    "color_hex": v.get("color_hex"),
                    "stock_quantity": v.get("stock_quantity", 0),
                    "weight_grams": v.get("weight_grams"),
                    "is_active": True,
                }
                vs, vd = api_post("/admin/variants", variant_payload)
                if vs in [200, 201]:
                    v_ok += 1
                else:
                    fail(f"    Variant {v.get('size')}/{v.get('color')}: {vs} Ã¢â‚¬â€ {vd}")
            if v_ok > 0:
                ok(f"    {v_ok} variants added")
                variants_added += v_ok
            continue

        # Ã¢â€â‚¬Ã¢â€â‚¬ Case 3: Product does NOT exist Ã¢â€ â€™ create with inline variants Ã¢â€â‚¬Ã¢â€â‚¬
        prod_data = {
            "title": product["title"],
            "slug": product_slug,
            "description": product["description"],
            "category_id": str(category_id),
            "brand": product["brand"],
            "base_price": product["base_price"],
            "sale_price": product.get("sale_price"),
            "hsn_code": product["hsn_code"],
            "gst_rate": product["gst_rate"],
            "attributes": product["attributes"],
            "is_active": product["is_active"],
            "is_featured": product["is_featured"],
        }

        inline_variants = []
        for v in product.get("variants", []):
            inline_variants.append({
                "size": v.get("size"),
                "color": v.get("color"),
                "color_hex": v.get("color_hex"),
                "stock_quantity": v.get("stock_quantity", 0),
                "weight_grams": v.get("weight_grams"),
                "is_active": True,
            })

        # FastAPI two-body-param format
        payload = {"data": prod_data, "variants": inline_variants}
        s, d = api_post("/admin/products", payload)

        if s in [200, 201]:
            ok(f"Product + {len(inline_variants)} variants: {product['title']}")
            created += 1
        else:
            fail(f"Product '{product['title']}': {s} Ã¢â‚¬â€ {json.dumps(d)[:200]}")

    print(f"  Summary: {created} new products, {variants_added} variants added to existing, {skipped} skipped")


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# STEP 6: Coupons
# Schema: CouponCreate
#   code: str max50 (required)
#   description: str|None max500
#   type: str pattern ^(flat|percent)$ (REQUIRED)
#   value: Decimal >0 (required)
#   min_order_value: Decimal >=0 default 0
#   max_discount: Decimal|None >=0
#   usage_limit: int|None >=1
#   per_user_limit: int >=1 default 1
#   applicable_categories: list[UUID]|None
#   starts_at: datetime (REQUIRED)
#   expires_at: datetime (REQUIRED)
#   is_active: bool = True
#
# Route: admin_coupon_router prefix="/admin/coupons"
# Full path: POST /api/v1/admin/coupons
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

now = datetime.now(timezone.utc)

COUPONS = [
    {
        "code": "WELCOME10",
        "description": "10% off on your first order",
        "type": "percent",
        "value": 10,
        "min_order_value": 500,
        "max_discount": 200,
        "per_user_limit": 1,
        "usage_limit": 1000,
        "starts_at": now.isoformat(),
        "expires_at": (now + timedelta(days=365)).isoformat(),
        "is_active": True,
    },
    {
        "code": "FLAT200",
        "description": "Flat Rs.200 off on orders above Rs.1500",
        "type": "flat",
        "value": 200,
        "min_order_value": 1500,
        "max_discount": 200,
        "per_user_limit": 3,
        "usage_limit": 500,
        "starts_at": now.isoformat(),
        "expires_at": (now + timedelta(days=365)).isoformat(),
        "is_active": True,
    },
]


def step6_create_coupons():
    print("\n[STEP 6] Creating coupons...")
    for coupon in COUPONS:
        s, d = api_post("/admin/coupons", coupon)
        if s in [200, 201]:
            ok(f"Coupon: {coupon['code']} Ã¢â‚¬â€ {coupon['description']}")
        elif s in [400, 409]:
            skip(f"Coupon exists: {coupon['code']}")
        else:
            fail(f"Coupon '{coupon['code']}': {s} Ã¢â‚¬â€ {d}")


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# MAIN
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

def main():
    print("=" * 60)
    print("  Ashmi Store Ã¢â‚¬â€ Test Data Seed Script v3")
    print("=" * 60)

    # Check backend
    try:
        resp = requests.get(f"{BASE_URL.replace('/api/v1', '')}/docs")
        if resp.status_code == 200:
            ok("Backend is running")
        else:
            fail(f"Backend returned {resp.status_code}")
            sys.exit(1)
    except requests.ConnectionError:
        fail("Cannot connect to backend at http://127.0.0.1:8000")
        print("  Start: uvicorn app.main:app --reload --port 8000")
        sys.exit(1)

    step1_admin_login()
    step2_register_customer()
    step3_seed_attributes()
    step4_create_categories()
    step5_create_products()
    step6_create_coupons()

    print("\n" + "=" * 60)
    print("  SEED COMPLETE")
    print("=" * 60)
    print(f"""
  Test Accounts:
    Admin:  {ADMIN_EMAIL} / {ADMIN_PASSWORD}
    Customer:    {CUSTOMER_EMAIL} / {CUSTOMER_PASSWORD}

  Data Created:
    - 8 attribute definitions
    - 5 parent + 14 subcategories = 19 categories
    - 20 products with ~100 variants
    - 2 coupons (WELCOME10, FLAT200)

  Next Steps:
    1. Open http://localhost:3000 Ã¢â‚¬â€ products should appear
    2. Login as customer -> add to cart -> checkout
    3. Login as admin -> admin dashboard shows data
""")


if __name__ == "__main__":
    main()
