import { ViewingFilters } from "@/features/viewings/ViewingFilters";

export function ViewingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Viewing Schedules</h2>
        <p className="text-muted-foreground">View and manage scheduled viewings</p>
      </div>
      <ViewingFilters />
    </div>
  );
}
