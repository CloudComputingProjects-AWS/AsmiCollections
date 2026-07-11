"""
Image Processing API â€” /api/v1/admin/images/
Phase 3: Pre-signed upload, Lambda callback, CRUD, reorder, primary toggle.
starts the upload flow
receives processing result
updates image metadata in DB
lets admins manage images
"""

from uuid import UUID
import hashlib
import hmac
import time

from fastapi import APIRouter, Depends, HTTPException,Request
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
from app.core.config import get_settings
from app.core.origin_policy import require_trusted_origin
router = APIRouter(prefix="/admin/images", tags=["Admin â€” Image Pipeline"])

product_mgr = require_role("product_manager", "admin")


def _handle_error(e: ImageServiceError):
    raise HTTPException(status_code=e.status_code, detail=e.message)

# PRE-SIGNED UPLOAD

@router.post(
    "/upload/{product_id}",
    response_model=PresignedUploadResponse,
    status_code=201,dependencies=[Depends(require_trusted_origin)]
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

settings = get_settings()

def _verify_image_callback_signature(request_body: bytes, timestamp: str | None, signature: str | None) -> None:
    callback_secret = settings.resolved_image_callback_secret

    if not callback_secret:
        raise HTTPException(status_code=500, detail="Image callback secret not configured")

    if not timestamp or not signature:
        raise HTTPException(status_code=401, detail="Missing callback signature")

    try:
        ts = int(timestamp)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid callback timestamp")

    now = int(time.time())
    if abs(now - ts) > 300:
        raise HTTPException(status_code=401, detail="Expired callback signature")

    signed_payload = timestamp.encode("utf-8") + b"." + request_body

    expected = hmac.new(
        callback_secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    received = signature.removeprefix("sha256=")

    if not hmac.compare_digest(expected, received):
        raise HTTPException(status_code=401, detail="Invalid callback signature")
        
@router.post("/callback")
async def image_processing_callback(
    request: Request,
    data: ImageCallbackRequest,
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()

    _verify_image_callback_signature(
        request_body=body,
        timestamp=request.headers.get("X-Ashmi-Timestamp"),
        signature=request.headers.get("X-Ashmi-Signature"),
    )
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


@router.put("/{image_id}", response_model=ProductImageResponse,dependencies=[Depends(require_trusted_origin)])
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


@router.delete("/{image_id}", response_model=MessageResponse,dependencies=[Depends(require_trusted_origin)])
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


@router.post("/{product_id}/reorder", response_model=list[ProductImageResponse],dependencies=[Depends(require_trusted_origin)])
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


@router.post("/set-primary/{image_id}", response_model=ProductImageResponse,dependencies=[Depends(require_trusted_origin)])
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
