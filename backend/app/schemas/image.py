"""
Pydantic schemas for Image Processing Pipeline — Phase 3.
"""

from uuid import UUID

from pydantic import BaseModel, Field


class PresignedUploadRequest(BaseModel):
    filename: str = Field(..., max_length=255)
    content_type: str = Field(..., pattern="^image/(jpeg|png|webp)$")


class PresignedUploadResponse(BaseModel):
    upload_url: str
    image_id: UUID
    s3_key: str
    expires_in: int


class ImageCallbackRequest(BaseModel):
    """Sent by Lambda after processing completes."""
    image_id: UUID
    processed_url: str = Field(..., max_length=1000)
    medium_url: str = Field(..., max_length=1000)
    thumbnail_url: str = Field(..., max_length=1000)
    status: str = Field(default="completed", pattern="^(completed|failed)$")


class ImageUpdateRequest(BaseModel):
    alt_text: str | None = Field(None, max_length=300)


class ImageReorderRequest(BaseModel):
    """List of image IDs in desired order."""
    image_ids: list[UUID]


class SetPrimaryRequest(BaseModel):
    image_id: UUID
