from datetime import datetime
from typing import Optional
import base64
import json

from sqlalchemy import Select, select, or_, and_, func
from app.listings.models import Listing


def encode_cursor(values: dict) -> str:
    return base64.urlsafe_b64encode(
        json.dumps(values, sort_keys=True, default=str).encode()
    ).decode()


def decode_cursor(raw: str) -> dict | None:
    try:
        return json.loads(base64.urlsafe_b64decode(raw.encode()))
    except (json.JSONDecodeError, Exception):
        return None


class ListingQueryService:
    @staticmethod
    def _normalize_city_filters(city: Optional[str | list[str]]) -> list[str]:
        if city is None:
            return []

        raw_values = [city] if isinstance(city, str) else city
        normalized: list[str] = []
        seen: set[str] = set()
        for raw_value in raw_values:
            stripped = raw_value.strip()
            if not stripped:
                continue
            dedupe_key = stripped.lower()
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            normalized.append(stripped)
        return normalized

    @staticmethod
    def build_public_search_query(
        location: Optional[str] = None,
        city: Optional[str | list[str]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        bedrooms: Optional[int] = None,
        bathrooms: Optional[int] = None,
        parking: Optional[int] = None,
        floor: Optional[int] = None,
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
        # Only exact city strings may be applied; vague location phrases are handled upstream
        city_filters = ListingQueryService._normalize_city_filters(city)
        if city_filters:
            q = q.where(func.lower(Listing.city).in_([value.lower() for value in city_filters]))
        if min_price is not None:
            q = q.where(Listing.price >= min_price)
        if max_price is not None:
            q = q.where(Listing.price <= max_price)
        if bedrooms is not None:
            q = q.where(Listing.bedrooms >= bedrooms)
        if bathrooms is not None:
            q = q.where(Listing.bathrooms >= bathrooms)
        if parking is not None:
            q = q.where(Listing.parking >= parking)
        if floor is not None:
            q = q.where(Listing.floor == floor)
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
            q = q.order_by(Listing.created_at.desc(), Listing.id.desc())
        elif sort == "oldest":
            q = q.order_by(Listing.created_at.asc(), Listing.id.asc())
        elif sort == "price_asc":
            q = q.order_by(Listing.price.asc().nulls_last(), Listing.id.desc())
        elif sort == "price_desc":
            q = q.order_by(Listing.price.desc().nulls_last(), Listing.id.desc())
        elif sort == "area_size_asc":
            q = q.order_by(Listing.area_size.asc().nulls_last(), Listing.id.desc())
        elif sort == "area_size_desc":
            q = q.order_by(Listing.area_size.desc().nulls_last(), Listing.id.desc())
        else:
            q = q.order_by(Listing.created_at.desc(), Listing.id.desc())

        return q

    @staticmethod
    def apply_public_search_cursor(
        q: Select,
        sort: Optional[str],
        cursor_values: dict,
    ) -> Select:
        sort_key = sort or "newest"

        if sort_key == "newest":
            ca_raw = cursor_values.get("created_at")
            ci = cursor_values.get("id")
            if ca_raw and ci:
                ca = datetime.fromisoformat(ca_raw)
                q = q.where(
                    or_(
                        Listing.created_at < ca,
                        and_(Listing.created_at == ca, Listing.id < ci),
                    )
                )
        elif sort_key == "oldest":
            ca_raw = cursor_values.get("created_at")
            ci = cursor_values.get("id")
            if ca_raw and ci:
                ca = datetime.fromisoformat(ca_raw)
                q = q.where(
                    or_(
                        Listing.created_at > ca,
                        and_(Listing.created_at == ca, Listing.id > ci),
                    )
                )
        elif sort_key in ("price_desc", "area_size_desc"):
            col = Listing.price if sort_key == "price_desc" else Listing.area_size
            cv = cursor_values.get("price" if sort_key == "price_desc" else "area_size")
            ci = cursor_values.get("id")
            if cv is not None and ci:
                q = q.where(
                    or_(
                        and_(col.is_not(None), col < cv),
                        and_(col == cv, Listing.id < ci),
                        col.is_(None),
                    )
                )
            elif cv is None and ci:
                q = q.where(and_(col.is_(None), Listing.id < ci))
        elif sort_key in ("price_asc", "area_size_asc"):
            col = Listing.price if sort_key == "price_asc" else Listing.area_size
            cv = cursor_values.get("price" if sort_key == "price_asc" else "area_size")
            ci = cursor_values.get("id")
            if cv is not None and ci:
                q = q.where(
                    or_(
                        and_(col.is_not(None), col > cv),
                        and_(col == cv, Listing.id < ci),
                        col.is_(None),
                    )
                )
            elif cv is None and ci:
                q = q.where(and_(col.is_(None), Listing.id < ci))
        return q

    @staticmethod
    def make_cursor_from_item(
        item,
        sort: Optional[str] = None,
    ) -> dict:
        sort_key = sort or "newest"
        if sort_key in ("newest", "oldest"):
            return {"created_at": item.created_at.isoformat() if hasattr(item.created_at, 'isoformat') else str(item.created_at), "id": str(item.id)}
        elif sort_key in ("price_desc", "price_asc"):
            return {"price": float(item.price) if item.price is not None else None, "id": str(item.id)}
        elif sort_key in ("area_size_desc", "area_size_asc"):
            return {"area_size": float(item.area_size) if item.area_size is not None else None, "id": str(item.id)}
        return {"id": str(item.id)}
