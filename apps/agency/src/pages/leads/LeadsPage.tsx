import { useActiveLeads } from "@/features/leads/useAgencyLeads";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MessageSquare } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

export function LeadsPage() {
  const { data, isLoading } = useActiveLeads();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Active Leads</h2>
        <p className="text-muted-foreground">Review and manage incoming leads</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Lead Queue
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
            <p className="text-muted-foreground">No active leads. All leads have been reviewed.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-2 font-medium">Name</th>
                    <th className="text-left py-3 px-2 font-medium">Email</th>
                    <th className="text-left py-3 px-2 font-medium">Status</th>
                    <th className="text-left py-3 px-2 font-medium">Created</th>
                    <th className="text-left py-3 px-2 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((lead) => (
                    <tr key={lead.id} className="border-b">
                      <td className="py-3 px-2">{lead.name || "—"}</td>
                      <td className="py-3 px-2">{lead.email || "—"}</td>
                      <td className="py-3 px-2">
                        <span className="inline-flex items-center rounded-full px-2 py-1 text-xs bg-blue-100 text-blue-700">
                          {lead.status}
                        </span>
                      </td>
                      <td className="py-3 px-2">{new Date(lead.created_at).toLocaleDateString()}</td>
                      <td className="py-3 px-2">
                        <Button variant="ghost" size="sm" asChild>
                          <Link to={`/leads/${lead.id}`}>Review</Link>
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
