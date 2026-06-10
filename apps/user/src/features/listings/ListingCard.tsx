import { Link } from "react-router-dom";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Heart, Bed, Bath, Maximize } from "lucide-react";
import { useSavedListings } from "@/features/saved-listings/useSavedListings";

interface Listing {
  id: string;
  title: string;
  description: string;
  property_type: string;
  listing_purpose: "sale" | "rent";
  price: number;
  currency: string;
  bedrooms: number | null;
  bathrooms: number | null;
  area_size: number | null;
  area_unit: string;
  city: string;
  address: string;
  status: string;
}

interface ListingCardProps {
  listing: Listing;
}

export function ListingCard({ listing }: ListingCardProps) {
  const { toggleSaved, isSaved: checkIsSaved } = useSavedListings();
  const isSaved = checkIsSaved(listing.id);

  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency,
      maximumFractionDigits: 0,
    }).format(price);
  };

  return (
    <Card className="overflow-hidden">
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
      <CardFooter className="p-4 pt-0">
        <Button asChild className="w-full">
          <Link to={`/listings/${listing.id}`}>View Details</Link>
        </Button>
      </CardFooter>
    </Card>
  );
}