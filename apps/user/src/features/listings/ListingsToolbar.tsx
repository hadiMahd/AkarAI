interface ListingsToolbarProps {
  total: number;
  sortBy: string;
  sortOrder: string;
  onSortChange: (sortBy: string, sortOrder: string) => void;
}

export function ListingsToolbar({ total, sortBy, sortOrder, onSortChange }: ListingsToolbarProps) {
  return (
    <div className="flex items-center justify-between">
      <p className="text-sm text-muted-foreground">
        Showing {total} {total === 1 ? "listing" : "listings"}
      </p>
      <div className="flex items-center gap-2">
        <label htmlFor="sort" className="text-sm text-muted-foreground">
          Sort by:
        </label>
        <select
          id="sort"
          value={`${sortBy}-${sortOrder}`}
          onChange={(e) => {
            const [newSortBy, newSortOrder] = e.target.value.split("-");
            onSortChange(newSortBy, newSortOrder);
          }}
          className="flex h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
        >
          <option value="created_at-desc">Newest</option>
          <option value="created_at-asc">Oldest</option>
          <option value="price-asc">Price: Low to High</option>
          <option value="price-desc">Price: High to Low</option>
          <option value="area_size-desc">Area: Large to Small</option>
          <option value="area_size-asc">Area: Small to Large</option>
        </select>
      </div>
    </div>
  );
}