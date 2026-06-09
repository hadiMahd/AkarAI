from typing import Optional

from sqlalchemy import Select, select, or_

from app.listings.models import Listing


class ListingQueryService:

    @staticmethod
    def build_public_search_query(
        location: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        bedrooms: Optional[int] = None,
        bathrooms: Optional[int] = None,
        property_type: Optional[str] = None,
        listing_purpose: Optional[str] = None,
        furnishing: Optional[str] = None,
        min_area_size: Optional[float] = None,
        max_area_size: Optional[float] = None,
        sort: Optional[str] = None,
    ) -> Select:
        q = select(Listing).where(Listing.status == "active")

        if location:
            q = q.where(
                or_(
                    Listing.location_text.ilike(f"%{location}%"),
                    Listing.city.ilike(f"%{location}%"),
                    Listing.address.ilike(f"%{location}%"),
                )
            )
        if min_price is not None:
            q = q.where(Listing.price >= min_price)
        if max_price is not None:
            q = q.where(Listing.price <= max_price)
        if bedrooms is not None:
            q = q.where(Listing.bedrooms == bedrooms)
        if bathrooms is not None:
            q = q.where(Listing.bathrooms == bathrooms)
        if property_type:
            q = q.where(Listing.property_type == property_type)
        if listing_purpose:
            q = q.where(Listing.listing_purpose == listing_purpose)
        if furnishing:
            q = q.where(Listing.furnishing == furnishing)
        if min_area_size is not None:
            q = q.where(Listing.area_size >= min_area_size)
        if max_area_size is not None:
            q = q.where(Listing.area_size <= max_area_size)

        if sort == "newest":
            q = q.order_by(Listing.created_at.desc())
        elif sort == "price_asc":
            q = q.order_by(Listing.price.asc())
        elif sort == "price_desc":
            q = q.order_by(Listing.price.desc())
        elif sort == "area_size_asc":
            q = q.order_by(Listing.area_size.asc())
        elif sort == "area_size_desc":
            q = q.order_by(Listing.area_size.desc())
        else:
            q = q.order_by(Listing.created_at.desc())

        return q
