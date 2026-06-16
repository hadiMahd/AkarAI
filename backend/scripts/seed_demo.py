"""Seed Lebanese cities and realistic demo listings for local/dev environments.

Usage (run from inside the backend container or with backend env active):
    python scripts/seed_demo.py

Re-running is safe: existing cities and demo listings are not duplicated.
To force a full re-seed, pass --reset which will delete demo listings first.
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

if __package__ is None or __package__ == "":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select, text

from app.common.database import async_session_factory
from app.common.rls import apply_rls_context_to_session
from app.cities.models import City
from app.listings.models import Listing
from app.users.models import User  # noqa: F401 — needed so SQLAlchemy can resolve FK target
from app.agencies.models import AgencyTenant  # noqa: F401 — same reason

LEBANESE_CITIES: list[tuple[str, str]] = [
    ("Beirut", "Lebanon"),
    ("Jounieh", "Lebanon"),
    ("Tripoli", "Lebanon"),
    ("Sidon", "Lebanon"),
    ("Tyre", "Lebanon"),
    ("Zahle", "Lebanon"),
    ("Byblos", "Lebanon"),
    ("Aley", "Lebanon"),
]

DEMO_LISTINGS: list[dict] = [
    {
        "title": "Modern 2BR Apartment in Hamra",
        "description": "Bright and spacious apartment near AUB with sea views. Recently renovated.",
        "property_type": "apartment",
        "listing_purpose": "rent",
        "price": 1200,
        "currency": "USD",
        "bedrooms": 2,
        "bathrooms": 1,
        "area_size": 110,
        "area_unit": "sqm",
        "furnishing": "furnished",
        "city": "Beirut",
        "country": "Lebanon",
        "address": "Hamra Street, Beirut",
        "location_text": "Hamra, Beirut",
        "status": "active",
    },
    {
        "title": "Cozy Studio in Gemmayzeh",
        "description": "Charming studio in the heart of Gemmayzeh, walking distance to restaurants and bars.",
        "property_type": "apartment",
        "listing_purpose": "rent",
        "price": 700,
        "currency": "USD",
        "bedrooms": 1,
        "bathrooms": 1,
        "area_size": 55,
        "area_unit": "sqm",
        "furnishing": "furnished",
        "city": "Beirut",
        "country": "Lebanon",
        "address": "Gemmayzeh, Beirut",
        "location_text": "Gemmayzeh, Beirut",
        "status": "active",
    },
    {
        "title": "Spacious 3BR Villa in Jounieh",
        "description": "Stunning villa with private garden and sea view terrace. 5 minutes from Jounieh Bay.",
        "property_type": "villa",
        "listing_purpose": "sale",
        "price": 450000,
        "currency": "USD",
        "bedrooms": 3,
        "bathrooms": 2,
        "area_size": 230,
        "area_unit": "sqm",
        "furnishing": "semi_furnished",
        "city": "Jounieh",
        "country": "Lebanon",
        "address": "Jounieh Highway, Jounieh",
        "location_text": "Jounieh Bay Area",
        "status": "active",
    },
    {
        "title": "2BR Apartment for Rent – Jounieh Centre",
        "description": "Well-maintained apartment in central Jounieh, close to supermarkets and schools.",
        "property_type": "apartment",
        "listing_purpose": "rent",
        "price": 900,
        "currency": "USD",
        "bedrooms": 2,
        "bathrooms": 1,
        "area_size": 100,
        "area_unit": "sqm",
        "furnishing": "unfurnished",
        "city": "Jounieh",
        "country": "Lebanon",
        "address": "Centre Ville, Jounieh",
        "location_text": "Jounieh Centre",
        "status": "active",
    },
    {
        "title": "Commercial Space in Tripoli Souks",
        "description": "Prime retail unit in the historic souks of Tripoli. High foot traffic.",
        "property_type": "commercial",
        "listing_purpose": "rent",
        "price": 1500,
        "currency": "USD",
        "bedrooms": 0,
        "bathrooms": 1,
        "area_size": 80,
        "area_unit": "sqm",
        "furnishing": "unfurnished",
        "city": "Tripoli",
        "country": "Lebanon",
        "address": "Khan El Askar, Tripoli",
        "location_text": "Tripoli Souks",
        "status": "active",
    },
    {
        "title": "Family House in Sidon",
        "description": "Detached house with large garden, ideal for families. Near Sidon Old City.",
        "property_type": "house",
        "listing_purpose": "sale",
        "price": 180000,
        "currency": "USD",
        "bedrooms": 4,
        "bathrooms": 2,
        "area_size": 280,
        "area_unit": "sqm",
        "furnishing": "unfurnished",
        "city": "Sidon",
        "country": "Lebanon",
        "address": "Abra, Sidon",
        "location_text": "Sidon",
        "status": "active",
    },
    {
        "title": "Mountain Apartment in Aley",
        "description": "Cool mountain retreat with panoramic views of Beirut and the sea. Perfect summer residence.",
        "property_type": "apartment",
        "listing_purpose": "rent",
        "price": 850,
        "currency": "USD",
        "bedrooms": 2,
        "bathrooms": 1,
        "area_size": 120,
        "area_unit": "sqm",
        "furnishing": "furnished",
        "city": "Aley",
        "country": "Lebanon",
        "address": "Main Road, Aley",
        "location_text": "Aley, Mount Lebanon",
        "status": "active",
    },
    {
        "title": "Land Plot for Sale in Byblos",
        "description": "Residential land plot with building permit. 5 minutes from Byblos Marina.",
        "property_type": "land",
        "listing_purpose": "sale",
        "price": 320000,
        "currency": "USD",
        "bedrooms": 0,
        "bathrooms": 0,
        "area_size": 600,
        "area_unit": "sqm",
        "furnishing": "unfurnished",
        "city": "Byblos",
        "country": "Lebanon",
        "address": "Jbeil Coastal Road, Byblos",
        "location_text": "Byblos Marina Area",
        "status": "active",
    },
]

DEMO_TAG = "demo-seed-v1"


async def seed_cities(session) -> int:
    inserted = 0
    for name, country in LEBANESE_CITIES:
        existing = await session.execute(select(City).where(City.name == name))
        if existing.scalar_one_or_none() is not None:
            continue
        city = City(
            id=uuid.uuid4(),
            name=name,
            country=country,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(city)
        inserted += 1
    await session.commit()
    return inserted


async def get_demo_agency_tenant_id(session) -> uuid.UUID | None:
    result = await session.execute(
        text("SELECT id FROM agency_tenants WHERE status = 'active' LIMIT 1")
    )
    row = result.fetchone()
    return row[0] if row else None


async def get_any_user_id(session) -> uuid.UUID | None:
    result = await session.execute(
        text("SELECT id FROM users WHERE status = 'active' LIMIT 1")
    )
    row = result.fetchone()
    return row[0] if row else None


async def seed_listings(session, agency_tenant_id: uuid.UUID, user_id: uuid.UUID) -> int:
    now = datetime.now(timezone.utc)
    # Phase 1: read-only — determine which listings to insert without any pending writes
    to_insert = []
    for data in DEMO_LISTINGS:
        existing = await session.execute(
            select(Listing).where(
                Listing.agency_tenant_id == agency_tenant_id,
                Listing.title == data["title"],
            )
        )
        if existing.scalar_one_or_none() is not None:
            continue
        to_insert.append(data)

    if not to_insert:
        return 0

    # Phase 2: set RLS context then add all new listings in one commit.
    # RLS context is transaction-local, so it must be set before the INSERT.
    await apply_rls_context_to_session(session, role="platform_admin", is_platform_admin=True)
    for data in to_insert:
        listing = Listing(
            id=uuid.uuid4(),
            agency_tenant_id=agency_tenant_id,
            title=data["title"],
            description=data["description"],
            property_type=data["property_type"],
            listing_purpose=data["listing_purpose"],
            price=data["price"],
            currency=data["currency"],
            bedrooms=data.get("bedrooms"),
            bathrooms=data.get("bathrooms"),
            area_size=data.get("area_size"),
            area_unit=data.get("area_unit"),
            furnishing=data.get("furnishing"),
            city=data["city"],
            country=data["country"],
            address=data.get("address"),
            location_text=data.get("location_text"),
            status=data["status"],
            created_by_user_id=user_id,
            created_at=now,
            updated_at=now,
        )
        session.add(listing)
    await session.commit()
    return len(to_insert)


async def main() -> None:
    print("=== AkarAI Demo Seed ===")

    async with async_session_factory() as session:
        await apply_rls_context_to_session(session, role="platform_admin", is_platform_admin=True)

        print("Seeding cities...")
        city_count = await seed_cities(session)
        print(f"  Inserted {city_count} new cities (skipped existing).")

        agency_tenant_id = await get_demo_agency_tenant_id(session)
        if agency_tenant_id is None:
            print("  No active agency tenant found. Skipping listing seed.")
            print("  Create an agency via the app first, then re-run this script.")
            return

        user_id = await get_any_user_id(session)
        if user_id is None:
            print("  No active user found. Skipping listing seed.")
            return

        print(f"Seeding demo listings (tenant={agency_tenant_id})...")
        listing_count = await seed_listings(session, agency_tenant_id, user_id)
        print(f"  Inserted {listing_count} new listings (skipped existing).")

    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
