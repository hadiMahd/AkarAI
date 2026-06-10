import { ReactNode, useEffect, useState } from "react";
import { Toaster } from "@/components/ui/toaster";
import { restoreSession } from "@/lib/api/client";
import { clearLegacyStorage } from "@/lib/session/auth-session";

export function Providers({ children }: { children: ReactNode }) {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    clearLegacyStorage();
    restoreSession().finally(() => setIsReady(true));
  }, []);

  if (!isReady) {
    return null;
  }

  return (
    <>
      {children}
      <Toaster />
    </>
  );
}
