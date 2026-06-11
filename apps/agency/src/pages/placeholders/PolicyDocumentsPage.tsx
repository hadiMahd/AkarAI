import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText } from "lucide-react";

export function PolicyDocumentsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Policy Documents</h2>
        <p className="text-muted-foreground">Manage agency policy documents</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-muted-foreground" />
            Feature Coming Soon
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Policy document upload and management will be available in a future phase.
            This section is currently a placeholder.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
