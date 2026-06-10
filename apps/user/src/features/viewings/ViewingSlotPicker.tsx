import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Calendar, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ViewingSlot {
  id: string;
  starts_at: string;
  ends_at: string;
  capacity: number;
  reserved_count: number;
  status: string;
}

interface ViewingSlotPickerProps {
  listingId: string;
  selectedSlotId: string | null;
  onSlotSelect: (slotId: string) => void;
}

export function ViewingSlotPicker({
  listingId,
  selectedSlotId,
  onSlotSelect,
}: ViewingSlotPickerProps) {
  const { data: slots, isLoading, error } = useQuery<ViewingSlot[]>({
    queryKey: ["viewing-slots", listingId],
    queryFn: () => apiClient<ViewingSlot[]>(`/listings/${listingId}/viewing-slots`),
    enabled: !!listingId,
  });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-center text-muted-foreground">Loading available slots...</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-center text-destructive">Failed to load viewing slots.</p>
        </CardContent>
      </Card>
    );
  }

  if (!slots || slots.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-center text-muted-foreground">No viewing slots available.</p>
        </CardContent>
      </Card>
    );
  }

  const formatDateTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Available Viewing Slots</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {slots.map((slot) => {
          const isFull = slot.reserved_count >= slot.capacity;
          const isSelected = selectedSlotId === slot.id;

          return (
            <Button
              key={slot.id}
              variant={isSelected ? "default" : "outline"}
              className={cn(
                "w-full justify-start h-auto py-3 px-4",
                isFull && "opacity-50 cursor-not-allowed"
              )}
              onClick={() => !isFull && onSlotSelect(slot.id)}
              disabled={isFull}
            >
              <div className="flex flex-col items-start gap-1 w-full">
                <div className="flex items-center gap-2 text-sm">
                  <Calendar className="h-4 w-4" />
                  <span>{formatDateTime(slot.starts_at)}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  <span>
                    {slot.reserved_count} / {slot.capacity} spots filled
                  </span>
                </div>
              </div>
            </Button>
          );
        })}
      </CardContent>
    </Card>
  );
}
