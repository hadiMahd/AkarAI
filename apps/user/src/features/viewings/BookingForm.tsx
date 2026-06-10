import { useState } from "react";
import { useBookViewing } from "./useBookViewing";
import { ViewingSlotPicker } from "./ViewingSlotPicker";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { CheckCircle, AlertCircle } from "lucide-react";

interface BookingFormProps {
  listingId: string;
}

export function BookingForm({ listingId }: BookingFormProps) {
  const [selectedSlotId, setSelectedSlotId] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const bookViewing = useBookViewing(listingId);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSlotId) return;

    bookViewing.mutate(
      {
        viewing_slot_id: selectedSlotId,
        notes: notes || undefined,
      },
      {
        onSuccess: () => {
          setNotes("");
        },
      }
    );
  };

  if (bookViewing.isSuccess) {
    return (
      <Card>
        <CardContent className="pt-6">
          <Alert className="border-green-200 bg-green-50">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              Your viewing has been booked successfully! You will receive a confirmation shortly.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Book a Viewing</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <ViewingSlotPicker
            listingId={listingId}
            selectedSlotId={selectedSlotId}
            onSlotSelect={setSelectedSlotId}
          />

          {selectedSlotId && (
            <>
              <div>
                <label htmlFor="notes" className="block text-sm font-medium mb-2">
                  Notes (optional)
                </label>
                <Textarea
                  id="notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Any special requests or questions..."
                  rows={3}
                />
              </div>

              {bookViewing.isError && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {bookViewing.error.message || "Failed to book viewing. Please try again."}
                  </AlertDescription>
                </Alert>
              )}

              <Button type="submit" disabled={bookViewing.isPending} className="w-full">
                {bookViewing.isPending ? "Booking..." : "Book Viewing"}
              </Button>
            </>
          )}
        </form>
      </CardContent>
    </Card>
  );
}
