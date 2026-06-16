import { Link } from "react-router-dom";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Heart, Bed, Bath, Maximize, LayoutGrid } from "lucide-react";
import { useSavedListings } from "@/features/saved-listings/useSavedListings";
import { useSessionComparison } from "@/features/comparison/sessionComparison";

interface Listing {
  id: string;
  title: string;
  description: string;
  property_type: string;
  listing_purpose: "sale" | "rent";
  price: number | null;
  currency: string | null;
  bedrooms: number | null;
  bathrooms: number | null;
  area_size: number | null;
  area_unit: string;
  city: string;
  address: string;
  status: string;
  thumbnail_url?: string | null;
}

interface ListingCardProps {
  listing: Listing;
}

export function ListingCard({ listing }: ListingCardProps) {
  const { toggleSaved, isSaved: checkIsSaved } = useSavedListings();
  const { addToComparison, isInComparison, canAddMore } = useSessionComparison();
  const isSaved = checkIsSaved(listing.id);
  const inComparison = isInComparison(listing.id);

  const formatPrice = (price: number | null, currency: string | null) => {
    if (price === null || !currency) {
      return "Price on request";
    }
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency,
      maximumFractionDigits: 0,
    }).format(price);
  };

  return (
    <Card className="overflow-hidden">
      {listing.thumbnail_url ? (
        <div className="aspect-video w-full overflow-hidden">
          <img
            src={listing.thumbnail_url}
            alt={listing.title}
            className="h-full w-full object-cover"
          />
        </div>
      ) : (
        <div className="flex aspect-video w-full items-center justify-center bg-muted">
          <span className="text-xs text-muted-foreground">No image</span>
        </div>
      )}
      <CardHeader className="p-4">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg line-clamp-1">{listing.title}</CardTitle>
            <p className="text-sm text-muted-foreground line-clamp-1">{listing.address}, {listing.city}</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={(e) => {
              e.preventDefault();
              toggleSaved(listing.id);
            }}
          >
            <Heart className={`h-5 w-5 ${isSaved ? "fill-red-500 text-red-500" : ""}`} />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-4 pt-0">
        <div className="flex items-center gap-4 text-sm text-muted-foreground mb-2">
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
        <p className="text-sm text-muted-foreground line-clamp-2 mb-2">{listing.description}</p>
        <div className="flex items-center justify-between">
          <span className="text-2xl font-bold">
            {formatPrice(listing.price, listing.currency)}
          </span>
          <span className="text-sm text-muted-foreground capitalize">
            For {listing.listing_purpose}
          </span>
        </div>
      </CardContent>
      <CardFooter className="p-4 pt-0 flex gap-2">
        <Button asChild className="flex-1">
          <Link to={`/listings/${listing.id}`}>View Details</Link>
        </Button>
        <Button
          variant={inComparison ? "default" : "outline"}
          size="icon"
          onClick={(e) => {
            e.preventDefault();
            addToComparison(listing);
          }}
          disabled={inComparison || !canAddMore}
          title={inComparison ? "In comparison" : canAddMore ? "Add to comparison" : "Comparison full"}
        >
          <LayoutGrid className="h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  );
}
