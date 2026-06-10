import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { Calendar, Clock } from "lucide-react";

interface ScheduledViewing {
  id: string;
  listing_id: string;
  viewing_slot_id: string;
  status: string;
  scheduled_start_at: string;
  scheduled_end_at: string;
}

interface PaginatedViewingsResponse {
  items: ScheduledViewing[];
  page: number;
  page_size: number;
  total: number;
  has_next: boolean;
  has_previous: boolean;
}

export function ScheduledViewingsTab() {
  const { data, isLoading, error } = useQuery<PaginatedViewingsResponse>({
    queryKey: ["my-viewings"],
    queryFn: () => apiClient<PaginatedViewingsResponse>("/me/viewings"),
  });

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6 text-center">
          <p className="text-destructive">Failed to load viewings.</p>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6 text-center">
          <Calendar className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">You haven't booked any viewings yet.</p>
          <Button asChild className="mt-4">
            <Link to="/listings">Browse Listings</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  const formatDateTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      weekday: "short",
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="space-y-4">
      {data.items.map((viewing) => (
        <Card key={viewing.id}>
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="font-semibold">Viewing Scheduled</span>
                </div>
                <div className="space-y-1 text-sm text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    <span>{formatDateTime(viewing.scheduled_start_at)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    <span>{formatDateTime(viewing.scheduled_end_at)}</span>
                  </div>
                </div>
                <Link
                  to={`/listings/${viewing.listing_id}`}
                  className="text-sm font-medium hover:underline"
                >
                  View Listing
                </Link>
              </div>
              <Badge variant={viewing.status === "scheduled" ? "default" : "secondary"}>
                {viewing.status}
              </Badge>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
