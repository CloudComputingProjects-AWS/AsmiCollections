"""
Admin Product Management API Ã¢â‚¬â€ /api/v1/admin/
Phase 2: Categories, Products, Variants, Attributes, Inventory, Size Guides.
All routes require admin roles (product_manager or admin).
"""

import csv
import io
import math
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import require_role
from app.models.models import User
from app.schemas.auth import MessageResponse
from app.schemas.product import (
    AttributeDefinitionCreate,
    AttributeDefinitionResponse,
    AttributeDefinitionUpdate,
    BulkProductCreateRequest,
    BulkProductCreateResponse,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    InventoryBulkUpdateRequest,
    InventoryUpdateRequest,
    LowStockResponse,
    PaginatedResponse,
    ProductCreate,
    ProductDuplicateRequest,
    ProductDuplicateResponse,
    ProductResponse,
    ProductUpdate,
    ProductVariantInline,
    ProductVariantResponse,
    SizeGuideCreate,
    SizeGuideResponse,
    SizeMappingResponse,
    VariantCreate,
    VariantUpdate,
)
from app.services.product_service import ProductService, ProductServiceError

router = APIRouter(prefix="/admin", tags=["Admin Ã¢â‚¬â€ Product Management"])

# Role dependencies
product_mgr = require_role("product_manager", "admin")
admin_only = require_role("admin")


def _handle_error(e: ProductServiceError):
    raise HTTPException(status_code=e.status_code, detail=e.message)


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# ATTRIBUTE DEFINITIONS
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â


@router.get("/attribute-definitions", response_model=list[AttributeDefinitionResponse])
async def list_attributes(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """List all attribute definitions."""
    service = ProductService(db)
    return await service.list_attribute_definitions()


@router.post("/attribute-definitions", response_model=AttributeDefinitionResponse, status_code=201)
async def create_attribute(
    data: AttributeDefinitionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """Create a new attribute definition."""
    service = ProductService(db)
    try:
        attr = await service.create_attribute_definition(data)
        await db.commit()
        return attr
    except ProductServiceError as e:
        _handle_error(e)


@router.put("/attribute-definitions/{attr_id}", response_model=AttributeDefinitionResponse)
async def update_attribute(
    attr_id: UUID,
    data: AttributeDefinitionUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """Update an attribute definition."""
    service = ProductService(db)
    try:
        attr = await service.update_attribute_definition(attr_id, data)
        await db.commit()
        return attr
    except ProductServiceError as e:
        _handle_error(e)


@router.delete("/attribute-definitions/{attr_id}", response_model=MessageResponse)
async def delete_attribute(
    attr_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(admin_only),
):
    """Delete an attribute definition (admin only)."""
    service = ProductService(db)
    try:
        await service.delete_attribute_definition(attr_id)
        await db.commit()
        return MessageResponse(message="Attribute definition deleted.")
    except ProductServiceError as e:
        _handle_error(e)


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# CATEGORIES
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    gender: str | None = None,
    age_group: str | None = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """List categories with optional filters."""
    service = ProductService(db)
    return await service.list_categories(gender, age_group, active_only)


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    service = ProductService(db)
    try:
        return await service.get_category(category_id)
    except ProductServiceError as e:
        _handle_error(e)


@router.post("/categories", response_model=CategoryResponse, status_code=201)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    service = ProductService(db)
    try:
        cat = await service.create_category(data)
        await db.commit()
        return cat
    except ProductServiceError as e:
        _handle_error(e)


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    service = ProductService(db)
    try:
        cat = await service.update_category(category_id, data)
        await db.commit()
        return cat
    except ProductServiceError as e:
        _handle_error(e)


@router.delete("/categories/{category_id}", response_model=MessageResponse)
async def delete_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """Soft-delete a category."""
    service = ProductService(db)
    try:
        await service.delete_category(category_id)
        await db.commit()
        return MessageResponse(message="Category soft-deleted.")
    except ProductServiceError as e:
        _handle_error(e)


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# PRODUCTS
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â


@router.get("/products", response_model=PaginatedResponse)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: UUID | None = None,
    brand: str | None = None,
    is_active: bool | None = None,
    is_featured: bool | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """List products with pagination, filters, search."""
    service = ProductService(db)
    products, total = await service.list_products(
        page=page,
        page_size=page_size,
        category_id=str(category_id) if category_id else None,
        brand=brand,
        is_active=is_active,
        is_featured=is_featured,
        search=search,
    )
    return PaginatedResponse(
        items=[ProductResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    service = ProductService(db)
    try:
        return await service.get_product(product_id)
    except ProductServiceError as e:
        _handle_error(e)


@router.post("/products", response_model=ProductResponse, status_code=201)
async def create_product(
    data: ProductCreate,
    variants: list[ProductVariantInline] | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """Create product with optional inline variants."""
    service = ProductService(db)
    try:
        product = await service.create_product(data, variants)
        await db.commit()
        # Reload with relationships
        return await service.get_product(product.id)
    except ProductServiceError as e:
        _handle_error(e)


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    service = ProductService(db)
    try:
        await service.update_product(product_id, data)
        await db.commit()
        return await service.get_product(product_id)
    except ProductServiceError as e:
        _handle_error(e)


@router.delete("/products/{product_id}", response_model=MessageResponse)
async def delete_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """Soft-delete product and its variants."""
    service = ProductService(db)
    try:
        await service.delete_product(product_id)
        await db.commit()
        return MessageResponse(message="Product soft-deleted.")
    except ProductServiceError as e:
        _handle_error(e)


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# PRODUCT VARIANTS
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â


@router.post("/variants", response_model=ProductVariantResponse, status_code=201)
async def create_variant(
    data: VariantCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    service = ProductService(db)
    try:
        variant = await service.create_variant(data)
        await db.commit()
        return variant
    except ProductServiceError as e:
        _handle_error(e)


@router.put("/variants/{variant_id}", response_model=ProductVariantResponse)
async def update_variant(
    variant_id: UUID,
    data: VariantUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    service = ProductService(db)
    try:
        variant = await service.update_variant(variant_id, data)
        await db.commit()
        return variant
    except ProductServiceError as e:
        _handle_error(e)


@router.delete("/variants/{variant_id}", response_model=MessageResponse)
async def delete_variant(
    variant_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    service = ProductService(db)
    try:
        await service.delete_variant(variant_id)
        await db.commit()
        return MessageResponse(message="Variant soft-deleted.")
    except ProductServiceError as e:
        _handle_error(e)


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# INVENTORY
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â


@router.get("/inventory", response_model=PaginatedResponse)
async def list_inventory(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100, alias="limit"),
    search: str | None = None,
    low_stock_only: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """List all product variants with stock info for admin inventory page."""
    service = ProductService(db)
    items, total = await service.list_inventory(
        page=page,
        page_size=page_size,
        search=search,
        low_stock_only=low_stock_only,
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.put("/inventory/{variant_id}", response_model=ProductVariantResponse)
async def update_inventory(
    variant_id: UUID,
    data: InventoryUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """Update stock quantity for a single variant."""
    service = ProductService(db)
    try:
        variant = await service.update_stock(variant_id, data.stock_quantity)
        await db.commit()
        return variant
    except ProductServiceError as e:
        _handle_error(e)


@router.put("/inventory/bulk", response_model=MessageResponse)
async def bulk_update_inventory(
    data: InventoryBulkUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """Bulk update stock quantities."""
    service = ProductService(db)
    try:
        await service.bulk_update_stock(data.items)
        await db.commit()
        return MessageResponse(message=f"Updated {len(data.items)} variants.")
    except ProductServiceError as e:
        _handle_error(e)


@router.get("/inventory/low-stock", response_model=list[LowStockResponse])
async def get_low_stock(
    threshold: int = Query(10, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """Get variants with stock below threshold."""
    service = ProductService(db)
    return await service.get_low_stock_variants(threshold)


@router.post("/inventory/bulk-update", response_model=MessageResponse)
async def bulk_update_inventory_alias(
    data: InventoryBulkUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """Alias for PUT /inventory/bulk Ã¢â‚¬â€ matches frontend POST /bulk-update call."""
    service = ProductService(db)
    try:
        await service.bulk_update_stock(data.items)
        await db.commit()
        return MessageResponse(message=f"Updated {len(data.items)} variants.")
    except ProductServiceError as e:
        _handle_error(e)


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# SIZE GUIDES
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â


@router.get("/size-guides/{category_id}", response_model=list[SizeGuideResponse])
async def list_size_guides(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    service = ProductService(db)
    return await service.list_size_guides(category_id)


@router.post("/size-guides", response_model=SizeGuideResponse, status_code=201)
async def create_size_guide(
    data: SizeGuideCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    service = ProductService(db)
    try:
        guide = await service.create_size_guide(data)
        await db.commit()
        return guide
    except ProductServiceError as e:
        _handle_error(e)


@router.delete("/size-guides/{guide_id}", response_model=MessageResponse)
async def delete_size_guide(
    guide_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    service = ProductService(db)
    try:
        await service.delete_size_guide(guide_id)
        await db.commit()
        return MessageResponse(message="Size guide entry deleted.")
    except ProductServiceError as e:
        _handle_error(e)


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# BULK CSV UPLOAD
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â


@router.post("/products/bulk-upload")
async def bulk_upload_products(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """
    Upload products via CSV file.
    Expected columns: title, slug, description, category_id, brand,
    base_price, sale_price, hsn_code, gst_rate, tags, is_active,
    size, color, color_hex, sku, stock_quantity, price_override, weight_grams
    """
    if not file.filename.endswith((".csv", ".CSV")):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    content = await file.read()
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(decoded))
    rows = list(reader)

    if not rows:
        raise HTTPException(status_code=400, detail="CSV file is empty.")

    service = ProductService(db)
    result = await service.bulk_create_from_csv(rows)
    await db.commit()

    return {
        "message": f"Processed {len(rows)} rows.",
        "created": result["created"],
        "errors": result["errors"],
        "error_count": len(result["errors"]),
    }


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# PHASE 13G: BULK CREATE & DUPLICATE
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â


@router.post(
    "/products/bulk",
    response_model=BulkProductCreateResponse,
    summary="Bulk create products across multiple categories",
)
async def bulk_create_products(
    data: BulkProductCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(admin_only),
):
    """
    Admin: Create multiple products with inline variants in one API call.
    Accepts up to 50 products per request, each with their own category and variants.
    """
    service = ProductService(db)
    result = await service.bulk_create_products(data.products)
    await db.commit()
    return BulkProductCreateResponse(**result)


@router.post(
    "/products/{product_id}/duplicate",
    response_model=ProductDuplicateResponse,
    summary="Duplicate product to another category with size mapping",
)
async def duplicate_product(
    product_id: UUID,
    data: ProductDuplicateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(admin_only),
):
    """
    Admin: Clone a product to a different category/gender.
    Auto-maps size variants (e.g., S/M/L/XL Ã¢â€ â€™ 4-6/7-9/10-12/13-15/16+ for kids).
    """
    service = ProductService(db)
    try:
        result = await service.duplicate_product(
            product_id=product_id,
            target_category_id=data.target_category_id,
            new_title=data.new_title,
            new_slug=data.new_slug,
            map_sizes=data.map_sizes,
        )
        await db.commit()
        return ProductDuplicateResponse(**result)
    except ProductServiceError as e:
        _handle_error(e)


@router.get(
    "/size-mappings",
    response_model=list[SizeMappingResponse],
    summary="Get all size mapping configurations",
)
async def get_size_mappings(
    user: User = Depends(product_mgr),
):
    """Returns size mapping config for cross-category duplication."""
    return [
        SizeMappingResponse(
            source_type="standard", target_type="kids",
            mappings=ProductService.SIZE_MAPPINGS["standard_to_kids"],
        ),
        SizeMappingResponse(
            source_type="kids", target_type="standard",
            mappings=ProductService.SIZE_MAPPINGS["kids_to_standard"],
        ),
        SizeMappingResponse(
            source_type="standard", target_type="waist",
            mappings=ProductService.SIZE_MAPPINGS["standard_to_waist"],
        ),
        SizeMappingResponse(
            source_type="waist", target_type="standard",
            mappings=ProductService.SIZE_MAPPINGS["waist_to_standard"],
        ),
    ]


@router.get(
    "/suggested-sizes/{gender}",
    response_model=list[str],
    summary="Get suggested sizes for a gender",
)
async def get_suggested_sizes(
    gender: str,
    user: User = Depends(product_mgr),
):
    """Returns standard sizes for the given gender (used by frontend size helper)."""
    return ProductService.get_suggested_sizes(gender)
