import { useSpamLeads } from "@/features/leads/useAgencyLeads";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ShieldAlert, ShieldCheck, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

export function SpamLeadsPage() {
  const { data, isLoading } = useSpamLeads();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Spam Leads</h2>
        <p className="text-muted-foreground">Manage flagged spam leads</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-red-500" />
            Spam Queue
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-16 bg-muted animate-pulse rounded" />
              ))}
            </div>
          ) : !data || data.items.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-8 text-muted-foreground">
              <ShieldCheck className="h-10 w-10" />
              <p>No spam leads detected.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-2 font-medium">Name</th>
                    <th className="text-left py-3 px-2 font-medium">Email</th>
                    <th className="text-left py-3 px-2 font-medium">Classification</th>
                    <th className="text-left py-3 px-2 font-medium">Processing</th>
                    <th className="text-left py-3 px-2 font-medium">Created</th>
                    <th className="text-left py-3 px-2 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((lead) => {
                    const isProcessing =
                      lead.processing_status === "pending" ||
                      lead.processing_status === "pending_spam" ||
                      lead.processing_status === "pending_level";
                    return (
                    <tr key={lead.id} className="border-b">
                      <td className="py-3 px-2">{lead.name || "—"}</td>
                      <td className="py-3 px-2">{lead.email || "—"}</td>
                      <td className="py-3 px-2">
                        {lead.spam_label === "spam" ? (
                          <span className="inline-flex items-center rounded-full px-2 py-1 text-xs bg-red-100 text-red-700">
                            Spam
                          </span>
                        ) : lead.spam_label === "not_spam" ? (
                          <span className="inline-flex items-center rounded-full px-2 py-1 text-xs bg-green-100 text-green-700">
                            Not Spam
                          </span>
                        ) : isProcessing ? (
                          <span className="inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs bg-yellow-100 text-yellow-700">
                            <Loader2 className="h-3 w-3 animate-spin" />
                            Pending
                          </span>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="py-3 px-2">
                        {isProcessing ? (
                          <span className="inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs bg-yellow-100 text-yellow-700">
                            <Loader2 className="h-3 w-3 animate-spin" />
                            Processing
                          </span>
                        ) : (
                          <span className="rounded-full px-2 py-1 text-xs bg-green-100 text-green-700">
                            Complete
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-2">{new Date(lead.created_at).toLocaleDateString()}</td>
                      <td className="py-3 px-2">
                        <Button variant="ghost" size="sm" asChild>
                          <Link to={`/leads/${lead.id}`}>Review</Link>
                        </Button>
                      </td>
                    </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
