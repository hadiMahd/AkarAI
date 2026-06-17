import { useReviewedLeads } from "@/features/leads/useAgencyLeads";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2, ShieldAlert, TrendingUp } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

export function ReviewedLeadsPage() {
  const { data, isLoading } = useReviewedLeads();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Reviewed Leads</h2>
        <p className="text-muted-foreground">Previously reviewed leads</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5" />
            Reviewed Lead Archive
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
            <p className="text-muted-foreground">No reviewed leads yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-2 font-medium">Name</th>
                    <th className="text-left py-3 px-2 font-medium">Email</th>
                    <th className="text-left py-3 px-2 font-medium">Classification</th>
                    <th className="text-left py-3 px-2 font-medium">Status</th>
                    <th className="text-left py-3 px-2 font-medium">Reviewed</th>
                    <th className="text-left py-3 px-2 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((lead) => {
                    const isSpamWithoutRank = lead.spam_label === "spam" && !lead.lead_level;
                    return (
                    <tr key={lead.id} className="border-b">
                      <td className="py-3 px-2">{lead.name || "—"}</td>
                      <td className="py-3 px-2">{lead.email || "—"}</td>
                      <td className="py-3 px-2">
                        <div className="flex flex-wrap gap-1">
                          {lead.spam_label && (
                            <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs ${
                              lead.spam_label === "spam"
                                ? "bg-red-100 text-red-700"
                                : "bg-green-100 text-green-700"
                            }`}>
                              {lead.spam_label === "spam" ? (
                                <><ShieldAlert className="h-3 w-3 mr-1" /> Spam</>
                              ) : "Not Spam"}
                            </span>
                          )}
                          {lead.lead_level && (
                            <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs ${
                              lead.lead_level === "hot"
                                ? "bg-orange-100 text-orange-700"
                                : "bg-blue-100 text-blue-700"
                            }`}>
                              {lead.lead_level === "hot" ? (
                                <><TrendingUp className="h-3 w-3 mr-1" /> Hot</>
                              ) : "Normal"}
                            </span>
                          )}
                          {isSpamWithoutRank && (
                            <span className="inline-flex items-center rounded-full px-2 py-1 text-xs bg-slate-100 text-slate-700">
                              Rank Skipped
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-2">
                        <span className="inline-flex items-center rounded-full px-2 py-1 text-xs bg-green-100 text-green-700">
                          {lead.status}
                        </span>
                      </td>
                      <td className="py-3 px-2">{new Date(lead.updated_at).toLocaleDateString()}</td>
                      <td className="py-3 px-2">
                        <Button variant="ghost" size="sm" asChild>
                          <Link to={`/leads/${lead.id}`}>View</Link>
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
