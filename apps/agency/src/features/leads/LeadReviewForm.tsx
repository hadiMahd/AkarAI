import { useState, type FormEvent } from "react";
import { useLeadDetail } from "./useAgencyLeads";
import { useLeadReplyDraft } from "@/features/agencyAi/useAgencyAi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2, Sparkles, Loader2, Mail, MessageSquareText, Send } from "lucide-react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { getApiErrorMessage } from "@/lib/api/errors";

type Channel = "email" | "whatsapp";

interface ReplyDraft {
  channel: Channel;
  subject?: string | null;
  body?: string | null;
}

function buildWhatsAppUrl(phone: string, body: string) {
  const cleaned = phone.replace(/[^\d+]/g, "");
  return `https://wa.me/${cleaned}?text=${encodeURIComponent(body)}`;
}

function buildMailtoUrl(email: string, subject: string | null | undefined, body: string | null | undefined) {
  const params = new URLSearchParams();
  if (subject) params.set("subject", subject);
  if (body) params.set("body", body);
  return `mailto:${email}?${params.toString()}`;
}

export function LeadReviewForm() {
  const { leadId } = useParams();
  const navigate = useNavigate();
  const { lead, isLoading, reviewLead, isReviewing } = useLeadDetail(leadId || "");
  const replyDraftMutation = useLeadReplyDraft();
  const [formData, setFormData] = useState({ outcome: "", notes: "" });
  const [successMessage, setSuccessMessage] = useState("");
  const [draftingChannel, setDraftingChannel] = useState<Channel | null>(null);
  const [replyDraft, setReplyDraft] = useState<ReplyDraft | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await reviewLead(formData);
      setSuccessMessage("Lead marked as reviewed successfully");
      setTimeout(() => navigate("/leads"), 1500);
    } catch {
      // Error is handled by the mutation
    }
  };

  const handleDraftReply = async (channel: Channel) => {
    if (!leadId) return;
    setDraftingChannel(channel);
    try {
      const result = await replyDraftMutation.mutateAsync({ leadId, channel });
      setReplyDraft({ channel, subject: result.subject, body: result.body });
    } finally {
      setDraftingChannel(null);
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Loading lead...</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-10 bg-muted animate-pulse rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!lead) {
    return (
      <Card>
        <CardContent className="py-8">
          <p className="text-muted-foreground text-center">Lead not found</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Lead Details</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-4 md:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Name</dt>
              <dd className="text-lg">{lead.name || "—"}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Email</dt>
              <dd className="text-lg">{lead.email || "—"}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Phone</dt>
              <dd className="text-lg">{lead.phone || "—"}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Status</dt>
              <dd>
                <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs ${
                  lead.status === "reviewed"
                    ? "bg-green-100 text-green-700"
                    : "bg-blue-100 text-blue-700"
                }`}>
                  {lead.status}
                </span>
              </dd>
            </div>
            <div className="md:col-span-2">
              <dt className="text-sm font-medium text-muted-foreground">Message</dt>
              <dd className="text-lg">{lead.message || "—"}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Created</dt>
              <dd className="text-lg">{new Date(lead.created_at).toLocaleString()}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      {lead.status !== "reviewed" && (
        <Card>
          <CardHeader>
            <CardTitle>Review Lead</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {successMessage && (
                <div className="flex items-center gap-2 p-3 rounded-md bg-green-50 text-green-700 text-sm">
                  <CheckCircle2 className="h-4 w-4" />
                  <span>{successMessage}</span>
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="outcome">Outcome</Label>
                <Input
                  id="outcome"
                  value={formData.outcome}
                  onChange={(e) => setFormData({ ...formData, outcome: e.target.value })}
                  placeholder="e.g., Interested, Not interested, Follow up needed"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="notes">Notes</Label>
                <Textarea
                  id="notes"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={3}
                  placeholder="Additional notes about this lead..."
                />
              </div>
              <Button type="submit" disabled={isReviewing}>
                {isReviewing ? "Reviewing..." : "Mark as Reviewed"}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {lead.status === "reviewed" && (
        <Card>
          <CardContent className="py-8">
            <div className="flex items-center justify-center gap-2 text-green-700">
              <CheckCircle2 className="h-5 w-5" />
              <span>This lead has been reviewed</span>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-4 w-4" />
            AI reply draft
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => void handleDraftReply("email")}
              disabled={draftingChannel !== null}
            >
              {draftingChannel === "email" ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Mail className="mr-2 h-4 w-4" />
              )}
              {draftingChannel === "email" ? "Drafting…" : "Draft email reply"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => void handleDraftReply("whatsapp")}
              disabled={draftingChannel !== null}
            >
              {draftingChannel === "whatsapp" ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <MessageSquareText className="mr-2 h-4 w-4" />
              )}
              {draftingChannel === "whatsapp" ? "Drafting…" : "Draft WhatsApp reply"}
            </Button>
          </div>

          {replyDraftMutation.error && (
            <p className="text-sm text-destructive">
              {getApiErrorMessage(replyDraftMutation.error, "agencyAi.leadReply.draft")}
            </p>
          )}

          {replyDraft && (
            <div className="rounded-md border bg-muted/30 p-4 space-y-3 text-sm">
              {replyDraft.subject && (
                <p className="font-medium">Subject: {replyDraft.subject}</p>
              )}
              <p className="whitespace-pre-wrap">{replyDraft.body}</p>

              <div className="pt-1 flex flex-wrap gap-2">
                {replyDraft.channel === "email" && lead.email && (
                  <Button asChild size="sm" variant="default">
                    <a
                      href={buildMailtoUrl(lead.email, replyDraft.subject, replyDraft.body)}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <Send className="mr-2 h-3 w-3" />
                      Open in email
                    </a>
                  </Button>
                )}
                {replyDraft.channel === "whatsapp" && lead.phone && (
                  <Button asChild size="sm" variant="default">
                    <a
                      href={buildWhatsAppUrl(lead.phone, replyDraft.body ?? "")}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <MessageSquareText className="mr-2 h-3 w-3" />
                      Open in WhatsApp
                    </a>
                  </Button>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Button variant="outline" asChild>
        <Link to="/leads">Back to Leads</Link>
      </Button>
    </div>
  );
}
