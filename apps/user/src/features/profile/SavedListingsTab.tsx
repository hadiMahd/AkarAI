import { Link } from "react-router-dom";
import { useSavedListings } from "@/features/saved-listings/useSavedListings";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Heart, Bed, Bath, Maximize } from "lucide-react";

export function SavedListingsTab() {
  const { savedListings, toggleSaved } = useSavedListings();

  if (savedListings.length === 0) {
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

  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency,
      maximumFractionDigits: 0,
    }).format(price);
  };

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {savedListings.map((listing) => (
        <Card key={listing.id} className="overflow-hidden">
          <CardContent className="p-4">
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <Link to={`/listings/${listing.id}`} className="font-semibold hover:underline">
                    {listing.title}
                  </Link>
                  <p className="text-sm text-muted-foreground">{listing.city}</p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => toggleSaved(listing)}
                  className="text-red-500"
                >
                  <Heart className="h-4 w-4 fill-current" />
                </Button>
              </div>

              <div className="text-2xl font-bold">
                {formatPrice(listing.price, listing.currency)}
              </div>

              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                {listing.bedrooms && (
                  <div className="flex items-center gap-1">
                    <Bed className="h-4 w-4" />
                    <span>{listing.bedrooms}</span>
                  </div>
                )}
                {listing.bathrooms && (
                  <div className="flex items-center gap-1">
                    <Bath className="h-4 w-4" />
                    <span>{listing.bathrooms}</span>
                  </div>
                )}
                {listing.area_size && (
                  <div className="flex items-center gap-1">
                    <Maximize className="h-4 w-4" />
                    <span>{listing.area_size} {listing.area_unit}</span>
                  </div>
                )}
              </div>

              <div className="flex gap-2">
                <Badge variant="outline">{listing.property_type}</Badge>
                <Badge variant={listing.listing_purpose === "sale" ? "default" : "secondary"}>
                  For {listing.listing_purpose}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
