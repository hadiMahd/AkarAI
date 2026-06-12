import { useState } from "react";
import { useRagDocuments, useUploadRagDocument, useRagDocument, downloadRagDocument } from "@/features/rag/useRagDocuments";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, Upload, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function RagDocumentsPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading, refetch } = useRagDocuments(page, 20);
  const uploadMutation = useUploadRagDocument();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    
    try {
      await uploadMutation.mutateAsync(selectedFile);
      setSelectedFile(null);
      refetch();
    } catch (error) {
      console.error("Upload failed:", error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Policy Documents</h2>
          <p className="text-muted-foreground">Upload and manage policy documents for RAG ingestion</p>
        </div>
        <Button variant="outline" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload New Document
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <Input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="flex-1"
            />
            <Button
              onClick={handleUpload}
              disabled={!selectedFile || uploadMutation.isPending}
            >
              {uploadMutation.isPending ? "Uploading..." : "Upload"}
            </Button>
          </div>
          {uploadMutation.error && (
            <p className="text-sm text-destructive mt-2">
              Upload failed: {(uploadMutation.error as Error).message}
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Documents
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-16 bg-muted animate-pulse rounded" />
              ))}
            </div>
          ) : !data || data.items.length === 0 ? (
            <p className="text-muted-foreground">No documents uploaded yet.</p>
          ) : (
            <div className="space-y-4">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-2 font-medium">Filename</th>
                      <th className="text-left py-3 px-2 font-medium">Status</th>
                      <th className="text-left py-3 px-2 font-medium">Uploaded</th>
                      <th className="text-left py-3 px-2 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.map((doc) => (
                      <RagDocumentRow key={doc.id} documentId={doc.id} filename={doc.filename} status={doc.status} createdAt={doc.created_at} />
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  Page {data.page} of {Math.ceil(data.total / data.size)} ({data.total} total)
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => p + 1)}
                    disabled={page >= Math.ceil(data.total / data.size)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function RagDocumentRow({ documentId, filename, status, createdAt }: { documentId: string; filename: string; status: string; createdAt: string }) {
  const { document } = useRagDocument(documentId);
  const currentStatus = document?.status || status;

  const statusColors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-700",
    processing: "bg-blue-100 text-blue-700",
    processed: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
  };

  return (
    <tr className="border-b">
      <td className="py-3 px-2">{filename}</td>
      <td className="py-3 px-2">
        <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs ${statusColors[currentStatus] || "bg-gray-100 text-gray-700"}`}>
          {currentStatus}
        </span>
      </td>
      <td className="py-3 px-2">{new Date(createdAt).toLocaleDateString()}</td>
      <td className="py-3 px-2">
        <Button
          variant="ghost"
          size="sm"
          disabled={currentStatus !== "processed" || !document}
          onClick={async () => {
            if (!document) return;
            const previewWindow = window.open("about:blank", "_blank");
            if (!previewWindow) return;
            previewWindow.opener = null;

            try {
              const blob = await downloadRagDocument(document);
              const url = URL.createObjectURL(blob);
              previewWindow.location.href = url;
              window.setTimeout(() => URL.revokeObjectURL(url), 60000);
            } catch (error) {
              previewWindow.close();
              throw error;
            }
          }}
        >
          View
        </Button>
      </td>
    </tr>
  );
}
