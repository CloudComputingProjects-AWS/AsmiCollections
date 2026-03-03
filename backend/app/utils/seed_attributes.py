"""
Seed default apparel attribute definitions.
Run: python -m app.utils.seed_attributes

Idempotent — skips existing keys.
"""

import asyncio
from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.models import AttributeDefinition


DEFAULT_ATTRIBUTES = [
    {
        "attribute_key": "material",
        "display_name": "Material",
        "input_type": "text",
        "options": None,
        "is_filterable": True,
        "is_required": True,
        "sort_order": 1,
    },
    {
        "attribute_key": "fit",
        "display_name": "Fit Type",
        "input_type": "select",
        "options": ["Regular Fit", "Slim Fit", "Relaxed Fit", "Oversized"],
        "is_filterable": True,
        "is_required": True,
        "sort_order": 2,
    },
    {
        "attribute_key": "sleeve_type",
        "display_name": "Sleeve Type",
        "input_type": "select",
        "options": ["Full Sleeve", "Half Sleeve", "Sleeveless", "3/4th Sleeve"],
        "is_filterable": True,
        "is_required": False,
        "sort_order": 3,
    },
    {
        "attribute_key": "neck_type",
        "display_name": "Neck Type",
        "input_type": "select",
        "options": ["Round Neck", "V-Neck", "Collar", "Mandarin", "Crew Neck"],
        "is_filterable": True,
        "is_required": False,
        "sort_order": 4,
    },
    {
        "attribute_key": "pattern",
        "display_name": "Pattern",
        "input_type": "select",
        "options": ["Solid", "Striped", "Printed", "Check", "Floral", "Graphic"],
        "is_filterable": True,
        "is_required": False,
        "sort_order": 5,
    },
    {
        "attribute_key": "occasion",
        "display_name": "Occasion",
        "input_type": "multiselect",
        "options": ["Casual", "Formal", "Party", "Sports", "Lounge"],
        "is_filterable": True,
        "is_required": False,
        "sort_order": 6,
    },
    {
        "attribute_key": "season",
        "display_name": "Season",
        "input_type": "multiselect",
        "options": ["Summer", "Winter", "Monsoon", "All Season"],
        "is_filterable": True,
        "is_required": False,
        "sort_order": 7,
    },
    {
        "attribute_key": "wash_care",
        "display_name": "Wash Care",
        "input_type": "text",
        "options": None,
        "is_filterable": False,
        "is_required": False,
        "sort_order": 8,
    },
    {
        "attribute_key": "country_of_origin",
        "display_name": "Country of Origin",
        "input_type": "text",
        "options": None,
        "is_filterable": False,
        "is_required": True,
        "sort_order": 9,
    },
]


async def seed_attributes():
    async with async_session_factory() as session:
        created = 0
        skipped = 0
        for attr_data in DEFAULT_ATTRIBUTES:
            result = await session.execute(
                select(AttributeDefinition).where(
                    AttributeDefinition.attribute_key == attr_data["attribute_key"]
                )
            )
            if result.scalar_one_or_none():
                skipped += 1
                continue

            attr = AttributeDefinition(**attr_data)
            session.add(attr)
            created += 1

        await session.commit()
        print(f"  [OK] Seeded {created} attribute definitions ({skipped} already existed)")


if __name__ == "__main__":
    asyncio.run(seed_attributes())
