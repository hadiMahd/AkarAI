from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.ai.listing_user_assistant import LeadProfileSnapshot, ListingUserAssistantService
from app.ai.schemas import ListingAssistantConversationMessage
from app.listings.models import Listing
from app.viewings.models import ListingViewingSlot


def _listing() -> Listing:
    return Listing(
        id=uuid4(),
        agency_tenant_id=uuid4(),
        title="Harbor Apartment",
        description="Sea view apartment",
        property_type="apartment",
        listing_purpose="sale",
        price=Decimal("250000"),
        currency="USD",
        bedrooms=2,
        bathrooms=2,
        area_size=Decimal("120"),
        area_unit="sqm",
        city="Beirut",
        location_text="Mar Mikhael",
        country="Lebanon",
        status="active",
    )


def _slot(*, starts_at: datetime, capacity: int = 2, reserved_count: int = 0) -> ListingViewingSlot:
    return ListingViewingSlot(
        id=uuid4(),
        listing_id=uuid4(),
        agency_tenant_id=uuid4(),
        starts_at=starts_at,
        ends_at=starts_at + timedelta(minutes=30),
        capacity=capacity,
        reserved_count=reserved_count,
        status="active",
    )


@pytest.mark.asyncio
async def test_prepare_inquiry_tool_requires_auth():
    service = ListingUserAssistantService(None, actor=None)  # type: ignore[arg-type]

    result = await service._prepare_inquiry_tool(  # noqa: SLF001
        listing=_listing(),
        user_request="Help me contact the agency",
    )

    assert result["metadata"]["auth_required"] is True
    assert result.get("pending_action") is None


@pytest.mark.asyncio
async def test_prepare_inquiry_tool_returns_confirmable_action(monkeypatch: pytest.MonkeyPatch):
    service = ListingUserAssistantService(None, actor={"user_id": str(uuid4())})  # type: ignore[arg-type]
    
    async def fake_get_user_profile():
        return LeadProfileSnapshot(
            name="Test User",
            email="test@example.com",
            phone="+96170000000",
            missing_fields=[],
        )

    monkeypatch.setattr(service, "_get_user_profile", fake_get_user_profile)

    async def fake_draft_inquiry_message(*, listing, user_request, profile):
        return "Hello, I would like more details about this property."

    monkeypatch.setattr(service, "_draft_inquiry_message", fake_draft_inquiry_message)

    result = await service._prepare_inquiry_tool(  # noqa: SLF001
        listing=_listing(),
        user_request="Please ask if the price is negotiable",
    )

    assert result["pending_action"]["type"] == "lead_inquiry"
    assert "confirm before sending" in result["assistant_message"].lower()
    assert result["pending_action"]["payload"]["message"].startswith("Hello")


@pytest.mark.asyncio
async def test_prepare_viewing_tool_returns_best_matching_slot():
    service = ListingUserAssistantService(None, actor={"user_id": str(uuid4())})  # type: ignore[arg-type]
    tomorrow = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) + timedelta(days=1)
    slots = [
        _slot(starts_at=tomorrow.replace(hour=14)),
        _slot(starts_at=tomorrow.replace(hour=18)),
    ]

    result = await service._prepare_viewing_tool(  # noqa: SLF001
        listing=_listing(),
        slots=slots,
        user_request="Book a viewing tomorrow after 5",
    )

    assert result["pending_action"]["type"] == "viewing_booking"
    assert result["pending_action"]["payload"]["viewing_slot_id"] == str(slots[1].id)
    assert result["metadata"]["matched_slot_reason"] == "best_valid_slot"


@pytest.mark.asyncio
async def test_prepare_viewing_tool_returns_clean_no_match():
    service = ListingUserAssistantService(None, actor={"user_id": str(uuid4())})  # type: ignore[arg-type]
    tomorrow = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) + timedelta(days=1)
    slots = [_slot(starts_at=tomorrow.replace(hour=10))]

    result = await service._prepare_viewing_tool(  # noqa: SLF001
        listing=_listing(),
        slots=slots,
        user_request="Book a viewing tomorrow evening",
    )

    assert result.get("pending_action") is None
    assert result["metadata"]["slot_match"] == "none"


@pytest.mark.asyncio
async def test_prepare_viewing_tool_ignores_full_slots():
    service = ListingUserAssistantService(None, actor={"user_id": str(uuid4())})  # type: ignore[arg-type]
    tomorrow = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) + timedelta(days=1)
    slots = [
        _slot(starts_at=tomorrow.replace(hour=18), capacity=1, reserved_count=1),
        _slot(starts_at=tomorrow.replace(hour=19), capacity=2, reserved_count=0),
    ]

    result = await service._prepare_viewing_tool(  # noqa: SLF001
        listing=_listing(),
        slots=slots,
        user_request="Book a viewing tomorrow after 5",
    )

    assert result["pending_action"]["payload"]["viewing_slot_id"] == str(slots[1].id)


@pytest.mark.asyncio
async def test_prepare_viewing_tool_uses_recent_assistant_slot_for_generic_confirmation():
    service = ListingUserAssistantService(None, actor={"user_id": str(uuid4())})  # type: ignore[arg-type]
    tomorrow = datetime.now(timezone.utc).replace(minute=15, second=0, microsecond=0) + timedelta(days=1)
    slot = _slot(starts_at=tomorrow.replace(hour=11))

    result = await service._prepare_viewing_tool(  # noqa: SLF001
        listing=_listing(),
        slots=[slot],
        user_request="yes just me",
        conversation_messages=[
            ListingAssistantConversationMessage(
                role="assistant",
                content=f"You can see it on {service._format_slot_label(slot)}.",  # noqa: SLF001
            )
        ],
    )

    assert result["pending_action"]["payload"]["viewing_slot_id"] == str(slot.id)
    assert result["pending_action"]["payload"]["scheduled_label"] == service._format_slot_label(slot)  # noqa: SLF001


@pytest.mark.asyncio
async def test_get_active_slots_filters_past_and_full_slots(monkeypatch: pytest.MonkeyPatch):
    service = ListingUserAssistantService(None, actor={"user_id": str(uuid4())})  # type: ignore[arg-type]
    future_slot = _slot(starts_at=datetime.now(timezone.utc).replace(second=0, microsecond=0) + timedelta(hours=3))

    async def fake_list_bookable_by_listing(_listing_id):
        return [future_slot]

    monkeypatch.setattr(service._slot_repo, "list_bookable_by_listing", fake_list_bookable_by_listing)

    result = await service._get_active_slots(uuid4())  # noqa: SLF001

    assert result == [future_slot]


def test_response_from_agent_result_prefers_viewing_tool_payload():
    service = ListingUserAssistantService(None, actor={"user_id": str(uuid4())})  # type: ignore[arg-type]
    tool_payload = {
        "assistant_message": "I found a viewing slot on Thu Jun 18 at 11:15 AM UTC. Review it and confirm before booking.",
        "pending_action": {
            "type": "viewing_booking",
            "payload": {
                "viewing_slot_id": str(uuid4()),
                "scheduled_start_at": "2026-06-18T11:15:00Z",
                "scheduled_end_at": "2026-06-18T12:15:00Z",
                "notes": "book it",
            },
        },
        "metadata": {"intent": "viewing_booking", "tool": "schedule_viewing"},
    }
    result = service._response_from_agent_result(  # noqa: SLF001
        {
            "messages": [
                SimpleNamespace(type="tool", content=json.dumps(tool_payload)),
                SimpleNamespace(type="ai", content="I couldn't schedule it for that window."),
            ]
        },
        {"schedule_viewing": object()},
    )

    assert result.assistant_message.startswith("I found a viewing slot")
    assert result.pending_action is not None
    assert result.pending_action.type == "viewing_booking"
