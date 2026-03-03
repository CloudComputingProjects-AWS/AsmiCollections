"""
Reviews API â€” Phase 5.
Reviews: /api/v1/reviews/ (public read, auth write)
Admin moderation: /api/v1/admin/reviews/
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_role
from app.models.models import User
from app.schemas.auth import MessageResponse
from app.schemas.wishlist_review import (
    AdminReviewAction,
    ReviewCreate,
    ReviewListResponse,
    ReviewResponse,
    ReviewUpdate,
)
from app.services.wishlist_review_service import (
    ReviewService,
    ReviewError,
)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# REVIEWS ROUTER (public read, auth write)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

review_router = APIRouter(prefix="/reviews", tags=["Reviews"])


@review_router.get("/product/{product_id}", response_model=ReviewListResponse)
async def list_product_reviews(
    product_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """List approved reviews for a product. Public endpoint."""
    service = ReviewService(db)
    return await service.list_reviews(product_id, page, page_size)


@review_router.post("", response_model=ReviewResponse, status_code=201)
async def create_review(
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Submit a review. One per user per product. Requires moderation."""
    service = ReviewService(db)
    try:
        review = await service.create_review(user.id, data)
        await db.commit()
        return review
    except ReviewError as e:
        _handle_error(e)


@review_router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: UUID,
    data: ReviewUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update own review. Resets approval status."""
    service = ReviewService(db)
    try:
        review = await service.update_review(user.id, review_id, data)
        await db.commit()
        return review
    except ReviewError as e:
        _handle_error(e)


@review_router.delete("/{review_id}", response_model=MessageResponse)
async def delete_review(
    review_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete own review."""
    service = ReviewService(db)
    try:
        await service.delete_review(user.id, review_id)
        await db.commit()
        return MessageResponse(message="Review deleted.")
    except ReviewError as e:
        _handle_error(e)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ADMIN REVIEW MODERATION
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

admin_review_router = APIRouter(prefix="/admin/reviews", tags=["Admin â€” Review Moderation"])
order_mgr = require_role("order_manager", "admin")


@admin_review_router.get("/pending")
async def list_pending_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(order_mgr),
):
    """List reviews pending moderation."""
    service = ReviewService(db)
    return await service.admin_list_pending(page, page_size)


@admin_review_router.post("/{review_id}/moderate")
async def moderate_review(
    review_id: UUID,
    data: AdminReviewAction,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(order_mgr),
):
    """Approve or reject a review."""
    service = ReviewService(db)
    try:
        review = await service.admin_moderate(review_id, data.action)
        await db.commit()
        return {"message": f"Review {data.action}d.", "review_id": str(review_id)}
    except ReviewError as e:
        _handle_error(e)
