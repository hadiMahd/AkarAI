import { Link } from "react-router-dom";
import { useSessionComparison } from "./sessionComparison";
import { Button } from "../../components/ui/button";
import { Card, CardContent } from "../../components/ui/card";
import { X } from "lucide-react";

export function ComparisonTray() {
  const { comparisonListings: items, removeFromComparison: removeItem, clearComparison: clearAll } = useSessionComparison();

  if (items.length === 0) {
    return null;
  }

  return (
    <Card className="fixed bottom-4 right-4 z-50 w-80 shadow-lg">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-sm">
            Compare ({items.length}/4)
          </h3>
          <Button variant="ghost" size="sm" onClick={clearAll}>
            Clear
          </Button>
        </div>

        <div className="space-y-2 mb-3">
          {items.map((item: { id: string; title: string }) => (
            <div
              key={item.id}
              className="flex items-center justify-between text-xs bg-muted p-2 rounded"
            >
              <span className="truncate flex-1">{item.title}</span>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={() => removeItem(item.id)}
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          ))}
        </div>

        <Link to="/comparison">
          <Button className="w-full" size="sm">
            View Comparison
          </Button>
        </Link>
      </CardContent>
    </Card>
  );
}
