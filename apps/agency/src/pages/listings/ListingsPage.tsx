import { useAgencyListings } from "@/features/listings/useAgencyListings";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Building2 } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

export function ListingsPage() {
  const { listings, isLoading } = useAgencyListings();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Listings</h2>
          <p className="text-muted-foreground">Manage your agency listings</p>
        </div>
        <Button asChild>
          <Link to="/listings/new">Create Listing</Link>
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Agency Listings
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-16 bg-muted animate-pulse rounded" />
              ))}
            </div>
          ) : listings.length === 0 ? (
            <p className="text-muted-foreground">No listings found. Create your first listing above.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-2 font-medium">Title</th>
                    <th className="text-left py-3 px-2 font-medium">Status</th>
                    <th className="text-left py-3 px-2 font-medium">Price</th>
                    <th className="text-left py-3 px-2 font-medium">Location</th>
                    <th className="text-left py-3 px-2 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {listings.map((listing) => (
                    <tr key={listing.id} className="border-b">
                      <td className="py-3 px-2">{listing.title}</td>
                      <td className="py-3 px-2">
                        <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs ${
                          listing.status === "active"
                            ? "bg-green-100 text-green-700"
                            : "bg-gray-100 text-gray-700"
                        }`}>
                          {listing.status}
                        </span>
                      </td>
                      <td className="py-3 px-2">
                        {listing.price ? `${listing.currency || ""} ${listing.price}` : "—"}
                      </td>
                      <td className="py-3 px-2">{listing.location_text || listing.city || "—"}</td>
                      <td className="py-3 px-2">
                        <Button variant="ghost" size="sm" asChild>
                          <Link to={`/listings/${listing.id}`}>Edit</Link>
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
