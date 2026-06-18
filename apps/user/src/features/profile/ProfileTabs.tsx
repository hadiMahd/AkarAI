import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ProfileTab } from "@/pages/profile/ProfilePage";

interface ProfileTabsProps {
  activeTab: ProfileTab;
  onTabChange: (tab: ProfileTab) => void;
}

export function ProfileTabs({ activeTab, onTabChange }: ProfileTabsProps) {
  const tabs: Array<{ value: ProfileTab; label: string }> = [
    { value: "profile", label: "Profile" },
    { value: "saved", label: "Saved Listings" },
    { value: "inquiries", label: "Submitted Inquiries" },
    { value: "viewings", label: "Scheduled Viewings" },
  ];

  return (
    <div role="tablist" aria-label="Profile sections" className="grid w-full grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
      {tabs.map((tab) => (
        <Button
          key={tab.value}
          type="button"
          variant="ghost"
          role="tab"
          aria-selected={activeTab === tab.value}
          onClick={() => onTabChange(tab.value)}
          className={cn(
            "h-11 justify-center border",
            activeTab === tab.value
              ? "border-primary bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground"
              : "border-border bg-background text-muted-foreground hover:bg-accent hover:text-foreground"
          )}
        >
          {tab.label}
        </Button>
      ))}
    </div>
  );
}
