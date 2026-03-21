"""
Image Processing API â€” /api/v1/admin/images/
Phase 3: Pre-signed upload, Lambda callback, CRUD, reorder, primary toggle.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import require_role
from app.models.models import User
from app.schemas.auth import MessageResponse
from app.schemas.image import (
    ImageCallbackRequest,
    ImageReorderRequest,
    ImageUpdateRequest,
    PresignedUploadRequest,
    PresignedUploadResponse,
    SetPrimaryRequest,
)
from app.schemas.product import ProductImageResponse
from app.services.image_service import ImageService, ImageServiceError

router = APIRouter(prefix="/admin/images", tags=["Admin â€” Image Pipeline"])

product_mgr = require_role("product_manager", "admin")


def _handle_error(e: ImageServiceError):
    raise HTTPException(status_code=e.status_code, detail=e.message)

# PRE-SIGNED UPLOAD

@router.post(
    "/upload/{product_id}",
    response_model=PresignedUploadResponse,
    status_code=201,
)
async def get_upload_url(
    product_id: UUID,
    data: PresignedUploadRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """
    Generate pre-signed S3 URL for direct image upload.
    Creates a pending product_images record.
    Frontend uploads directly to the returned URL.
    """
    service = ImageService(db)
    try:
        result = await service.generate_presigned_upload(
            product_id, data.filename, data.content_type
        )
        await db.commit()
        return PresignedUploadResponse(
            upload_url=result["upload_url"],
            image_id=result["image_id"],
            s3_key=result["s3_key"],
            expires_in=result["expires_in"],
        )
    except ImageServiceError as e:
        _handle_error(e)


# LAMBDA CALLBACK


@router.post("/callback")
async def image_processing_callback(
    data: ImageCallbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Callback endpoint for Lambda image processor.
    Updates product_images with processed URLs and status.
    
    No auth required â€” should be protected by API key or VPC in production.
    """
    service = ImageService(db)
    try:
        if data.status == "completed":
            image = await service.process_callback(
                data.image_id,
                data.processed_url,
                data.medium_url,
                data.thumbnail_url,
            )
        else:
            image = await service.mark_processing_failed(data.image_id)
        await db.commit()
        return {"status": "ok", "image_id": str(image.id), "processing_status": image.processing_status}
    except ImageServiceError as e:
        _handle_error(e)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# IMAGE CRUD
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


@router.get("/{product_id}", response_model=list[ProductImageResponse])
async def list_product_images(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """List all images for a product, ordered by sort_order."""
    service = ImageService(db)
    return await service.list_images(product_id)


@router.put("/{image_id}", response_model=ProductImageResponse)
async def update_image(
    image_id: UUID,
    data: ImageUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """Update image alt text."""
    service = ImageService(db)
    try:
        image = await service.update_image(image_id, alt_text=data.alt_text)
        await db.commit()
        return image
    except ImageServiceError as e:
        _handle_error(e)


@router.delete("/{image_id}", response_model=MessageResponse)
async def delete_image(
    image_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """Delete an image. Auto-reassigns primary if needed."""
    service = ImageService(db)
    try:
        await service.delete_image(image_id)
        await db.commit()
        return MessageResponse(message="Image deleted.")
    except ImageServiceError as e:
        _handle_error(e)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# REORDERING & PRIMARY
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


@router.post("/{product_id}/reorder", response_model=list[ProductImageResponse])
async def reorder_images(
    product_id: UUID,
    data: ImageReorderRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """Reorder images by providing image IDs in desired order (drag-and-drop)."""
    service = ImageService(db)
    try:
        images = await service.reorder_images(product_id, data.image_ids)
        await db.commit()
        return images
    except ImageServiceError as e:
        _handle_error(e)


@router.post("/set-primary/{image_id}", response_model=ProductImageResponse)
async def set_primary_image(
    image_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(product_mgr),
):
    """Set an image as the primary product image."""
    service = ImageService(db)
    try:
        image = await service.set_primary(image_id)
        await db.commit()
        return image
    except ImageServiceError as e:
        _handle_error(e)
