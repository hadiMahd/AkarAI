import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  AlertCircle,
  Calendar,
  MessageSquare,
  Minimize2,
  Send,
  Sparkles,
  X,
} from "lucide-react";
import { useAuth } from "@/features/auth/useAuth";
import { useUserProfile } from "@/features/profile/useUserProfile";
import { useSubmitInquiry } from "@/features/inquiries/useSubmitInquiry";
import { useBookViewing } from "@/features/viewings/useBookViewing";
import {
  useListingAssistant,
  type ListingAssistantMessage,
  type ListingAssistantPendingAction,
} from "./useListingAssistant";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { getApiErrorMessage } from "@/lib/api/errors";

interface ListingAssistantWidgetProps {
  listingId: string;
  listingTitle: string;
}

type ActionRequirement = "none" | "sign-in" | "profile";

function formatViewingWindow(pendingAction: ListingAssistantPendingAction | null) {
  if (pendingAction?.type !== "viewing_booking") {
    return null;
  }

  const payloadLabel = pendingAction.payload.scheduled_label;
  if (typeof payloadLabel === "string" && payloadLabel.trim()) {
    return payloadLabel;
  }

  const startValue = pendingAction.payload.scheduled_start_at;
  const endValue = pendingAction.payload.scheduled_end_at;
  if (!startValue || !endValue) {
    return null;
  }

  const start = new Date(startValue);
  const end = new Date(endValue);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    return startValue;
  }

  const dateFormatter = new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  });
  const endFormatter = new Intl.DateTimeFormat(undefined, {
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  });

  return `${dateFormatter.format(start)} to ${endFormatter.format(end)}`;
}

export function ListingAssistantWidget({
  listingId,
  listingTitle,
}: ListingAssistantWidgetProps) {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { data: profile } = useUserProfile();
  const assistant = useListingAssistant(listingId);
  const submitInquiry = useSubmitInquiry(listingId);
  const bookViewing = useBookViewing(listingId);

  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<ListingAssistantMessage[]>([]);
  const [pendingAction, setPendingAction] = useState<ListingAssistantPendingAction | null>(null);
  const [actionRequirement, setActionRequirement] = useState<ActionRequirement>("none");
  const [isOpen, setIsOpen] = useState(false);
  const transcriptRef = useRef<HTMLDivElement | null>(null);

  const trimmedDraft = draft.trim();
  const hasActivity = messages.length > 0 || pendingAction !== null;
  const viewingWindow = formatViewingWindow(pendingAction);

  useEffect(() => {
    if (!isOpen || !transcriptRef.current) {
      return;
    }
    if (typeof transcriptRef.current.scrollTo === "function") {
      transcriptRef.current.scrollTo({
        top: transcriptRef.current.scrollHeight,
        behavior: "smooth",
      });
      return;
    }
    transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
  }, [isOpen, messages, pendingAction, actionRequirement, assistant.isPending]);

  const sendMessage = () => {
    if (!trimmedDraft || assistant.isPending) {
      return;
    }

    const userMessage: ListingAssistantMessage = { role: "user", content: trimmedDraft };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setDraft("");
    setPendingAction(null);
    setActionRequirement("none");

    assistant.mutate(
      {
        message: userMessage.content,
        conversation_messages: nextMessages,
      },
      {
        onSuccess: (response) => {
          setMessages((current) => [
            ...current,
            { role: "assistant", content: response.assistant_message },
          ]);
          setPendingAction(response.pending_action);
          if (response.metadata?.auth_required) {
            setActionRequirement("sign-in");
          } else if (response.metadata?.profile_incomplete) {
            setActionRequirement("profile");
          } else {
            setActionRequirement("none");
          }
        },
        onError: () => {
          setMessages((current) => current.slice(0, -1));
        },
      }
    );
  };

  const confirmPendingAction = () => {
    if (!pendingAction) {
      return;
    }

    if (pendingAction.type === "lead_inquiry") {
      if (!isAuthenticated) {
        navigate("/sign-in");
        return;
      }
      if (!profile?.is_complete_for_leads) {
        navigate("/profile");
        return;
      }
      submitInquiry.mutate(
        { message: pendingAction.payload.message || "" },
        {
          onSuccess: () => {
            setMessages((current) => [
              ...current,
              {
                role: "assistant",
                content: "Your inquiry was submitted using the existing listing inquiry flow.",
              },
            ]);
            setPendingAction(null);
          },
        }
      );
      return;
    }

    if (!isAuthenticated) {
      navigate("/sign-in");
      return;
    }
    const slotId = pendingAction.payload.viewing_slot_id;
    if (!slotId) {
      return;
    }
    bookViewing.mutate(
      {
        viewing_slot_id: slotId,
        notes: pendingAction.payload.notes,
      },
      {
        onSuccess: () => {
          setMessages((current) => [
            ...current,
            {
              role: "assistant",
              content: "Your viewing was booked using the existing booking flow.",
            },
          ]);
          setPendingAction(null);
        },
      }
    );
  };

  const cancelPendingAction = () => {
    setPendingAction(null);
    setActionRequirement("none");
  };

  const actionError =
    pendingAction?.type === "lead_inquiry"
      ? submitInquiry.error
      : pendingAction?.type === "viewing_booking"
        ? bookViewing.error
        : null;

  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-50 sm:bottom-6 sm:right-6">
      {isOpen && (
        <section
          id="listing-assistant-panel"
          role="dialog"
          aria-label="Listing assistant"
          className="pointer-events-auto mb-3 w-[min(24rem,calc(100vw-1rem))] overflow-hidden rounded-[1.75rem] border border-slate-200/80 bg-white shadow-[0_28px_90px_rgba(15,23,42,0.2)]"
        >
          <div className="border-b border-white/10 bg-[radial-gradient(circle_at_top_left,_rgba(96,165,250,0.3),_transparent_45%),linear-gradient(135deg,_#020617,_#0f172a_60%,_#1e293b)] px-4 py-3 text-white">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-white/20 bg-white/10 backdrop-blur">
                    <Sparkles className="h-4 w-4" />
                  </span>
                  <p className="truncate text-sm font-semibold text-white">Ask about {listingTitle}</p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  className="h-8 w-8 rounded-full text-white hover:bg-white/10 hover:text-white"
                  onClick={() => setIsOpen(false)}
                  aria-label="Collapse listing assistant"
                >
                  <Minimize2 className="h-4 w-4" />
                </Button>
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  className="h-8 w-8 rounded-full text-white hover:bg-white/10 hover:text-white"
                  onClick={() => {
                    setIsOpen(false);
                    setPendingAction(null);
                    setActionRequirement("none");
                  }}
                  aria-label="Close listing assistant"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          <div className="flex max-h-[min(72vh,42rem)] min-h-[24rem] flex-col bg-[linear-gradient(180deg,_#f8fafc_0%,_#ffffff_22%,_#ffffff_100%)] p-3">
            <div
              ref={transcriptRef}
              className="min-h-0 flex-1 space-y-3 overflow-y-auto rounded-[1.35rem] border border-slate-200 bg-white px-3 py-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.9)]"
            >
              {messages.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50/80 p-3 text-sm text-slate-600">
                  <div className="flex items-center gap-2 text-slate-900">
                    <MessageSquare className="h-4 w-4" />
                    <span className="font-medium">Try:</span>
                  </div>
                  <div className="mt-2 space-y-1 text-[13px] leading-5">
                    <p>"What is the price?"</p>
                    <p>"Contact the agency"</p>
                    <p>"Book tomorrow after 5"</p>
                  </div>
                </div>
              ) : (
                messages.map((message, index) => (
                  <div
                    key={`${message.role}-${index}`}
                    className={
                      message.role === "assistant"
                        ? "mr-10 rounded-[1.25rem] rounded-tl-md border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-700"
                        : "ml-10 rounded-[1.25rem] rounded-tr-md bg-slate-950 px-3 py-3 text-sm text-white shadow-lg shadow-slate-950/10"
                    }
                  >
                    <div className="mb-1.5 flex items-center gap-2">
                      <Badge
                        variant={message.role === "assistant" ? "secondary" : "outline"}
                        className={
                          message.role === "assistant"
                            ? "bg-white text-slate-700"
                            : "border-white/20 text-white"
                        }
                      >
                        {message.role === "assistant" ? "Assistant" : "You"}
                      </Badge>
                    </div>
                    <p className="whitespace-pre-wrap leading-6">{message.content}</p>
                  </div>
                ))
              )}

              {assistant.isPending && (
                <div className="mr-10 rounded-[1.25rem] rounded-tl-md border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-500">
                  Thinking...
                </div>
              )}
            </div>

            <div className="mt-3 space-y-3">
              <div className="rounded-[1.35rem] border border-slate-200 bg-white p-3 shadow-sm">
                <Textarea
                  id="listing_assistant_message"
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  placeholder="Ask about this listing..."
                  rows={2}
                  className="resize-none border-slate-200 bg-slate-50"
                />
                <Button
                  type="button"
                  onClick={sendMessage}
                  disabled={!trimmedDraft || assistant.isPending}
                  className="mt-3 w-full rounded-full bg-slate-950 shadow-lg shadow-slate-950/15 hover:bg-slate-800"
                >
                  <Send className="mr-2 h-4 w-4" />
                  Send
                </Button>
              </div>

              {assistant.isError && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {getApiErrorMessage(assistant.error, "listing.assistant", {
                      fallback:
                        "We couldn't get a listing assistant response. Try again or use the forms below.",
                    })}
                  </AlertDescription>
                </Alert>
              )}

              {pendingAction && (
                <div className="rounded-[1.35rem] border border-sky-200 bg-[linear-gradient(180deg,_rgba(240,249,255,1),_rgba(255,255,255,1))] p-4 shadow-sm">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-950">
                        {pendingAction.type === "lead_inquiry"
                          ? "Review Inquiry Draft"
                          : "Review Viewing Proposal"}
                      </p>
                      <p className="text-xs text-slate-500">
                        Nothing is sent until you press confirm.
                      </p>
                    </div>
                    <Badge className="bg-sky-100 text-sky-800 hover:bg-sky-100">Ready</Badge>
                  </div>

                  {pendingAction.type === "lead_inquiry" ? (
                    <p className="mt-3 whitespace-pre-wrap rounded-2xl bg-white px-3 py-3 text-sm text-slate-700">
                      {pendingAction.payload.message}
                    </p>
                  ) : (
                    <div className="mt-3 space-y-2 rounded-2xl bg-white px-3 py-3 text-sm text-slate-700">
                      <div className="flex items-start gap-2">
                        <Calendar className="mt-0.5 h-4 w-4 text-slate-400" />
                        <span>{viewingWindow || pendingAction.payload.scheduled_start_at}</span>
                      </div>
                      {pendingAction.payload.notes && (
                        <p className="text-slate-500">Notes: {pendingAction.payload.notes}</p>
                      )}
                    </div>
                  )}

                  {actionError && (
                    <Alert variant="destructive" className="mt-3">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        {pendingAction.type === "lead_inquiry"
                          ? getApiErrorMessage(actionError, "inquiry.submit")
                          : getApiErrorMessage(actionError, "viewing.book")}
                      </AlertDescription>
                    </Alert>
                  )}

                  <div className="mt-3 flex gap-2">
                    <Button
                      type="button"
                      onClick={confirmPendingAction}
                      disabled={submitInquiry.isPending || bookViewing.isPending}
                      className="flex-1 rounded-full"
                    >
                      {submitInquiry.isPending || bookViewing.isPending ? "Confirming..." : "Confirm"}
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={cancelPendingAction}
                      className="flex-1 rounded-full"
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}

              {actionRequirement === "sign-in" && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <span>Sign in before you confirm an inquiry or viewing for this listing.</span>
                    <Button asChild size="sm" variant="outline">
                      <Link to="/sign-in">Sign in</Link>
                    </Button>
                  </AlertDescription>
                </Alert>
              )}

              {actionRequirement === "profile" && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <span>Complete your profile before you confirm an inquiry for this listing.</span>
                    <Button asChild size="sm" variant="outline">
                      <Link to="/profile">Complete profile</Link>
                    </Button>
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </div>
        </section>
      )}

      {!isOpen && (
        <div className="pointer-events-auto mb-3 hidden justify-end sm:flex">
          <div className="max-w-[14rem] rounded-full border border-slate-200/80 bg-white/95 px-3 py-2 text-right text-xs text-slate-600 shadow-lg backdrop-blur">
            <span className="font-medium text-slate-900">Listing AI</span>
            <span className="ml-1">
              {hasActivity ? "Pick up where you left off." : "Ask about this property."}
            </span>
          </div>
        </div>
      )}

      <div className="pointer-events-auto flex justify-end">
        <div className="relative">
          <div className="absolute inset-0 rounded-full bg-sky-400/30 blur-xl" />
          <Button
            type="button"
            size="icon"
            onClick={() => setIsOpen((current) => !current)}
            aria-expanded={isOpen}
            aria-controls="listing-assistant-panel"
            aria-label={isOpen ? "Collapse listing assistant" : "Open listing assistant"}
            className="relative h-16 w-16 rounded-full border border-white/20 bg-[linear-gradient(135deg,_#020617,_#0f172a_60%,_#1e3a8a)] shadow-[0_18px_50px_rgba(15,23,42,0.35)] hover:scale-[1.02] hover:bg-[linear-gradient(135deg,_#020617,_#1e293b_60%,_#2563eb)]"
          >
            <Sparkles className="h-6 w-6" />
          </Button>
          {!isOpen && hasActivity && (
            <span className="absolute right-1 top-1 h-3 w-3 rounded-full border-2 border-white bg-emerald-400" />
          )}
        </div>
      </div>
    </div>
  );
}
