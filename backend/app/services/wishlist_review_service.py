"""
"""

import math

from sqlalchemy import Float, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    OrderItem,
    Product,
    ProductImage,
    ProductVariant,
    Review,
    User,
)


class ReviewError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)



class ReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_reviews(
        self,
        product_id,
        page: int = 1,
        page_size: int = 10,
        approved_only: bool = True,
    ) -> dict:
        """List reviews for a product with pagination and stats."""
        query = select(Review).where(Review.product_id == product_id)
        if approved_only:
            query = query.where(Review.is_approved == True)

        # Count
        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_q)).scalar()

        # Avg rating
        avg_q = select(func.avg(cast(Review.rating, Float))).where(
            Review.product_id == product_id, Review.is_approved == True
        )
        avg_rating = (await self.db.execute(avg_q)).scalar()

        # Rating distribution
        dist_q = (
            select(Review.rating, func.count(Review.id))
            .where(Review.product_id == product_id, Review.is_approved == True)
            .group_by(Review.rating)
        )
        dist_result = await self.db.execute(dist_q)
        distribution = {str(i): 0 for i in range(1, 6)}
        for rating, count in dist_result.all():
            distribution[str(rating)] = count

        # Paginated reviews
        query = query.order_by(Review.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        reviews = list(result.scalars().all())

        # Enrich with reviewer names
        enriched = []
        for review in reviews:
            user_result = await self.db.execute(
                select(User.first_name, User.last_name).where(User.id == review.user_id)
            )
            user_row = user_result.one_or_none()
            reviewer_name = None
            if user_row:
                parts = [user_row.first_name or "", user_row.last_name or ""]
                reviewer_name = " ".join(p for p in parts if p).strip() or "Anonymous"

            enriched.append({
                "id": review.id,
                "user_id": review.user_id,
                "product_id": review.product_id,
                "order_item_id": review.order_item_id,
                "rating": review.rating,
                "title": review.title,
                "comment": review.comment,
                "fit_feedback": review.fit_feedback,
                "is_verified": review.is_verified,
                "is_approved": review.is_approved,
                "created_at": review.created_at,
                "reviewer_name": reviewer_name,
            })

        return {
            "items": enriched,
            "total": total,
            "page": page,
            "page_size": page_size,
            "avg_rating": round(float(avg_rating), 1) if avg_rating else None,
            "rating_distribution": distribution,
        }

    async def create_review(self, user_id, data) -> Review:
        """Submit a product review. One review per user per product."""
        # Check duplicate
        existing = await self.db.execute(
            select(Review).where(
                Review.user_id == user_id,
                Review.product_id == data.product_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ReviewError("You already reviewed this product.", 409)

        # Verify product exists
        prod_result = await self.db.execute(
            select(Product).where(
                Product.id == data.product_id, Product.deleted_at.is_(None)
            )
        )
        if not prod_result.scalar_one_or_none():
            raise ReviewError("Product not found.", 404)

        # Check verified purchase
        is_verified = False
        if data.order_item_id:
            oi_result = await self.db.execute(
                select(OrderItem).where(
                    OrderItem.id == data.order_item_id,
                    OrderItem.order_id.in_(
                        select(OrderItem.order_id).where(OrderItem.id == data.order_item_id)
                    ),
                )
            )
            if oi_result.scalar_one_or_none():
                is_verified = True

        review = Review(
            user_id=user_id,
            product_id=data.product_id,
            order_item_id=data.order_item_id,
            rating=data.rating,
            title=data.title,
            comment=data.comment,
            fit_feedback=data.fit_feedback,
            is_verified=is_verified,
            is_approved=False,  # Requires admin moderation
        )
        self.db.add(review)
        await self.db.flush()
        return review

    async def update_review(self, user_id, review_id, data) -> Review:
        """Update own review."""
        result = await self.db.execute(
            select(Review).where(Review.id == review_id, Review.user_id == user_id)
        )
        review = result.scalar_one_or_none()
        if not review:
            raise ReviewError("Review not found.", 404)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(review, key, value)
        review.is_approved = False  # Re-approval needed after edit
        await self.db.flush()
        return review

    async def delete_review(self, user_id, review_id) -> None:
        result = await self.db.execute(
            select(Review).where(Review.id == review_id, Review.user_id == user_id)
        )
        review = result.scalar_one_or_none()
        if not review:
            raise ReviewError("Review not found.", 404)
        await self.db.delete(review)

    # ── Admin moderation ──

    async def admin_list_pending(self, page: int = 1, page_size: int = 20) -> dict:
        """List reviews pending moderation."""
        query = select(Review).where(Review.is_approved == False)
        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_q)).scalar()

        query = query.order_by(Review.created_at.asc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        reviews = list(result.scalars().all())

        return {
            "items": reviews,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def admin_moderate(self, review_id, action: str) -> Review:
        """Approve or reject a review."""
        result = await self.db.execute(
            select(Review).where(Review.id == review_id)
        )
        review = result.scalar_one_or_none()
        if not review:
            raise ReviewError("Review not found.", 404)

        if action == "approve":
            review.is_approved = True
        elif action == "reject":
            await self.db.delete(review)
            await self.db.flush()
            return review

        await self.db.flush()
        return review
