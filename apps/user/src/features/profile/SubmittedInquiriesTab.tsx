import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { MessageSquare } from "lucide-react";

interface Inquiry {
  id: string;
  listing_id: string;
  status: string;
  created_at: string;
}

interface PaginatedInquiriesResponse {
  items: Inquiry[];
  page: number;
  page_size: number;
  total: number;
  has_next: boolean;
  has_previous: boolean;
}

export function SubmittedInquiriesTab() {
  const { data, isLoading, error } = useQuery<PaginatedInquiriesResponse>({
    queryKey: ["my-inquiries"],
    queryFn: () => apiClient<PaginatedInquiriesResponse>("/me/inquiries"),
  });

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6 text-center">
          <p className="text-destructive">Failed to load inquiries.</p>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6 text-center">
          <MessageSquare className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">You haven't submitted any inquiries yet.</p>
          <Button asChild className="mt-4">
            <Link to="/listings">Browse Listings</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="space-y-4">
      {data.items.map((inquiry) => (
        <Card key={inquiry.id}>
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">
                    Inquiry for listing
                  </span>
                </div>
                <Link
                  to={`/listings/${inquiry.listing_id}`}
                  className="font-semibold hover:underline"
                >
                  View Listing
                </Link>
                <p className="text-sm text-muted-foreground">
                  Submitted {formatDate(inquiry.created_at)}
                </p>
              </div>
              <Badge variant={inquiry.status === "new" ? "default" : "secondary"}>
                {inquiry.status}
              </Badge>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
