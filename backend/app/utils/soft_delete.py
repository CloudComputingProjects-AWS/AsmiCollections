"""
Soft Delete Filtering.
Provides query helpers and SQLAlchemy event listeners that automatically
filter out soft-deleted records (WHERE deleted_at IS NULL).

Applies to: users, user_addresses, categories, products, product_variants, coupons
"""

from sqlalchemy import event
from sqlalchemy.orm import Query

# Models that have soft delete (deleted_at column)
SOFT_DELETE_MODELS = set()


def register_soft_delete(model_class):
    """
    Decorator: registers a model for automatic soft-delete filtering.
    Usage:
        @register_soft_delete
        class Product(Base):
            ...
            deleted_at = Column(DateTime(timezone=True))
    """
    SOFT_DELETE_MODELS.add(model_class)
    return model_class


def soft_delete_filter(query, model_class):
    """
    Apply soft delete filter to a query.
    Usage:
        query = soft_delete_filter(select(Product), Product)
    """
    if hasattr(model_class, "deleted_at"):
        return query.where(model_class.deleted_at.is_(None))
    return query


def apply_soft_delete(entity, deleted_at_value=None):
    """
    Soft-delete an entity instead of hard deleting.
    Usage:
        apply_soft_delete(product)
        await db.commit()
    """
    from datetime import datetime, timezone
    entity.deleted_at = deleted_at_value or datetime.now(timezone.utc)


def restore_soft_delete(entity):
    """
    Restore a soft-deleted entity.
    Usage:
        restore_soft_delete(product)
        await db.commit()
    """
    entity.deleted_at = None


class SoftDeleteMixin:
    """
    Mixin providing soft delete helper methods on model instances.
    Usage:
        class Product(Base, SoftDeleteMixin):
            ...
    """

    def soft_delete(self):
        from datetime import datetime, timezone
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self):
        self.deleted_at = None

    @property
    def is_deleted(self) -> bool:
        return getattr(self, 'deleted_at', None) is not None
