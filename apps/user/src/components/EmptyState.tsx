import { cn } from "@/lib/utils";
import { Home, Search, Heart, MessageSquare, Calendar } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: "home" | "search" | "saved" | "inquiry" | "viewing";
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

const icons = {
  home: Home,
  search: Search,
  saved: Heart,
  inquiry: MessageSquare,
  viewing: Calendar,
};

export function EmptyState({
  title,
  description,
  icon = "search",
  action,
  className,
}: EmptyStateProps) {
  const Icon = icons[icon];

  return (
    <div className={cn("flex flex-col items-center justify-center py-12 px-4 text-center", className)}>
      <Icon className="h-12 w-12 text-muted-foreground/50 mb-4" />
      <h3 className="text-lg font-medium text-foreground mb-2">{title}</h3>
      <p className="text-muted-foreground max-w-sm mb-6">{description}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}