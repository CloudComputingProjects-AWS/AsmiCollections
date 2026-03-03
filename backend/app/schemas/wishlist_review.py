"""
Pydantic schemas for Reviews — Phase 5.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


# ══════════════════════════════════════════
# ══════════════════════════════════════════



class ReviewCreate(BaseModel):
    product_id: UUID
    order_item_id: UUID | None = None
    rating: int = Field(..., ge=1, le=5)
    title: str | None = Field(None, max_length=200)
    comment: str | None = None
    fit_feedback: str | None = Field(None, pattern="^(true_to_size|runs_small|runs_large)$")


class ReviewUpdate(BaseModel):
    rating: int | None = Field(None, ge=1, le=5)
    title: str | None = Field(None, max_length=200)
    comment: str | None = None
    fit_feedback: str | None = Field(None, pattern="^(true_to_size|runs_small|runs_large)$")


class ReviewResponse(BaseModel):
    id: UUID
    user_id: UUID
    product_id: UUID
    order_item_id: UUID | None
    rating: int
    title: str | None
    comment: str | None
    fit_feedback: str | None
    is_verified: bool
    is_approved: bool
    created_at: datetime
    # Populated by service
    reviewer_name: str | None = None

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
    total: int
    page: int
    page_size: int
    avg_rating: float | None
    rating_distribution: dict[str, int]  # {"5": 10, "4": 5, ...}


class AdminReviewAction(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
