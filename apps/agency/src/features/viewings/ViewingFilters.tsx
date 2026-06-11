import { useState } from "react";
import { useAgencyViewings } from "./useAgencyViewings";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Calendar, Filter, X } from "lucide-react";

export function ViewingFilters() {
  const [filters, setFilters] = useState({
    status: "",
    listing_id: "",
    date_from: "",
    date_to: "",
  });

  const { data, isLoading } = useAgencyViewings(filters);

  const handleApply = () => {
    // Filters are applied reactively via the query
  };

  const handleClear = () => {
    setFilters({ status: "", listing_id: "", date_from: "", date_to: "" });
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <select
                id="status"
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">All</option>
                <option value="scheduled">Scheduled</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="listing_id">Listing ID</Label>
              <Input
                id="listing_id"
                value={filters.listing_id}
                onChange={(e) => setFilters({ ...filters, listing_id: e.target.value })}
                placeholder="Filter by listing"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="date_from">From Date</Label>
              <Input
                id="date_from"
                type="date"
                value={filters.date_from}
                onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="date_to">To Date</Label>
              <Input
                id="date_to"
                type="date"
                value={filters.date_to}
                onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
              />
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <Button onClick={handleApply}>
              <Filter className="h-4 w-4 mr-2" />
              Apply Filters
            </Button>
            <Button variant="outline" onClick={handleClear}>
              <X className="h-4 w-4 mr-2" />
              Clear
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Scheduled Viewings
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
            <p className="text-muted-foreground">No viewings match the current filters.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-2 font-medium">Start</th>
                    <th className="text-left py-3 px-2 font-medium">End</th>
                    <th className="text-left py-3 px-2 font-medium">Status</th>
                    <th className="text-left py-3 px-2 font-medium">Listing</th>
                    <th className="text-left py-3 px-2 font-medium">Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((viewing) => (
                    <tr key={viewing.id} className="border-b">
                      <td className="py-3 px-2">{new Date(viewing.scheduled_start_at).toLocaleString()}</td>
                      <td className="py-3 px-2">{new Date(viewing.scheduled_end_at).toLocaleString()}</td>
                      <td className="py-3 px-2">
                        <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs ${
                          viewing.status === "scheduled"
                            ? "bg-blue-100 text-blue-700"
                            : viewing.status === "completed"
                            ? "bg-green-100 text-green-700"
                            : "bg-gray-100 text-gray-700"
                        }`}>
                          {viewing.status}
                        </span>
                      </td>
                      <td className="py-3 px-2">{viewing.listing_id.substring(0, 8)}...</td>
                      <td className="py-3 px-2">{viewing.notes || "—"}</td>
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
