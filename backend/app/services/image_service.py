"""
Image Processing Service — Phase 3.
Handles: S3 pre-signed URL generation, image record CRUD,
         Lambda callback processing, reordering, primary toggle.

Architecture:
  Admin uploads via pre-signed URL → S3 raw bucket
  → S3 Event → Lambda (Sharp.js) → 3 WebP variants
  → Lambda POSTs callback → this service updates URLs + status
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.models import Product, ProductImage

settings = get_settings()

# Allowed MIME types and max file size
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE_MB = 5
MAX_IMAGES_PER_PRODUCT = 8


class ImageServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ImageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ══════════════════════════════════════
    # PRE-SIGNED URL GENERATION
    # ══════════════════════════════════════

    async def generate_presigned_upload(
        self, product_id, filename: str, content_type: str
    ) -> dict:
        """
        Generate a pre-signed S3 PUT URL for direct browser upload.
        Also creates a pending product_images record.

        Returns: {upload_url, image_id, s3_key, expires_in}
        """
        # Validate product exists
        result = await self.db.execute(
            select(Product).where(
                Product.id == product_id, Product.deleted_at.is_(None)
            )
        )
        if not result.scalar_one_or_none():
            raise ImageServiceError("Product not found.", 404)

        # Validate content type
        if content_type not in ALLOWED_TYPES:
            raise ImageServiceError(
                f"Invalid file type. Allowed: {', '.join(ALLOWED_TYPES)}", 400
            )

        # Validate extension
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise ImageServiceError(
                f"Invalid file extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}", 400
            )

        # Check image count limit
        count_result = await self.db.execute(
            select(ProductImage).where(ProductImage.product_id == product_id)
        )
        current_count = len(count_result.scalars().all())
        if current_count >= MAX_IMAGES_PER_PRODUCT:
            raise ImageServiceError(
                f"Maximum {MAX_IMAGES_PER_PRODUCT} images per product.", 400
            )

        # Generate S3 key
        image_uuid = str(uuid.uuid4())
        s3_key = f"uploads/raw/{product_id}/{image_uuid}{ext}"

        # Generate pre-signed URL using boto3
        try:
            import boto3
            s3_client = boto3.client(
                "s3",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
            )

            presigned_url = s3_client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": settings.S3_BUCKET_NAME,
                    "Key": s3_key,
                    "ContentType": content_type,
                },
                ExpiresIn=600,  # 10 minutes
            )
        except Exception as e:
            # In development without AWS credentials, return a mock URL
            if settings.ENVIRONMENT == "development":
                presigned_url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}?mock=true"
            else:
                raise ImageServiceError(f"Failed to generate upload URL: {str(e)}", 500)

        # Determine sort order and primary status
        is_primary = current_count == 0  # First image is primary

        # Create pending image record
        image = ProductImage(
            product_id=product_id,
            original_url=f"s3://{settings.S3_BUCKET_NAME}/{s3_key}",
            alt_text=filename,
            is_primary=is_primary,
            sort_order=current_count,
            processing_status="pending",
        )
        self.db.add(image)
        await self.db.flush()

        return {
            "upload_url": presigned_url,
            "image_id": str(image.id),
            "s3_key": s3_key,
            "expires_in": 600,
        }

    # ══════════════════════════════════════
    # LAMBDA CALLBACK (after processing)
    # ══════════════════════════════════════

    async def process_callback(
        self,
        image_id,
        processed_url: str,
        medium_url: str,
        thumbnail_url: str,
        status: str = "completed",
    ) -> ProductImage:
        """
        Called by Lambda after image processing completes.
        Updates the product_images record with processed URLs.
        """
        result = await self.db.execute(
            select(ProductImage).where(ProductImage.id == image_id)
        )
        image = result.scalar_one_or_none()
        if not image:
            raise ImageServiceError("Image record not found.", 404)

        image.processed_url = processed_url
        image.medium_url = medium_url
        image.thumbnail_url = thumbnail_url
        image.processing_status = status
        await self.db.flush()
        return image

    async def mark_processing_failed(self, image_id, error_message: str = None) -> ProductImage:
        """Mark image processing as failed."""
        result = await self.db.execute(
            select(ProductImage).where(ProductImage.id == image_id)
        )
        image = result.scalar_one_or_none()
        if not image:
            raise ImageServiceError("Image record not found.", 404)

        image.processing_status = "failed"
        await self.db.flush()
        return image

    # ══════════════════════════════════════
    # IMAGE CRUD
    # ══════════════════════════════════════

    async def list_images(self, product_id) -> list:
        """List all images for a product, ordered by sort_order."""
        result = await self.db.execute(
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.sort_order)
        )
        return list(result.scalars().all())

    async def update_image(self, image_id, alt_text: str = None) -> ProductImage:
        """Update image alt text."""
        result = await self.db.execute(
            select(ProductImage).where(ProductImage.id == image_id)
        )
        image = result.scalar_one_or_none()
        if not image:
            raise ImageServiceError("Image not found.", 404)

        if alt_text is not None:
            image.alt_text = alt_text
        await self.db.flush()
        return image

    async def delete_image(self, image_id) -> None:
        """Delete an image record. Optionally delete from S3 too."""
        result = await self.db.execute(
            select(ProductImage).where(ProductImage.id == image_id)
        )
        image = result.scalar_one_or_none()
        if not image:
            raise ImageServiceError("Image not found.", 404)

        product_id = image.product_id
        was_primary = image.is_primary

        await self.db.delete(image)
        await self.db.flush()

        # If deleted image was primary, assign next image as primary
        if was_primary:
            next_result = await self.db.execute(
                select(ProductImage)
                .where(ProductImage.product_id == product_id)
                .order_by(ProductImage.sort_order)
                .limit(1)
            )
            next_image = next_result.scalar_one_or_none()
            if next_image:
                next_image.is_primary = True
                await self.db.flush()

    # ══════════════════════════════════════
    # REORDERING & PRIMARY TOGGLE
    # ══════════════════════════════════════

    async def set_primary(self, image_id) -> ProductImage:
        """Set an image as the primary image for its product."""
        result = await self.db.execute(
            select(ProductImage).where(ProductImage.id == image_id)
        )
        image = result.scalar_one_or_none()
        if not image:
            raise ImageServiceError("Image not found.", 404)

        # Unset current primary
        await self.db.execute(
            update(ProductImage)
            .where(
                ProductImage.product_id == image.product_id,
                ProductImage.is_primary == True,
            )
            .values(is_primary=False)
        )

        image.is_primary = True
        await self.db.flush()
        return image

    async def reorder_images(self, product_id, image_ids: list) -> list:
        """
        Reorder images by setting sort_order based on position in image_ids list.
        image_ids = [uuid1, uuid2, uuid3] → sort_order = [0, 1, 2]
        """
        # Verify all IDs belong to this product
        result = await self.db.execute(
            select(ProductImage).where(ProductImage.product_id == product_id)
        )
        existing = {str(img.id): img for img in result.scalars().all()}

        for idx, img_id in enumerate(image_ids):
            img_id_str = str(img_id)
            if img_id_str not in existing:
                raise ImageServiceError(
                    f"Image {img_id} does not belong to product {product_id}.", 400
                )
            existing[img_id_str].sort_order = idx

        await self.db.flush()

        # Return updated list
        return await self.list_images(product_id)
