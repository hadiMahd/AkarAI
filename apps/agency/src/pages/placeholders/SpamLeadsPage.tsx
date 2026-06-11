import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangle } from "lucide-react";

export function SpamLeadsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Spam Leads</h2>
        <p className="text-muted-foreground">Manage flagged spam leads</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-muted-foreground" />
            Feature Coming Soon
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Spam lead classification and management will be available in a future phase.
            This section is currently a placeholder.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
