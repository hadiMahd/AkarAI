import { useAuth } from "./useAuth";
import { Button } from "@/components/ui/button";
import { LogOut } from "lucide-react";

export function AuthActions() {
  const { logout, user } = useAuth();

  if (!user) return null;

  return (
    <Button variant="ghost" size="sm" onClick={() => logout()}>
      <LogOut className="h-4 w-4 mr-2" />
      Sign Out
    </Button>
  );
}