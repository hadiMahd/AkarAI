import { useState, type FormEvent } from "react";
import { useAgencyListings } from "./useAgencyListings";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import { useNavigate } from "react-router-dom";

export function ListingForm() {
  const { createListing, isCreating, createError } = useAgencyListings();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    property_type: "",
    listing_purpose: "rent",
    price: "",
    currency: "USD",
    bedrooms: "",
    bathrooms: "",
    area_size: "",
    area_unit: "sqft",
    furnishing: "",
    location_text: "",
    address: "",
    city: "",
    country: "",
  });
  const [successMessage, setSuccessMessage] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSuccessMessage("");
    try {
      const listing = await createListing({
        ...formData,
        price: formData.price ? parseFloat(formData.price) : undefined,
        bedrooms: formData.bedrooms ? parseInt(formData.bedrooms) : undefined,
        bathrooms: formData.bathrooms ? parseInt(formData.bathrooms) : undefined,
        area_size: formData.area_size ? parseFloat(formData.area_size) : undefined,
        status: "active",
      });
      setSuccessMessage("Listing created and published successfully!");
      setTimeout(() => navigate(`/listings/${listing.id}`), 1500);
    } catch {
      // Error is handled by the mutation
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create New Listing</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {successMessage && (
            <div className="flex items-center gap-2 p-3 rounded-md bg-green-50 text-green-700 text-sm">
              <CheckCircle2 className="h-4 w-4" />
              <span>{successMessage}</span>
            </div>
          )}
          {createError && (
            <div className="flex items-center gap-2 p-3 rounded-md bg-destructive/10 text-destructive text-sm">
              <AlertCircle className="h-4 w-4" />
              <span>Failed to create listing</span>
            </div>
          )}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="property_type">Property Type</Label>
              <Input
                id="property_type"
                value={formData.property_type}
                onChange={(e) => setFormData({ ...formData, property_type: e.target.value })}
                placeholder="Apartment, House, etc."
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="listing_purpose">Purpose</Label>
              <select
                id="listing_purpose"
                value={formData.listing_purpose}
                onChange={(e) => setFormData({ ...formData, listing_purpose: e.target.value })}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="rent">Rent</option>
                <option value="sale">Sale</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="price">Price</Label>
              <Input
                id="price"
                type="number"
                value={formData.price}
                onChange={(e) => setFormData({ ...formData, price: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="currency">Currency</Label>
              <Input
                id="currency"
                value={formData.currency}
                onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="bedrooms">Bedrooms</Label>
              <Input
                id="bedrooms"
                type="number"
                value={formData.bedrooms}
                onChange={(e) => setFormData({ ...formData, bedrooms: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="bathrooms">Bathrooms</Label>
              <Input
                id="bathrooms"
                type="number"
                value={formData.bathrooms}
                onChange={(e) => setFormData({ ...formData, bathrooms: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="area_size">Area Size</Label>
              <Input
                id="area_size"
                type="number"
                value={formData.area_size}
                onChange={(e) => setFormData({ ...formData, area_size: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="area_unit">Area Unit</Label>
              <Input
                id="area_unit"
                value={formData.area_unit}
                onChange={(e) => setFormData({ ...formData, area_unit: e.target.value })}
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="location_text">Location</Label>
              <Input
                id="location_text"
                value={formData.location_text}
                onChange={(e) => setFormData({ ...formData, location_text: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="address">Address</Label>
              <Input
                id="address"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="city">City</Label>
              <Input
                id="city"
                value={formData.city}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="country">Country</Label>
              <Input
                id="country"
                value={formData.country}
                onChange={(e) => setFormData({ ...formData, country: e.target.value })}
              />
            </div>
          </div>
          <Button type="submit" disabled={isCreating}>
            {isCreating ? "Creating..." : "Create & Publish Listing"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
