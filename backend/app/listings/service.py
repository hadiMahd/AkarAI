from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.domain import (
    LISTING_STATUS_TRANSITIONS,
    VALID_LISTING_STATUSES,
    LISTING_STATUS_ACTIVE,
    LISTING_STATUS_INACTIVE,
    LISTING_STATUS_ARCHIVED,
)
from app.common.exceptions import NotFoundError, ForbiddenError, ValidationError, ServiceUnavailableError
from app.common.pagination import PaginationRequest, PaginationResult
from app.common.tenant import TenantContext, require_tenant, ensure_tenant_match
from app.common.cache import invalidate_listing_search_cache
from app.common.events import write_domain_event_log, write_media_audit_log, publish_outbox_event_in_session
from app.common.media_moderation import run_nsfw_moderation
from app.common.storage import presigned_get_url, get_media_bucket
from app.listings.models import Listing, ListingPhotoMetadata, ListingPhotoDerivative
from app.listings.repository import ListingRepository, ListingPhotoRepository, ListingPhotoDerivativeRepository


class ListingService:
    def __init__(self, session: AsyncSession, tenant: Optional[TenantContext] = None):
        self._session = session
        self._tenant = tenant
        self._repo = ListingRepository(session, tenant)
        self._photo_repo = ListingPhotoRepository(session, tenant)

    async def list_tenant_listings(self, pagination: PaginationRequest) -> PaginationResult:
        ctx = require_tenant(self._tenant)
        items, total = await self._repo.list_by_tenant(
            ctx.tenant_id, offset=pagination.offset, limit=pagination.limit
        )
        return PaginationResult(items=items, total=total, pagination=pagination)

    async def get_listing(self, listing_id: UUID) -> Listing:
        ctx = require_tenant(self._tenant)
        listing = await self._repo.get_by_id(listing_id)
        if listing is None:
            raise NotFoundError(detail="Listing not found")
        ensure_tenant_match(self._tenant, listing.agency_tenant_id)
        return listing

    async def read_only_get_listing(self, listing_id: UUID) -> Listing | None:
        """Read-only lookup for the agency assistant. No RBAC check beyond
        the existing tenant context. Returns None if the listing is not in
        the current tenant, so the assistant can refuse gracefully.
        """
        ctx = require_tenant(self._tenant)
        listing = await self._repo.get_by_id(listing_id)
        if listing is None:
            return None
        if listing.agency_tenant_id != ctx.tenant_id:
            return None
        return listing

    async def read_only_search_listings(
        self,
        *,
        query: str | None = None,
        status: str | None = None,
        limit: int = 5,
    ) -> list[Listing]:
        """Read-only tenant-scoped search for the agency assistant.

        Only supports lightweight substring-style filters; the assistant
        tool must never be a backdoor into the broader search subsystem.
        """
        from sqlalchemy import or_, select

        from app.listings.models import Listing

        ctx = require_tenant(self._tenant)
        limit = max(1, min(limit, settings.agency_ai_max_tool_listing_results))
        stmt = select(Listing).where(Listing.agency_tenant_id == ctx.tenant_id)
        if status:
            stmt = stmt.where(Listing.status == status)
        if query:
            like = f"%{query[:80]}%"
            stmt = stmt.where(
                or_(
                    Listing.title.ilike(like),
                    Listing.address.ilike(like),
                    Listing.city.ilike(like),
                    Listing.location_text.ilike(like),
                )
            )
        stmt = stmt.order_by(Listing.updated_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_listing(self, data: dict) -> Listing:
        ctx = require_tenant(self._tenant)
        if ctx.role == "support_employee":
            raise ForbiddenError(detail="Support employees cannot create listings")

        listing = Listing(
            agency_tenant_id=ctx.tenant_id,
            title=data["title"],
            description=data.get("description"),
            property_type=data.get("property_type"),
            listing_purpose=data.get("listing_purpose"),
            price=data.get("price"),
            currency=data.get("currency"),
            bedrooms=data.get("bedrooms"),
            bathrooms=data.get("bathrooms"),
            area_size=data.get("area_size"),
            area_unit=data.get("area_unit"),
            furnishing=data.get("furnishing"),
            location_text=data.get("location_text"),
            address=data.get("address"),
            city=data.get("city"),
            country=data.get("country"),
            status=data.get("status", "inactive"),
            created_by_user_id=ctx.actor_id,
        )
        if listing.status not in VALID_LISTING_STATUSES:
            raise ValidationError(detail=f"Invalid listing status: {listing.status}")
        listing = await self._repo.create(listing)
        await invalidate_listing_search_cache(str(listing.id))
        await write_domain_event_log(
            self._session, "listing.created",
            aggregate_type="listing", aggregate_id=str(listing.id),
            agency_tenant_id=ctx.tenant_id, actor_user_id=ctx.actor_id,
            payload={"title": listing.title, "status": listing.status},
        )
        return listing

    async def update_listing(self, listing_id: UUID, data: dict) -> Listing:
        ctx = require_tenant(self._tenant)
        listing = await self._repo.get_by_id(listing_id)
        if listing is None:
            raise NotFoundError(detail="Listing not found")
        ensure_tenant_match(self._tenant, listing.agency_tenant_id)

        for field in (
            "title",
            "description",
            "property_type",
            "listing_purpose",
            "price",
            "currency",
            "bedrooms",
            "bathrooms",
            "area_size",
            "area_unit",
            "furnishing",
            "location_text",
            "address",
            "city",
            "country",
        ):
            if field in data and data[field] is not None:
                setattr(listing, field, data[field])

        if "status" in data and data["status"] is not None:
            new_status = data["status"]
            if new_status not in VALID_LISTING_STATUSES:
                raise ValidationError(detail=f"Invalid listing status: {new_status}")
            allowed = LISTING_STATUS_TRANSITIONS.get(listing.status, [])
            if new_status not in allowed:
                raise ValidationError(
                    detail=f"Cannot transition from '{listing.status}' to '{new_status}'"
                )
            listing.status = new_status
            if new_status == LISTING_STATUS_ARCHIVED:
                listing.archived_at = datetime.now(timezone.utc)

        listing.updated_by_user_id = ctx.actor_id
        await self._session.flush()
        await invalidate_listing_search_cache(str(listing_id))
        await write_domain_event_log(
            self._session, "listing.updated",
            aggregate_type="listing", aggregate_id=str(listing_id),
            agency_tenant_id=ctx.tenant_id, actor_user_id=ctx.actor_id,
            payload={"status": listing.status},
        )
        return listing

    async def archive_listing(self, listing_id: UUID) -> None:
        ctx = require_tenant(self._tenant)
        listing = await self._repo.get_by_id(listing_id)
        if listing is None:
            raise NotFoundError(detail="Listing not found")
        ensure_tenant_match(self._tenant, listing.agency_tenant_id)
        if listing.status == LISTING_STATUS_ARCHIVED:
            return

        listing.status = LISTING_STATUS_ARCHIVED
        listing.archived_at = datetime.now(timezone.utc)
        listing.updated_by_user_id = ctx.actor_id
        await self._session.flush()
        await invalidate_listing_search_cache(str(listing_id))
        await write_domain_event_log(
            self._session, "listing.archived",
            aggregate_type="listing", aggregate_id=str(listing_id),
            agency_tenant_id=ctx.tenant_id, actor_user_id=ctx.actor_id,
        )

    async def list_photos(self, listing_id: UUID) -> list[dict]:
        ctx = require_tenant(self._tenant)
        listing = await self._repo.get_by_id(listing_id)
        if listing is None:
            raise NotFoundError(detail="Listing not found")
        ensure_tenant_match(self._tenant, listing.agency_tenant_id)

        photos = await self._photo_repo.list_by_listing(listing_id)

        derivative_repo = ListingPhotoDerivativeRepository(self._session, self._tenant)
        photo_ids = [p.id for p in photos]
        all_derivs = await derivative_repo.list_public_safe_by_photos(photo_ids)
        deriv_map: dict[UUID, ListingPhotoDerivative] = {}
        for d in all_derivs:
            if d.listing_photo_metadata_id not in deriv_map:
                deriv_map[d.listing_photo_metadata_id] = d

        bucket = get_media_bucket()
        result = []
        for photo in photos:
            photo_dict = {
                "id": photo.id,
                "listing_id": photo.listing_id,
                "agency_tenant_id": photo.agency_tenant_id,
                "object_key": photo.object_key,
                "caption": photo.caption,
                "alt_text": photo.alt_text,
                "display_order": photo.display_order,
                "status": photo.status,
                "content_type": photo.content_type,
                "file_size_bytes": photo.file_size_bytes,
                "width": photo.width,
                "height": photo.height,
                "moderation_label": photo.moderation_label,
                "moderation_score": photo.moderation_score,
                "quality_score": photo.quality_score,
                "created_at": photo.created_at,
                "updated_at": photo.updated_at,
            }

            derivative = deriv_map.get(photo.id)
            if derivative:
                photo_dict["preview_url"] = presigned_get_url(bucket, derivative.object_key, expires_seconds=3600)
            else:
                photo_dict["preview_url"] = presigned_get_url(bucket, photo.object_key, expires_seconds=3600)

            result.append(photo_dict)

        return result

    async def create_photo(self, listing_id: UUID, data: dict) -> ListingPhotoMetadata:
        ctx = require_tenant(self._tenant)
        listing = await self._repo.get_by_id(listing_id)
        if listing is None:
            raise NotFoundError(detail="Listing not found")
        ensure_tenant_match(self._tenant, listing.agency_tenant_id)

        order = data.get("display_order", 0)
        if order == 0:
            max_order = await self._photo_repo.get_max_display_order(listing_id)
            order = max_order + 1

        photo = ListingPhotoMetadata(
            listing_id=listing_id,
            agency_tenant_id=ctx.tenant_id,
            object_key=data["object_key"],
            caption=data.get("caption"),
            alt_text=data.get("alt_text"),
            display_order=order,
            status="active",
        )
        photo = await self._photo_repo.create(photo)
        await write_domain_event_log(
            self._session, "listing.photo_added",
            aggregate_type="listing", aggregate_id=str(listing_id),
            agency_tenant_id=ctx.tenant_id, actor_user_id=ctx.actor_id,
            payload={"photo_id": str(photo.id)},
        )
        return photo

    async def validate_photo_preflight(
        self,
        file_bytes: bytes,
        content_type: str | None = None,
    ) -> dict:
        ctx = require_tenant(self._tenant)
        if ctx.role == "support_employee":
            raise ForbiddenError(detail="Support employees cannot upload photos")

        from app.common.media import validate_media_upload, MediaValidationError

        try:
            media_metadata = validate_media_upload(file_bytes, content_type)
        except MediaValidationError as exc:
            return {
                "safe": False,
                "rejection_reason": "invalid_file",
                "message": str(exc),
                "content_type": content_type,
            }

        moderation_result = await run_nsfw_moderation(file_bytes, content_type=content_type)
        if moderation_result["rejected"]:
            label = moderation_result["label"]
            if label == "nsfw":
                message = "This image was flagged as unsafe and cannot be uploaded."
                reason = "nsfw"
            else:
                message = "Image safety could not be verified right now. Try again later."
                reason = "moderation_failed"

            return {
                "safe": False,
                "rejection_reason": reason,
                "message": message,
                **media_metadata,
                "moderation_label": label,
                "moderation_score": moderation_result["score"],
            }

        return {
            "safe": True,
            "rejection_reason": None,
            "message": "Image is safe to upload.",
            **media_metadata,
            "moderation_label": moderation_result["label"],
            "moderation_score": moderation_result["score"],
        }

    async def update_photo(self, listing_id: UUID, photo_id: UUID, data: dict) -> ListingPhotoMetadata:
        ctx = require_tenant(self._tenant)
        photo = await self._photo_repo.get_by_id(photo_id)
        if photo is None:
            raise NotFoundError(detail="Photo metadata not found")
        if str(photo.listing_id) != str(listing_id):
            raise NotFoundError(detail="Photo not found for this listing")
        ensure_tenant_match(self._tenant, photo.agency_tenant_id)

        if "caption" in data:
            photo.caption = data["caption"]
        if "alt_text" in data:
            photo.alt_text = data["alt_text"]
        if "display_order" in data and data["display_order"] is not None:
            photo.display_order = data["display_order"]

        await self._session.flush()
        await write_domain_event_log(
            self._session, "listing.photo_updated",
            aggregate_type="listing", aggregate_id=str(listing_id),
            agency_tenant_id=photo.agency_tenant_id, actor_user_id=ctx.actor_id,
            payload={"photo_id": str(photo_id)},
        )
        return photo

    async def remove_photo(self, listing_id: UUID, photo_id: UUID) -> None:
        ctx = require_tenant(self._tenant)
        photo = await self._photo_repo.get_by_id(photo_id)
        if photo is None:
            raise NotFoundError(detail="Photo metadata not found")
        if str(photo.listing_id) != str(listing_id):
            raise NotFoundError(detail="Photo not found for this listing")
        ensure_tenant_match(self._tenant, photo.agency_tenant_id)

        photo.status = "removed"
        await self._session.flush()
        await write_domain_event_log(
            self._session, "listing.photo_removed",
            aggregate_type="listing", aggregate_id=str(listing_id),
            agency_tenant_id=photo.agency_tenant_id, actor_user_id=ctx.actor_id,
            payload={"photo_id": str(photo_id)},
        )

    async def upload_photo(
        self,
        listing_id: UUID,
        file_bytes: bytes,
        filename: str,
        content_type: str | None = None,
        caption: str | None = None,
        alt_text: str | None = None,
        display_order: int | None = None,
    ) -> ListingPhotoMetadata:
        """Upload a listing photo with validation and storage.

        Atomic flow:
        1. Validate file and listing ownership
        2. Upload to MinIO FIRST (before DB transaction)
        3. Create photo metadata record and outbox event in same session
        4. Commit transaction (both records persist or neither does)
        5. If MinIO upload fails, no DB record is created
        """
        ctx = require_tenant(self._tenant)
        if ctx.role == "support_employee":
            raise ForbiddenError(detail="Support employees cannot upload photos")

        # Validate listing exists and belongs to tenant
        listing = await self._repo.get_by_id(listing_id)
        if listing is None:
            raise NotFoundError(detail="Listing not found")
        ensure_tenant_match(self._tenant, listing.agency_tenant_id)

        # Validate the uploaded file
        from app.common.media import validate_media_upload, MediaValidationError
        try:
            media_metadata = validate_media_upload(file_bytes, content_type)
        except MediaValidationError as e:
            raise ValidationError(detail=str(e))

        # Generate object key and upload to MinIO FIRST
        from app.common.storage import (
            generate_original_object_key,
            get_media_bucket,
            upload_object,
            ensure_bucket_exists,
        )

        bucket = get_media_bucket()
        ensure_bucket_exists(bucket)
        object_key = generate_original_object_key(
            str(ctx.tenant_id), str(listing_id), filename
        )

        # Upload to MinIO FIRST - if this fails, no DB record is created
        try:
            upload_object(bucket, object_key, file_bytes, media_metadata["content_type"])
        except Exception as e:
            raise ServiceUnavailableError(
                detail="We couldn't store this image right now. Try again in a moment.",
                error_code="PHOTO_STORAGE_FAILED",
            ) from e

        # Calculate display order
        if display_order is None or display_order == 0:
            max_order = await self._photo_repo.get_max_display_order(listing_id)
            display_order = max_order + 1

        try:
            # Create photo metadata record
            photo = ListingPhotoMetadata(
                listing_id=listing_id,
                agency_tenant_id=ctx.tenant_id,
                object_key=object_key,
                caption=caption,
                alt_text=alt_text,
                display_order=display_order,
                status="uploaded",
                content_type=media_metadata["content_type"],
                file_size_bytes=media_metadata["file_size_bytes"],
                width=media_metadata.get("width"),
                height=media_metadata.get("height"),
            )
            photo = await self._photo_repo.create(photo)

            # Create outbox event in the SAME session (atomic with photo record)
            idempotency_key = f"upload-{photo.id}-{uuid4().hex[:8]}"
            await publish_outbox_event_in_session(
                self._session,
                event_name="listing.image_uploaded",
                payload={
                    "listing_id": str(listing_id),
                    "listing_photo_id": str(photo.id),
                    "agency_tenant_id": str(ctx.tenant_id),
                    "object_key": object_key,
                    "content_type": media_metadata["content_type"],
                    "file_size_bytes": media_metadata["file_size_bytes"],
                    "uploaded_by_user_id": str(ctx.actor_id) if ctx.actor_id else None,
                },
                idempotency_key=idempotency_key,
                aggregate_type="listing_photo",
                aggregate_id=str(photo.id),
            )

            # Write audit log in same session
            await write_media_audit_log(
                self._session,
                event_name="listing.image_uploaded",
                agency_tenant_id=ctx.tenant_id,
                listing_photo_metadata_id=photo.id,
                result="uploaded",
                details={
                    "content_type": media_metadata["content_type"],
                    "file_size_bytes": media_metadata["file_size_bytes"],
                },
                actor_user_id=ctx.actor_id,
            )

            # Write domain event log in same session
            await write_domain_event_log(
                self._session,
                "listing.image_uploaded",
                aggregate_type="listing_photo",
                aggregate_id=str(photo.id),
                agency_tenant_id=ctx.tenant_id,
                actor_user_id=ctx.actor_id,
                payload={"photo_id": str(photo.id), "listing_id": str(listing_id)},
            )

            return photo
        except Exception as e:
            from app.common.storage import delete_object

            try:
                delete_object(bucket, object_key)
            except Exception:
                pass
            raise ServiceUnavailableError(detail=f"Failed to persist photo metadata: {e}") from e


async def build_thumbnail_map(
    session: AsyncSession,
    listing_ids: list[UUID],
) -> dict[UUID, str | None]:
    if not listing_ids:
        return {}

    from app.listings.repository import ListingPhotoRepository, ListingPhotoDerivativeRepository

    photo_repo = ListingPhotoRepository(session)
    derivative_repo = ListingPhotoDerivativeRepository(session)

    first_photos = await photo_repo.get_first_public_safe_for_listings(listing_ids)
    if not first_photos:
        return {lid: None for lid in listing_ids}

    photo_ids = [p.id for p in first_photos.values()]
    all_derivs = await derivative_repo.list_public_safe_by_photos(photo_ids)

    deriv_map: dict[UUID, list[ListingPhotoDerivative]] = {}
    for d in all_derivs:
        deriv_map.setdefault(d.listing_photo_metadata_id, []).append(d)

    bucket = get_media_bucket()
    thumb_map: dict[UUID, str | None] = {}
    for lid, photo in first_photos.items():
        photo_derivs = deriv_map.get(photo.id, [])
        if photo_derivs:
            thumb_map[lid] = presigned_get_url(bucket, photo_derivs[0].object_key, expires_seconds=3600)
        else:
            thumb_map[lid] = None

    for lid in listing_ids:
        thumb_map.setdefault(lid, None)

    return thumb_map
