import { useState, type FormEvent } from "react";
import { useLeadDetail } from "./useAgencyLeads";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2 } from "lucide-react";
import { useParams, Link, useNavigate } from "react-router-dom";

export function LeadReviewForm() {
  const { leadId } = useParams();
  const navigate = useNavigate();
  const { lead, isLoading, reviewLead, isReviewing } = useLeadDetail(leadId || "");
  const [formData, setFormData] = useState({
    outcome: "",
    notes: "",
  });
  const [successMessage, setSuccessMessage] = useState("");

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

      <Button variant="outline" asChild>
        <Link to="/leads">Back to Leads</Link>
      </Button>
    </div>
  );
}
