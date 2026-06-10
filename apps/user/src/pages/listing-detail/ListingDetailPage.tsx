import { useParams, Link } from "react-router-dom";
import { useListingDetail } from "@/features/listings/useListingDetail";
import { useSavedListings } from "@/features/saved-listings/useSavedListings";
import { useSessionComparison } from "@/features/comparison/sessionComparison";
import { InquiryForm } from "@/features/inquiries/InquiryForm";
import { BookingForm } from "@/features/viewings/BookingForm";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { ErrorState } from "@/components/ErrorState";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Heart, LayoutGrid, Bed, Bath, Maximize, MapPin, ArrowLeft } from "lucide-react";

export function ListingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { savedListings, toggleSaved } = useSavedListings();
  const { addToComparison, isInComparison, canAddMore } = useSessionComparison();

  const { data: listing, isLoading, error } = useListingDetail(id);

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (error || !listing) {
    return (
      <ErrorState
        message="Listing unavailable or not found."
        onRetry={() => window.location.reload()}
      />
    );
  }

  const isSaved = savedListings.some((l) => l.id === listing.id);
  const inComparison = isInComparison(listing.id);

  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency,
      maximumFractionDigits: 0,
    }).format(price);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link to="/listings">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </Button>
        <h1 className="text-3xl font-bold">{listing.title}</h1>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-2xl">{listing.title}</CardTitle>
                  <p className="text-muted-foreground flex items-center gap-1 mt-1">
                    <MapPin className="h-4 w-4" />
                    {listing.address}, {listing.city}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={listing.listing_purpose === "sale" ? "default" : "secondary"}>
                    For {listing.listing_purpose}
                  </Badge>
                  <Badge variant="outline">{listing.property_type}</Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="text-4xl font-bold">
                {formatPrice(listing.price, listing.currency)}
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {listing.bedrooms && (
                  <div className="flex flex-col items-center p-4 bg-muted rounded-lg">
                    <Bed className="h-6 w-6 mb-2" />
                    <span className="text-2xl font-bold">{listing.bedrooms}</span>
                    <span className="text-sm text-muted-foreground">Bedrooms</span>
                  </div>
                )}
                {listing.bathrooms && (
                  <div className="flex flex-col items-center p-4 bg-muted rounded-lg">
                    <Bath className="h-6 w-6 mb-2" />
                    <span className="text-2xl font-bold">{listing.bathrooms}</span>
                    <span className="text-sm text-muted-foreground">Bathrooms</span>
                  </div>
                )}
                {listing.area_size && (
                  <div className="flex flex-col items-center p-4 bg-muted rounded-lg">
                    <Maximize className="h-6 w-6 mb-2" />
                    <span className="text-2xl font-bold">{listing.area_size}</span>
                    <span className="text-sm text-muted-foreground">{listing.area_unit}</span>
                  </div>
                )}
                {listing.furnishing && (
                  <div className="flex flex-col items-center p-4 bg-muted rounded-lg">
                    <span className="text-2xl font-bold capitalize">{listing.furnishing}</span>
                    <span className="text-sm text-muted-foreground">Furnishing</span>
                  </div>
                )}
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-2">Description</h3>
                <p className="text-muted-foreground whitespace-pre-wrap">{listing.description}</p>
              </div>
            </CardContent>
          </Card>

          <div id="inquiry">
            <InquiryForm listingId={listing.id} />
          </div>

          <div id="viewing">
            <BookingForm listingId={listing.id} />
          </div>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                variant={isSaved ? "default" : "outline"}
                className="w-full"
                onClick={() => toggleSaved(listing)}
              >
                <Heart className={`h-4 w-4 mr-2 ${isSaved ? "fill-current" : ""}`} />
                {isSaved ? "Saved" : "Save Listing"}
              </Button>

              <Button
                variant={inComparison ? "default" : "outline"}
                className="w-full"
                onClick={() => addToComparison(listing)}
                disabled={inComparison || !canAddMore}
              >
                <LayoutGrid className="h-4 w-4 mr-2" />
                {inComparison ? "In Comparison" : canAddMore ? "Add to Comparison" : "Comparison Full"}
              </Button>

              <Button asChild className="w-full" variant="outline">
                <a href="#inquiry">Submit Inquiry</a>
              </Button>

              <Button asChild className="w-full" variant="outline">
                <a href="#viewing">Book Viewing</a>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
