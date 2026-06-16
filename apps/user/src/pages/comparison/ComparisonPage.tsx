import { useState, useEffect } from "react";
import { useSessionComparison } from "@/features/comparison/sessionComparison";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/EmptyState";
import { X, Bed, Bath, Maximize, Sparkles, Loader2, WandSparkles } from "lucide-react";
import { Link } from "react-router-dom";
import {
  useComparisonSummaryMutation,
  type ComparisonSummaryResponse,
} from "@/features/comparison/useComparisonSummary";
import { getApiErrorMessage } from "@/lib/api/errors";

const COMPARISON_PHRASES = [
  "Analyzing properties…",
  "Comparing locations…",
  "Evaluating pricing…",
  "Checking amenities…",
  "Building your summary…",
];

function useRotatingPhrase(active: boolean, intervalMs = 1800) {
  const [index, setIndex] = useState(0);
  useEffect(() => {
    if (!active) { setIndex(0); return; }
    const id = setInterval(() => setIndex((i) => (i + 1) % COMPARISON_PHRASES.length), intervalMs);
    return () => clearInterval(id);
  }, [active, intervalMs]);
  return COMPARISON_PHRASES[index];
}

export function ComparisonPage() {
  const { comparisonListings, removeFromComparison, clearComparison } = useSessionComparison();
  const summaryMutation = useComparisonSummaryMutation();
  const [summary, setSummary] = useState<ComparisonSummaryResponse | null>(null);
  const summaryError = summaryMutation.error
    ? getApiErrorMessage(summaryMutation.error, "compare.update")
    : null;

  const loadingPhrase = useRotatingPhrase(summaryMutation.isPending);

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

  const handleGenerateSummary = async () => {
    const result = await summaryMutation.mutateAsync({
      listing_ids: comparisonListings.map((listing) => listing.id),
    });
    setSummary(result);
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
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => void handleGenerateSummary()}
            disabled={comparisonListings.length < 2 || summaryMutation.isPending}
          >
            {summaryMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {loadingPhrase}
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Compare with AI
              </>
            )}
          </Button>
          <Button variant="outline" onClick={clearComparison}>
            Clear All
          </Button>
        </div>
      </div>

      {(summary || summaryError) && (
        <Card className="border-dashed">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <WandSparkles className="h-4 w-4" />
              AI comparison
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            {summary?.summary && (
              <p className="leading-relaxed text-foreground">
                {summary.summary.replace(/#{1,6}\s*/g, "").replace(/\*\*/g, "").replace(/\*/g, "")}
              </p>
            )}
            {summary?.key_differences?.length ? (
              <div>
                <p className="mb-2 font-medium">Key differences</p>
                <ul className="space-y-1 text-muted-foreground list-disc list-inside">
                  {summary.key_differences.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {summary?.best_fit_notes?.length ? (
              <div>
                <p className="mb-2 font-medium">Best fit</p>
                <ul className="space-y-1 text-muted-foreground list-disc list-inside">
                  {summary.best_fit_notes.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {summaryError && <p className="text-destructive">{summaryError}</p>}
          </CardContent>
        </Card>
      )}

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
