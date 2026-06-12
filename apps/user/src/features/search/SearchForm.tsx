import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";

interface SearchFilters {
  q?: string;
  purpose?: string;
  property_type?: string;
  city?: string;
  min_price?: number;
  max_price?: number;
  min_bedrooms?: number;
  min_bathrooms?: number;
  furnishing?: string;
  min_area_size?: number;
  max_area_size?: number;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  page_size?: number;
}

interface SearchFormProps {
  filters: SearchFilters;
  onFilterChange: (filters: SearchFilters) => void;
}

export function SearchForm({ filters, onFilterChange }: SearchFormProps) {
  const [localFilters, setLocalFilters] = useState<SearchFilters>(filters);

  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onFilterChange({ ...localFilters, page: 1 });
  };

  const handleReset = () => {
    setLocalFilters({});
    onFilterChange({});
  };

  return (
    <form onSubmit={handleSearch} className="space-y-4">
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="space-y-2">
          <Label htmlFor="q">Search</Label>
          <Input
            id="q"
            placeholder="Search listings..."
            value={localFilters.q || ""}
            onChange={(e) => setLocalFilters({ ...localFilters, q: e.target.value })}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="purpose">Purpose</Label>
          <select
            id="purpose"
            value={localFilters.purpose || ""}
            onChange={(e) => setLocalFilters({ ...localFilters, purpose: e.target.value })}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">All</option>
            <option value="sale">For Sale</option>
            <option value="rent">For Rent</option>
          </select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="property_type">Property Type</Label>
          <select
            id="property_type"
            value={localFilters.property_type || ""}
            onChange={(e) => setLocalFilters({ ...localFilters, property_type: e.target.value })}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">All Types</option>
            <option value="apartment">Apartment</option>
            <option value="house">House</option>
            <option value="villa">Villa</option>
            <option value="land">Land</option>
            <option value="commercial">Commercial</option>
          </select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="city">City</Label>
          <Input
            id="city"
            placeholder="City"
            value={localFilters.city || ""}
            onChange={(e) => setLocalFilters({ ...localFilters, city: e.target.value })}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="min_price">Min Price</Label>
          <Input
            id="min_price"
            type="number"
            placeholder="Min"
            value={localFilters.min_price || ""}
            onChange={(e) =>
              setLocalFilters({
                ...localFilters,
                min_price: e.target.value ? Number(e.target.value) : undefined,
              })
            }
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="max_price">Max Price</Label>
          <Input
            id="max_price"
            type="number"
            placeholder="Max"
            value={localFilters.max_price || ""}
            onChange={(e) =>
              setLocalFilters({
                ...localFilters,
                max_price: e.target.value ? Number(e.target.value) : undefined,
              })
            }
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="min_bedrooms">Min Bedrooms</Label>
          <Input
            id="min_bedrooms"
            type="number"
            placeholder="Min"
            value={localFilters.min_bedrooms || ""}
            onChange={(e) =>
              setLocalFilters({
                ...localFilters,
                min_bedrooms: e.target.value ? Number(e.target.value) : undefined,
              })
            }
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="min_bathrooms">Min Bathrooms</Label>
          <Input
            id="min_bathrooms"
            type="number"
            placeholder="Min"
            value={localFilters.min_bathrooms || ""}
            onChange={(e) =>
              setLocalFilters({
                ...localFilters,
                min_bathrooms: e.target.value ? Number(e.target.value) : undefined,
              })
            }
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="furnishing">Furnishing</Label>
          <select
            id="furnishing"
            value={localFilters.furnishing || ""}
            onChange={(e) => setLocalFilters({ ...localFilters, furnishing: e.target.value || undefined })}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">Any</option>
            <option value="furnished">Furnished</option>
            <option value="semi_furnished">Semi Furnished</option>
            <option value="unfurnished">Unfurnished</option>
          </select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="min_area_size">Min Area</Label>
          <Input
            id="min_area_size"
            type="number"
            placeholder="Min area"
            value={localFilters.min_area_size || ""}
            onChange={(e) =>
              setLocalFilters({
                ...localFilters,
                min_area_size: e.target.value ? Number(e.target.value) : undefined,
              })
            }
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="max_area_size">Max Area</Label>
          <Input
            id="max_area_size"
            type="number"
            placeholder="Max area"
            value={localFilters.max_area_size || ""}
            onChange={(e) =>
              setLocalFilters({
                ...localFilters,
                max_area_size: e.target.value ? Number(e.target.value) : undefined,
              })
            }
          />
        </div>
      </div>

      <div className="flex gap-2">
        <Button type="submit">
          <Search className="h-4 w-4 mr-2" />
          Search
        </Button>
        <Button type="button" variant="outline" onClick={handleReset}>
          Reset
        </Button>
      </div>
    </form>
  );
}
