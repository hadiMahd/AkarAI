import { cn } from "@/lib/utils";

export function LoadingSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center justify-center min-h-[200px]", className)}>
      <div className="flex flex-col items-center gap-4">
        <div className="animate-pulse">
          <div className="h-12 w-12 rounded-full bg-muted" />
        </div>
        <p className="text-muted-foreground">Loading...</p>
      </div>
    </div>
  );
}

export function CardSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("animate-pulse space-y-4", className)}>
      <div className="h-40 w-full rounded-lg bg-muted" />
      <div className="h-4 w-3/4 bg-muted rounded" />
      <div className="h-4 w-1/2 bg-muted rounded" />
      <div className="h-4 w-1/4 bg-muted rounded" />
    </div>
  );
}

export function ListSkeleton({ count = 5, className }: { count?: number; className?: string }) {
  return (
    <div className={cn("space-y-4", className)}>
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}