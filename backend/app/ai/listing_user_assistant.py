from __future__ import annotations

import contextlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Annotated, Any, TypedDict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.schemas import (
    ListingAssistantConversationMessage,
    ListingAssistantMessageRequest,
    ListingAssistantPendingAction,
    ListingAssistantResponse,
)
from app.common.config import settings
from app.common.exceptions import NotFoundError, ServiceUnavailableError
from app.listings.models import Listing
from app.listings.repository import ListingRepository
from app.users.repository import UsersRepository
from app.users.service import UsersService
from app.viewings.models import ListingViewingSlot
from app.viewings.repository import ViewingSlotRepository

logger = logging.getLogger(__name__)

_OUT_OF_SCOPE_PATTERNS = (
    r"\bcompare\b",
    r"\bneighborhood\b",
    r"\bschool\b",
    r"\binvestment advice\b",
    r"\bmortgage\b",
    r"\banother listing\b",
    r"\bmarket trend\b",
)

_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


class AgentState(TypedDict):
    messages: list[Any]


@dataclass(slots=True)
class LeadProfileSnapshot:
    name: str | None
    email: str | None
    phone: str | None
    missing_fields: list[str]

    @property
    def is_complete(self) -> bool:
        return not self.missing_fields


class ListingUserAssistantService:
    def __init__(self, session: AsyncSession, actor: dict | None = None):
        self._session = session
        self._actor = actor
        self._listing_repo = ListingRepository(session)
        self._slot_repo = ViewingSlotRepository(session)

    async def send_message(
        self,
        listing_id: UUID,
        body: ListingAssistantMessageRequest,
    ) -> ListingAssistantResponse:
        listing = await self._get_active_listing(listing_id)
        slots = await self._get_active_slots(listing_id)

        if self._is_out_of_scope(body.message):
            return ListingAssistantResponse(
                assistant_message=(
                    "I can only help with this listing's facts, prepare an inquiry, or prepare a viewing booking for this listing."
                ),
                metadata={"scope": "listing_only", "intent": "refusal"},
            )

        graph, compiled_tools = self._build_agent_graph(
            listing=listing,
            slots=slots,
            conversation_messages=body.conversation_messages[-8:],
        )
        messages = await self._build_conversation_messages(body)
        config = {
            "run_name": "listing_user_assistant.agent",
            "metadata": {
                "listing_id": str(listing.id),
                "actor_user_id": self._actor.get("user_id") if self._actor else None,
            },
            "tags": ["listing-assistant", "langgraph"],
        }

        try:
            with self._langsmith_trace_context():
                result = await graph.ainvoke({"messages": messages}, config=config)
        except ServiceUnavailableError:
            raise
        except Exception as exc:
            logger.exception("Listing assistant agent run failed")
            raise ServiceUnavailableError(detail="Listing assistant agent is unavailable right now.") from exc

        response = self._response_from_agent_result(result, compiled_tools)
        if response.pending_action is None:
            response.metadata.setdefault("intent", "listing_facts")
        return response

    def _build_agent_graph(
        self,
        *,
        listing: Listing,
        slots: list[ListingViewingSlot],
        conversation_messages: list[ListingAssistantConversationMessage],
    ):
        try:
            from langchain_core.messages import SystemMessage
            from langchain_core.tools import tool
            from langchain_openai import AzureChatOpenAI
            from langgraph.graph import END, START, StateGraph
            from langgraph.graph.message import add_messages
            from langgraph.prebuilt import ToolNode, tools_condition
        except Exception as exc:
            raise ServiceUnavailableError(
                detail="Listing assistant agent dependencies are not installed."
            ) from exc

        # LangGraph resolves Annotated metadata for TypedDict state via module globals.
        globals()["add_messages"] = add_messages

        if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
            raise ServiceUnavailableError(detail="Azure OpenAI is not configured for the listing assistant.")
        if not settings.azure_openai_chat_deployment:
            raise ServiceUnavailableError(detail="Azure OpenAI chat deployment is not configured.")

        llm = AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint.rstrip("/"),
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_deployment=settings.azure_openai_chat_deployment,
            temperature=0.1,
        )

        @tool
        async def get_listing_context() -> str:
            """Get the current listing facts and active viewing slots for this listing only."""
            return json.dumps(
                {
                    "assistant_message": "Loaded current listing context.",
                    "metadata": {"intent": "listing_facts", "tool": "get_listing_context"},
                    "listing": self._serialize_listing(listing),
                    "active_viewing_slots": [self._serialize_slot(slot) for slot in slots],
                }
            )

        @tool
        async def send_inquiry(user_request: str) -> str:
            """Prepare a confirmable inquiry draft for this listing. This tool does not send anything."""
            return json.dumps(await self._prepare_inquiry_tool(listing=listing, user_request=user_request))

        @tool
        async def schedule_viewing(user_request: str) -> str:
            """Prepare a confirmable viewing booking for this listing. This tool does not book anything."""
            return json.dumps(
                await self._prepare_viewing_tool(
                    listing=listing,
                    slots=slots,
                    user_request=user_request,
                    conversation_messages=conversation_messages,
                )
            )

        tools = [get_listing_context, send_inquiry, schedule_viewing]
        bound_llm = llm.bind_tools(tools)

        async def call_model(state: AgentState) -> dict[str, list[Any]]:
            system_prompt = self._system_prompt()
            response = await bound_llm.ainvoke(
                [SystemMessage(content=system_prompt), *state["messages"]],
                config={
                    "run_name": "listing_user_assistant.model",
                    "metadata": {"listing_id": str(listing.id)},
                    "tags": ["listing-assistant", "azure-openai"],
                },
            )
            return {"messages": [response]}

        class _GraphState(TypedDict):
            messages: Annotated[list[Any], add_messages]

        graph_builder = StateGraph(_GraphState)
        graph_builder.add_node("agent", call_model)
        graph_builder.add_node("tools", ToolNode(tools))
        graph_builder.add_edge(START, "agent")
        graph_builder.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
        graph_builder.add_edge("tools", "agent")
        return graph_builder.compile(), {tool.name: tool for tool in tools}

    async def _build_conversation_messages(self, body: ListingAssistantMessageRequest) -> list[Any]:
        try:
            from langchain_core.messages import AIMessage, HumanMessage
        except Exception as exc:
            raise ServiceUnavailableError(
                detail="Listing assistant agent dependencies are not installed."
            ) from exc

        messages: list[Any] = []
        for item in body.conversation_messages[-8:]:
            content = item.content[: settings.ai_guardrails_max_message_chars].strip()
            if not content:
                continue
            if item.role == "assistant":
                messages.append(AIMessage(content=content))
            else:
                messages.append(HumanMessage(content=content))

        if not body.conversation_messages or body.conversation_messages[-1].content.strip() != body.message.strip():
            messages.append(HumanMessage(content=body.message.strip()))
        return messages

    def _response_from_agent_result(
        self,
        result: dict[str, Any],
        compiled_tools: dict[str, Any],
    ) -> ListingAssistantResponse:
        messages = list(result.get("messages") or [])
        assistant_message = ""
        pending_action: ListingAssistantPendingAction | None = None
        metadata: dict[str, Any] = {}
        latest_action_tool_payload: dict[str, Any] | None = None

        for message in reversed(messages):
            parsed = self._maybe_parse_tool_payload(message)
            if parsed:
                parsed_metadata = parsed.get("metadata") or {}
                metadata.update(parsed_metadata)
                pending = parsed.get("pending_action")
                if pending and pending_action is None:
                    pending_action = ListingAssistantPendingAction.model_validate(pending)
                if parsed_metadata.get("tool") in {"send_inquiry", "schedule_viewing"}:
                    latest_action_tool_payload = parsed
                    assistant_message = parsed.get("assistant_message", "") or assistant_message
                    continue
                assistant_message = assistant_message or parsed.get("assistant_message", "")
            if getattr(message, "type", "") == "ai":
                content = self._message_text(message)
                if content and not assistant_message:
                    assistant_message = content
                tool_calls = getattr(message, "tool_calls", None) or []
                if tool_calls and "tool_calls" not in metadata:
                    metadata["tool_calls"] = [call.get("name") for call in tool_calls if call.get("name") in compiled_tools]

        if latest_action_tool_payload is not None:
            assistant_message = latest_action_tool_payload.get("assistant_message", "") or assistant_message

        if not assistant_message:
            assistant_message = "I couldn't produce a listing assistant response."

        return ListingAssistantResponse(
            assistant_message=assistant_message,
            pending_action=pending_action,
            metadata=metadata,
        )

    def _maybe_parse_tool_payload(self, message: Any) -> dict[str, Any] | None:
        if getattr(message, "type", "") != "tool":
            return None
        content = self._message_text(message)
        if not content:
            return None
        try:
            payload = json.loads(content)
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None
        return payload

    def _message_text(self, message: Any) -> str:
        content = getattr(message, "content", None)
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                text = getattr(item, "text", None)
                if text:
                    parts.append(str(text).strip())
                elif isinstance(item, dict) and item.get("text"):
                    parts.append(str(item["text"]).strip())
                else:
                    parts.append(str(item).strip())
            return " ".join(part for part in parts if part).strip()
        return str(content or "").strip()

    async def _prepare_inquiry_tool(
        self,
        *,
        listing: Listing,
        user_request: str,
    ) -> dict[str, Any]:
        if not self._actor:
            return {
                "assistant_message": "Sign in to prepare an inquiry for this listing.",
                "metadata": {"intent": "lead_inquiry", "auth_required": True, "tool": "send_inquiry"},
            }

        profile = await self._get_user_profile()
        if profile is None:
            return {
                "assistant_message": "Sign in again to continue with an inquiry for this listing.",
                "metadata": {"intent": "lead_inquiry", "auth_required": True, "tool": "send_inquiry"},
            }

        if not profile.is_complete:
            return {
                "assistant_message": "Complete your profile with your name and at least one contact method before sending an inquiry.",
                "metadata": {
                    "intent": "lead_inquiry",
                    "profile_incomplete": True,
                    "missing_fields": profile.missing_fields,
                    "tool": "send_inquiry",
                },
            }

        draft = await self._draft_inquiry_message(listing=listing, user_request=user_request, profile=profile)
        return {
            "assistant_message": "I prepared an inquiry draft for this listing. Review it and confirm before sending.",
            "pending_action": {
                "type": "lead_inquiry",
                "payload": {"message": draft},
            },
            "metadata": {
                "intent": "lead_inquiry",
                "tool": "send_inquiry",
                "profile_name": profile.name,
                "profile_email": profile.email,
                "profile_phone": profile.phone,
            },
        }

    async def _prepare_viewing_tool(
        self,
        *,
        listing: Listing,
        slots: list[ListingViewingSlot],
        user_request: str,
        conversation_messages: list[ListingAssistantConversationMessage] | None = None,
    ) -> dict[str, Any]:
        if not self._actor:
            return {
                "assistant_message": "Sign in to prepare a viewing request for this listing.",
                "metadata": {"intent": "viewing_booking", "auth_required": True, "tool": "schedule_viewing"},
            }

        if not slots:
            return {
                "assistant_message": "There are no active viewing slots for this listing right now.",
                "metadata": {"intent": "viewing_booking", "no_slots": True, "tool": "schedule_viewing"},
            }

        matched = None
        if self._is_generic_booking_confirmation(user_request):
            matched = self._match_slot_from_conversation(conversation_messages or [], slots)

        if matched is None:
            matched = self._match_slot(user_request, slots)

        if matched is None:
            available_slots = self._available_slot_labels(slots)
            assistant_message = "I couldn't find a matching viewing slot. Try a different day or time window."
            if available_slots:
                assistant_message = (
                    "I couldn't match that request to a bookable slot. "
                    f"Available slots right now: {', '.join(available_slots)}. "
                    "Tell me one of those times or say 'book the next available slot'."
                )
            return {
                "assistant_message": assistant_message,
                "metadata": {"intent": "viewing_booking", "slot_match": "none", "tool": "schedule_viewing"},
            }

        return {
            "assistant_message": f"I found a viewing slot on {self._format_slot_start(matched.starts_at)}. Review it and confirm before booking.",
            "pending_action": {
                "type": "viewing_booking",
                "payload": {
                    "viewing_slot_id": str(matched.id),
                    "scheduled_start_at": matched.starts_at.isoformat(),
                    "scheduled_end_at": matched.ends_at.isoformat(),
                    "scheduled_label": self._format_slot_label(matched),
                    "notes": user_request.strip()[:500],
                },
            },
            "metadata": {
                "intent": "viewing_booking",
                "tool": "schedule_viewing",
                "matched_slot_id": str(matched.id),
                "matched_slot_reason": "best_valid_slot",
                "listing_id": str(listing.id),
            },
        }

    async def _draft_inquiry_message(
        self,
        *,
        listing: Listing,
        user_request: str,
        profile: LeadProfileSnapshot,
    ) -> str:
        prompt = (
            "Draft one concise property inquiry message for human review.\n"
            f"Listing title: {listing.title}\n"
            f"Listing city: {listing.city or listing.location_text or 'Unknown'}\n"
            f"User intent: {user_request.strip()}\n"
            f"Available profile fields: name={profile.name or ''}, email={profile.email or ''}, phone={profile.phone or ''}\n"
            "Do not invent facts. Do not include any signature block beyond the provided profile fields."
        )
        text = await self._invoke_plain_llm(
            prompt=prompt,
            run_name="listing_user_assistant.inquiry_draft",
            metadata={"intent": "lead_inquiry", "listing_id": str(listing.id)},
        )
        if text:
            return text

        intro = f"Hello, I'm interested in {listing.title}"
        if listing.city:
            intro += f" in {listing.city}"
        intro += "."
        detail = user_request.strip()
        return f"{intro} {detail}".strip()

    async def _invoke_plain_llm(
        self,
        *,
        prompt: str,
        run_name: str,
        metadata: dict[str, Any],
    ) -> str | None:
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from langchain_openai import AzureChatOpenAI
        except Exception:
            return None

        if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
            return None
        if not settings.azure_openai_chat_deployment:
            return None

        try:
            llm = AzureChatOpenAI(
                azure_endpoint=settings.azure_openai_endpoint.rstrip("/"),
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_deployment=settings.azure_openai_chat_deployment,
                temperature=0.1,
            )
            response = await llm.ainvoke(
                [
                    SystemMessage(content="You prepare concise real-estate assistant copy for human review."),
                    HumanMessage(content=prompt[: settings.listing_assistant_max_context_chars]),
                ],
                config={"run_name": run_name, "metadata": metadata, "tags": ["listing-assistant"]},
            )
        except Exception:
            logger.exception("Listing assistant plain LLM invocation failed")
            return None

        return self._message_text(response) or None

    def _system_prompt(self) -> str:
        return (
            "You are AkarAI's listing-page assistant for one specific listing.\n"
            "You must stay within this listing only.\n"
            "For factual listing questions, call get_listing_context before answering.\n"
            "If the user wants to contact the agency or send a message, call send_inquiry.\n"
            "If the user wants to book or schedule a viewing, call schedule_viewing.\n"
            "If the user confirms a slot you already proposed, call schedule_viewing again and include that exact slot timing in the tool input.\n"
            "The send_inquiry and schedule_viewing tools only prepare confirmable actions. They do not mutate anything.\n"
            "Never claim a lead was sent or a viewing was booked unless the frontend later confirms it.\n"
            "If the user asks about neighborhoods, schools, financing, investment advice, comparisons, or other listings, refuse briefly.\n"
            "Keep answers concise."
        )

    def _langsmith_trace_context(self):
        if not settings.listing_assistant_enable_langsmith_tracing:
            return contextlib.nullcontext()
        if not settings.langsmith_api_key:
            return contextlib.nullcontext()
        try:
            from langsmith.run_helpers import tracing_context
        except Exception:
            return contextlib.nullcontext()
        return tracing_context(enabled=True, project_name=settings.langsmith_project)

    async def _get_active_listing(self, listing_id: UUID) -> Listing:
        listing = await self._listing_repo.get_by_id(listing_id)
        if listing is None or listing.status != "active":
            raise NotFoundError(detail="Listing not found")
        return listing

    async def _get_active_slots(self, listing_id: UUID) -> list[ListingViewingSlot]:
        slots = await self._slot_repo.list_bookable_by_listing(listing_id)
        return slots[: settings.listing_assistant_max_slot_options]

    async def _get_user_profile(self) -> LeadProfileSnapshot | None:
        if not self._actor:
            return None
        user_id = self._actor.get("user_id")
        if not user_id:
            return None
        users_service = UsersService(UsersRepository(self._session))
        user = await users_service.get_user(str(user_id))
        if user is None:
            return None
        missing_fields = users_service.get_lead_profile_missing_fields(user)
        return LeadProfileSnapshot(
            name=user.name.strip() if user.name else None,
            email=user.email.strip() if user.email else None,
            phone=user.phone.strip() if user.phone else None,
            missing_fields=missing_fields,
        )

    def _is_out_of_scope(self, query: str) -> bool:
        return any(re.search(pattern, query, re.IGNORECASE) for pattern in _OUT_OF_SCOPE_PATTERNS)

    def _serialize_listing(self, listing: Listing) -> dict[str, Any]:
        return {
            "id": str(listing.id),
            "title": listing.title,
            "description": (listing.description or "").strip()[: settings.listing_assistant_max_context_chars],
            "property_type": listing.property_type,
            "listing_purpose": listing.listing_purpose,
            "price": self._format_price(listing.price, listing.currency),
            "bedrooms": listing.bedrooms,
            "bathrooms": listing.bathrooms,
            "area": self._format_area(listing.area_size, listing.area_unit),
            "furnishing": listing.furnishing,
            "location_text": listing.location_text,
            "address": listing.address,
            "city": listing.city,
            "country": listing.country,
        }

    def _serialize_slot(self, slot: ListingViewingSlot) -> dict[str, Any]:
        return {
            "id": str(slot.id),
            "starts_at": slot.starts_at.isoformat(),
            "ends_at": slot.ends_at.isoformat(),
            "capacity": slot.capacity,
            "reserved_count": slot.reserved_count,
            "status": slot.status,
            "label": f"{self._format_slot_start(slot.starts_at)} to {self._format_slot_end(slot.ends_at)}",
        }

    def _match_slot(
        self,
        query: str,
        slots: list[ListingViewingSlot],
    ) -> ListingViewingSlot | None:
        if not slots:
            return None

        now = datetime.now(timezone.utc)
        candidates = [
            slot for slot in slots
            if slot.starts_at >= now and (slot.reserved_count or 0) < (slot.capacity or 0)
        ]
        if not candidates:
            return None

        parsed = self._parse_time_preferences(query, now)
        if parsed["target_date"] is not None:
            target_date = parsed["target_date"]
            narrowed = [slot for slot in candidates if slot.starts_at.date() == target_date]
            if not narrowed:
                return None
            candidates = narrowed

        if parsed["weekday"] is not None:
            narrowed = [slot for slot in candidates if slot.starts_at.weekday() == parsed["weekday"]]
            if not narrowed:
                return None
            candidates = narrowed

        after_hour = parsed["after_hour"]
        before_hour = parsed["before_hour"]
        around_hour = parsed["around_hour"]

        if after_hour is not None:
            narrowed = [slot for slot in candidates if slot.starts_at.hour >= after_hour]
            if not narrowed:
                return None
            candidates = narrowed

        if before_hour is not None:
            narrowed = [slot for slot in candidates if slot.starts_at.hour <= before_hour]
            if not narrowed:
                return None
            candidates = narrowed

        if around_hour is not None:
            return min(candidates, key=lambda slot: abs(slot.starts_at.hour - around_hour))

        return min(candidates, key=lambda slot: slot.starts_at)

    def _match_slot_from_conversation(
        self,
        conversation_messages: list[ListingAssistantConversationMessage],
        slots: list[ListingViewingSlot],
    ) -> ListingViewingSlot | None:
        if not conversation_messages or not slots:
            return None

        for message in reversed(conversation_messages):
            if message.role != "assistant":
                continue
            content = self._normalize_text(message.content)
            for slot in slots:
                if self._assistant_message_mentions_slot(content, slot):
                    return slot
        return None

    def _assistant_message_mentions_slot(self, content: str, slot: ListingViewingSlot) -> bool:
        slot_start = slot.starts_at.astimezone(timezone.utc)
        slot_end = slot.ends_at.astimezone(timezone.utc)
        date_variants = {
            self._normalize_text(slot_start.strftime("%a %b %d")),
            self._normalize_text(slot_start.strftime("%a, %b %d")),
        }
        start_variants = {
            self._normalize_time_token(slot_start),
            self._normalize_text(slot_start.strftime("%I:%M %p")),
        }
        end_variants = {
            self._normalize_time_token(slot_end),
            self._normalize_text(slot_end.strftime("%I:%M %p")),
        }
        return (
            any(date_value in content for date_value in date_variants)
            and any(time_value in content for time_value in start_variants)
            and any(time_value in content for time_value in end_variants)
        )

    def _is_generic_booking_confirmation(self, query: str) -> bool:
        lowered = self._normalize_text(query)
        patterns = (
            r"^(yes|yes please|please|book it|book that|that works|sounds good|confirm)$",
            r"\bjust me\b",
            r"\b1 person\b",
            r"\bfor one person\b",
        )
        return any(re.search(pattern, lowered) for pattern in patterns)

    def _parse_time_preferences(self, query: str, now: datetime) -> dict[str, Any]:
        lowered = query.lower()
        target_date = None
        weekday = None
        after_hour = None
        before_hour = None
        around_hour = None

        if "tomorrow" in lowered:
            target_date = (now + timedelta(days=1)).date()
        elif "today" in lowered:
            target_date = now.date()

        for name, weekday_index in _WEEKDAYS.items():
            if name in lowered:
                weekday = weekday_index
                break

        if "morning" in lowered:
            after_hour = 6
            before_hour = 12
        elif "afternoon" in lowered:
            after_hour = 12
            before_hour = 17
        elif "evening" in lowered or "tonight" in lowered:
            after_hour = 17
            before_hour = 21

        after_match = re.search(r"after\s+(\d{1,2})(?::\d{2})?\s*(am|pm)?", lowered)
        if after_match:
            after_hour = self._to_24_hour(
                int(after_match.group(1)),
                after_match.group(2),
                default_to_pm=after_match.group(2) is None and "morning" not in lowered,
            )

        before_match = re.search(r"before\s+(\d{1,2})(?::\d{2})?\s*(am|pm)?", lowered)
        if before_match:
            before_hour = self._to_24_hour(
                int(before_match.group(1)),
                before_match.group(2),
                default_to_pm=before_match.group(2) is None and "morning" not in lowered,
            )

        around_match = re.search(r"(around|at)\s+(\d{1,2})(?::\d{2})?\s*(am|pm)?", lowered)
        if around_match:
            around_hour = self._to_24_hour(
                int(around_match.group(2)),
                around_match.group(3),
                default_to_pm=around_match.group(3) is None and "morning" not in lowered,
            )

        return {
            "target_date": target_date,
            "weekday": weekday,
            "after_hour": after_hour,
            "before_hour": before_hour,
            "around_hour": around_hour,
        }

    def _to_24_hour(self, hour: int, meridiem: str | None, *, default_to_pm: bool = False) -> int:
        if meridiem is None:
            if default_to_pm and 1 <= hour <= 7:
                return hour + 12
            return hour
        meridiem = meridiem.lower()
        if meridiem == "pm" and hour < 12:
            return hour + 12
        if meridiem == "am" and hour == 12:
            return 0
        return hour

    def _format_price(self, price: Decimal | None, currency: str | None) -> str:
        if price is None or not currency:
            return "price on request"
        try:
            return f"{currency} {int(price):,}"
        except Exception:
            return f"{currency} {price}"

    def _format_area(self, area_size: Decimal | None, area_unit: str | None) -> str:
        if area_size is None:
            return "not specified"
        if area_unit:
            return f"{area_size} {area_unit}"
        return str(area_size)

    def _format_slot_start(self, value: datetime) -> str:
        return value.astimezone(timezone.utc).strftime("%a %b %d at %I:%M %p UTC")

    def _format_slot_end(self, value: datetime) -> str:
        return value.astimezone(timezone.utc).strftime("%I:%M %p UTC")

    def _format_slot_label(self, slot: ListingViewingSlot) -> str:
        return f"{self._format_slot_start(slot.starts_at)} to {self._format_slot_end(slot.ends_at)}"

    def _available_slot_labels(self, slots: list[ListingViewingSlot]) -> list[str]:
        return [self._format_slot_label(slot) for slot in slots[:3]]

    def _normalize_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value.strip().lower())

    def _normalize_time_token(self, value: datetime) -> str:
        return self._normalize_text(value.astimezone(timezone.utc).strftime("%I:%M %p").lstrip("0"))
