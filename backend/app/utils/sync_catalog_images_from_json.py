"""
Sync product image metadata from catalog JSON into local Postgres.

This utility is intended for local/dev data alignment only. It does not download
image files. It copies image URL fields, such as CloudFront thumbnail URLs, into
the local product_images table so the local frontend can render the same public
assets that AWS dev returns.

Usage:
  python -m app.utils.sync_catalog_images_from_json --file catalog-page-1.json
  curl.exe -L "https://.../api/v1/catalog/products?page=1&page_size=40" |
    python -m app.utils.sync_catalog_images_from_json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import and_, or_, select

from app.core.database import async_session_factory
from app.models.models import Product, ProductImage


@dataclass
class SyncStats:
    products_seen: int = 0
    products_matched: int = 0
    products_without_images: int = 0
    images_seen: int = 0
    images_created: int = 0
    images_updated: int = 0
    images_skipped: int = 0


def _parse_uuid(value: str | None) -> UUID | None:
    if not value:
        return None
    try:
        return UUID(value)
    except ValueError:
        return None


def _load_payloads(paths: list[str]) -> list[dict[str, Any]]:
    if paths:
        return [
            json.loads(Path(path).read_text(encoding="utf-8-sig"))
            for path in paths
        ]

    raw = sys.stdin.read().strip()
    if not raw:
        raise SystemExit("No JSON input provided. Pass --file or pipe JSON to stdin.")
    return [json.loads(raw)]


def _iter_products(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    for payload in payloads:
        if isinstance(payload, dict) and isinstance(payload.get("items"), list):
            products.extend(payload["items"])
        elif isinstance(payload, list):
            products.extend(payload)
        else:
            raise SystemExit("Unsupported JSON shape. Expected catalog response with 'items'.")
    return products


def _renderable_status(image: dict[str, Any]) -> str:
    if image.get("thumbnail_url") or image.get("medium_url") or image.get("processed_url"):
        return "completed"
    return "pending"


async def _find_local_product(db, product: dict[str, Any]) -> Product | None:
    product_id = _parse_uuid(product.get("id"))
    slug = product.get("slug")
    title = product.get("title")
    brand = product.get("brand")

    if slug:
        result = await db.execute(
            select(Product).where(
                Product.slug == slug,
                Product.is_active == True,
                Product.deleted_at.is_(None),
            ).limit(1)
        )
        matched = result.scalar_one_or_none()
        if matched:
            return matched

    if not title:
        return None

    if brand:
        result = await db.execute(
            select(Product).where(
                Product.is_active == True,
                Product.deleted_at.is_(None),
                Product.title == title,
                Product.brand == brand,
            ).limit(2)
        )
        matches = list(result.scalars().all())
        if len(matches) == 1:
            return matches[0]

    if product_id:
        result = await db.execute(
            select(Product).where(
                Product.id == product_id,
                Product.is_active == True,
                Product.deleted_at.is_(None),
            ).limit(1)
        )
        matched = result.scalar_one_or_none()
        if matched and (not brand or matched.brand == brand):
            return matched

    result = await db.execute(
        select(Product)
        .where(
            Product.is_active == True,
            Product.deleted_at.is_(None),
            Product.title == title,
        )
        .limit(2)
    )
    matches = list(result.scalars().all())
    if len(matches) == 1:
        return matches[0]

    return None


async def _find_existing_image(
    db,
    image_id: UUID | None,
    product_id: UUID,
    original_url: str,
) -> ProductImage | None:
    filters = []
    if image_id:
        filters.append(ProductImage.id == image_id)
    filters.append(
        (ProductImage.product_id == product_id)
        & (ProductImage.original_url == original_url)
    )

    result = await db.execute(select(ProductImage).where(or_(*filters)).limit(1))
    return result.scalar_one_or_none()


async def sync_catalog_images(payloads: list[dict[str, Any]], dry_run: bool = False) -> SyncStats:
    stats = SyncStats()
    products = _iter_products(payloads)

    async with async_session_factory() as db:
        for product in products:
            stats.products_seen += 1
            images = product.get("images") or []
            if not images:
                stats.products_without_images += 1
                continue

            local_product = await _find_local_product(db, product)
            if not local_product:
                stats.images_skipped += len(images)
                continue

            stats.products_matched += 1

            for image in images:
                stats.images_seen += 1
                original_url = image.get("original_url")
                if not original_url:
                    stats.images_skipped += 1
                    continue

                image_id = _parse_uuid(image.get("id"))
                existing = await _find_existing_image(
                    db,
                    image_id=image_id,
                    product_id=local_product.id,
                    original_url=original_url,
                )

                values = {
                    "product_id": local_product.id,
                    "original_url": original_url,
                    "processed_url": image.get("processed_url"),
                    "thumbnail_url": image.get("thumbnail_url"),
                    "medium_url": image.get("medium_url"),
                    "alt_text": image.get("alt_text"),
                    "is_primary": bool(image.get("is_primary")),
                    "sort_order": int(image.get("sort_order") or 0),
                    "processing_status": _renderable_status(image),
                }

                if existing:
                    if not dry_run:
                        for key, value in values.items():
                            setattr(existing, key, value)
                    stats.images_updated += 1
                else:
                    if not dry_run:
                        if image_id:
                            values["id"] = image_id
                        db.add(ProductImage(**values))
                    stats.images_created += 1

        if dry_run:
            await db.rollback()
        else:
            await db.commit()

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync catalog product image URL metadata into local Postgres."
    )
    parser.add_argument(
        "--file",
        action="append",
        default=[],
        help="Catalog JSON file. Can be passed multiple times.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and compare without committing database changes.",
    )
    args = parser.parse_args()

    payloads = _load_payloads(args.file)
    stats = asyncio.run(sync_catalog_images(payloads, dry_run=args.dry_run))
    print(json.dumps(stats.__dict__, indent=2))


if __name__ == "__main__":
    main()
