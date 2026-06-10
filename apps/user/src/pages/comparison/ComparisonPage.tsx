import { useSessionComparison } from "@/features/comparison/sessionComparison";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/EmptyState";
import { X, Bed, Bath, Maximize } from "lucide-react";
import { Link } from "react-router-dom";

export function ComparisonPage() {
  const { comparisonListings, removeFromComparison, clearComparison } = useSessionComparison();

  if (comparisonListings.length === 0) {
    return (
      <EmptyState
        icon="search"
        title="No listings to compare"
        description="Add listings to comparison from the listings page to compare them side by side."
        action={{
          label: "Browse Listings",
          onClick: () => window.location.href = "/listings",
        }}
      />
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Compare Listings</h1>
          <p className="text-muted-foreground">
            Comparing {comparisonListings.length} {comparisonListings.length === 1 ? "listing" : "listings"}
          </p>
        </div>
        <Button variant="outline" onClick={clearComparison}>
          Clear All
        </Button>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {comparisonListings.map((listing) => (
          <Card key={listing.id}>
            <CardHeader className="p-4">
              <div className="flex items-start justify-between">
                <CardTitle className="text-lg line-clamp-2">{listing.title}</CardTitle>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeFromComparison(listing.id)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">{listing.address}, {listing.city}</p>
            </CardHeader>
            <CardContent className="p-4 pt-0 space-y-4">
              <div className="text-2xl font-bold">
                {formatPrice(listing.price, listing.currency)}
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Purpose</span>
                  <span className="capitalize">{listing.listing_purpose}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Type</span>
                  <span className="capitalize">{listing.property_type}</span>
                </div>
                {listing.bedrooms && (
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground flex items-center gap-1">
                      <Bed className="h-4 w-4" /> Bedrooms
                    </span>
                    <span>{listing.bedrooms}</span>
                  </div>
                )}
                {listing.bathrooms && (
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground flex items-center gap-1">
                      <Bath className="h-4 w-4" /> Bathrooms
                    </span>
                    <span>{listing.bathrooms}</span>
                  </div>
                )}
                {listing.area_size && (
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground flex items-center gap-1">
                      <Maximize className="h-4 w-4" /> Area
                    </span>
                    <span>{listing.area_size} {listing.area_unit}</span>
                  </div>
                )}
              </div>
              <Button asChild className="w-full" size="sm">
                <Link to={`/listings/${listing.id}`}>View Details</Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}