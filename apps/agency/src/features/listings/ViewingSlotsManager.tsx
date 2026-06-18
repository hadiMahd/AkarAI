import { useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { useViewingSlots } from "@/features/listings/useViewingSlots";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Calendar, Plus, Trash2, ArrowLeft } from "lucide-react";

function minViewingDateTimeLocal() {
  const minimum = new Date(Date.now() + 5 * 60 * 1000);
  minimum.setSeconds(0, 0);
  return minimum.toISOString().slice(0, 16);
}

interface ViewingSlotsManagerProps {
  listingId?: string | null;
  embedded?: boolean;
}

export function ViewingSlotsManager({ listingId: listingIdProp = null, embedded = false }: ViewingSlotsManagerProps) {
  const { listingId: routeListingId } = useParams();
  const listingId = listingIdProp ?? routeListingId ?? "";
  const { slots, isLoading, createSlot, isCreating, deactivateSlot, isDeactivating } = useViewingSlots(listingId);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    starts_at: "",
    ends_at: "",
    capacity: "1",
  });
  const minimumSlotStart = minViewingDateTimeLocal();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await createSlot({
        starts_at: new Date(formData.starts_at).toISOString(),
        ends_at: new Date(formData.ends_at).toISOString(),
        capacity: parseInt(formData.capacity),
      });
      setShowForm(false);
      setFormData({ starts_at: "", ends_at: "", capacity: "1" });
    } catch {
      // Error is handled by the mutation
    }
  };

  if (!listingId) {
    return <p>No listing selected</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Viewing Slots</h2>
          <p className="text-muted-foreground">
            Manage the dates and time windows buyers can book for this listing.
          </p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Slot
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create Viewing Slot</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-2">
                  <Label htmlFor="starts_at">Start Time</Label>
                  <Input
                    id="starts_at"
                    type="datetime-local"
                    value={formData.starts_at}
                    onChange={(e) => setFormData({ ...formData, starts_at: e.target.value })}
                    min={minimumSlotStart}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ends_at">End Time</Label>
                  <Input
                    id="ends_at"
                    type="datetime-local"
                    value={formData.ends_at}
                    onChange={(e) => setFormData({ ...formData, ends_at: e.target.value })}
                    min={formData.starts_at || minimumSlotStart}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="capacity">Capacity</Label>
                  <Input
                    id="capacity"
                    type="number"
                    min="1"
                    value={formData.capacity}
                    onChange={(e) => setFormData({ ...formData, capacity: e.target.value })}
                    required
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <Button type="submit" disabled={isCreating}>
                  {isCreating ? "Creating..." : "Create Slot"}
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Available Slots
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-16 bg-muted animate-pulse rounded" />
              ))}
            </div>
          ) : slots.length === 0 ? (
            <p className="text-muted-foreground">No viewing slots created yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-2 font-medium">Start</th>
                    <th className="text-left py-3 px-2 font-medium">End</th>
                    <th className="text-left py-3 px-2 font-medium">Capacity</th>
                    <th className="text-left py-3 px-2 font-medium">Reserved</th>
                    <th className="text-left py-3 px-2 font-medium">Status</th>
                    <th className="text-left py-3 px-2 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {slots.map((slot) => (
                    <tr key={slot.id} className="border-b">
                      <td className="py-3 px-2">{new Date(slot.starts_at).toLocaleString()}</td>
                      <td className="py-3 px-2">{new Date(slot.ends_at).toLocaleString()}</td>
                      <td className="py-3 px-2">{slot.capacity}</td>
                      <td className="py-3 px-2">{slot.reserved_count}</td>
                      <td className="py-3 px-2">
                        <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs ${
                          slot.status === "active"
                            ? "bg-green-100 text-green-700"
                            : "bg-gray-100 text-gray-700"
                        }`}>
                          {slot.status}
                        </span>
                      </td>
                      <td className="py-3 px-2">
                        {slot.status === "active" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deactivateSlot(slot.id)}
                            disabled={isDeactivating}
                            className="text-destructive hover:text-destructive"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {!embedded ? (
        <Button variant="outline" asChild>
          <Link to="/listings">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Listings
          </Link>
        </Button>
      ) : null}
    </div>
  );
}
