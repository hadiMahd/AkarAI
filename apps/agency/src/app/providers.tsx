import { ReactNode, useEffect, useState } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { queryClient } from "@/lib/query/query-client";
import { restoreSession } from "@/lib/api/client";
import { clearLegacyStorage } from "@/lib/session/auth-session";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";

export function Providers({ children }: { children: ReactNode }) {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    clearLegacyStorage();
    restoreSession().finally(() => setIsReady(true));
  }, []);

  if (!isReady) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSkeleton />
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster />
    </QueryClientProvider>
  );
}
