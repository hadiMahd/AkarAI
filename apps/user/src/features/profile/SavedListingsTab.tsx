import { Link } from "react-router-dom";
import { useSavedListings, useSavedListingsFull } from "@/features/saved-listings/useSavedListings";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Heart, Bed, Bath, Maximize } from "lucide-react";

export function SavedListingsTab() {
  const { savedListings: fullListings, isLoading } = useSavedListingsFull();
  const { unsave } = useSavedListings();

  if (isLoading) {
    return (
      <Card>
        <CardContent className="pt-6 text-center">
          <p className="text-muted-foreground">Loading saved listings...</p>
        </CardContent>
      </Card>
    );
  }

  if (fullListings.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6 text-center">
          <p className="text-muted-foreground">You haven't saved any listings yet.</p>
          <Button asChild className="mt-4">
            <Link to="/listings">Browse Listings</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  const formatPrice = (price: number | null, currency: string | null) => {
    if (price === null) return "Price on request";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency || "USD",
      maximumFractionDigits: 0,
    }).format(price);
  };

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {fullListings.map((item) => (
        <Card key={item.id} className="overflow-hidden">
          <CardContent className="p-4">
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <Link to={`/listings/${item.listing_id}`} className="font-semibold hover:underline">
                    {item.listing?.title || "Untitled Listing"}
                  </Link>
                  <p className="text-sm text-muted-foreground">{item.listing?.city || ""}</p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => unsave(item.listing_id)}
                  className="text-red-500"
                >
                  <Heart className="h-4 w-4 fill-current" />
                </Button>
              </div>

              <div className="text-2xl font-bold">
                {formatPrice(item.listing?.price ?? null, item.listing?.currency ?? null)}
              </div>

              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                {item.listing?.bedrooms && (
                  <div className="flex items-center gap-1">
                    <Bed className="h-4 w-4" />
                    <span>{item.listing.bedrooms}</span>
                  </div>
                )}
                {item.listing?.bathrooms && (
                  <div className="flex items-center gap-1">
                    <Bath className="h-4 w-4" />
                    <span>{item.listing.bathrooms}</span>
                  </div>
                )}
                {item.listing?.area_size && (
                  <div className="flex items-center gap-1">
                    <Maximize className="h-4 w-4" />
                    <span>{item.listing.area_size} {item.listing.area_unit}</span>
                  </div>
                )}
              </div>

              <div className="flex gap-2">
                <Badge variant="outline">{item.listing?.property_type}</Badge>
                <Badge variant={item.listing?.listing_purpose === "sale" ? "default" : "secondary"}>
                  For {item.listing?.listing_purpose}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
