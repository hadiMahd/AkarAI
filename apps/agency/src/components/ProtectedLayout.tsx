import { ReactNode } from "react";
import { Outlet, Link } from "react-router-dom";
import { useAgencyAuth } from "@/features/auth/useAgencyAuth";
import { useAgencyNavigation } from "@/features/navigation/useAgencyNavigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Settings,
  Users,
  Building2,
  Bot,
  MessageSquare,
  CheckCircle2,
  Calendar,
  AlertTriangle,
  FileText,
  LogOut,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useState } from "react";
import { isAgencyAdmin } from "@/lib/session/tenant-session";
import { getTenantSession } from "@/lib/session/auth-session";

const routeIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  dashboard: LayoutDashboard,
  profile: Settings,
  employees: Users,
  listings: Building2,
  leads: MessageSquare,
  leadsReviewed: CheckCircle2,
  viewings: Calendar,
  spamLeads: AlertTriangle,
  policyDocuments: FileText,
  policyAssistant: Bot,
};

export function ProtectedLayout({ children }: { children?: ReactNode }) {
  const { user, logout } = useAgencyAuth();
  const tenantSession = getTenantSession();
  const { navItems, isActiveRoute } = useAgencyNavigation(tenantSession);
  const showAdminSettings = isAgencyAdmin(tenantSession);
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-background flex">
      <aside
        className={cn(
          "fixed left-0 top-0 z-40 h-screen border-r bg-background transition-all duration-200",
          collapsed ? "w-16" : "w-64"
        )}
      >
        <div className="flex h-16 items-center border-b px-4">
          {!collapsed && (
            <Link to="/dashboard" className="flex items-center gap-2 font-bold text-lg">
              <Building2 className="h-6 w-6 text-primary" />
              <span>Agency</span>
            </Link>
          )}
          {collapsed && (
            <Link to="/dashboard" className="mx-auto">
              <Building2 className="h-6 w-6 text-primary" />
            </Link>
          )}
        </div>
        <nav className="flex flex-col gap-1 p-2">
          {navItems.map((item) => {
            const Icon = routeIcons[item.routeKey] || LayoutDashboard;
            const isActive = isActiveRoute(item.href);
            return (
              <Link
                key={item.routeKey}
                to={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                  collapsed && "justify-center px-2"
                )}
                title={collapsed ? item.name : undefined}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {!collapsed && <span>{item.name}</span>}
              </Link>
            );
          })}
        </nav>
        <div className="absolute bottom-4 left-0 right-0 px-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setCollapsed(!collapsed)}
            className="w-full justify-center"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>
      </aside>
      <div className={cn("flex-1 transition-all duration-200", collapsed ? "ml-16" : "ml-64")}>
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-background/95 backdrop-blur px-6">
          <div className="flex items-center gap-4">
            <h1 className="text-lg font-semibold">Agency Dashboard</h1>
          </div>
          <div className="flex items-center gap-4">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="gap-2">
                  <span className="text-sm">{user?.email}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                {showAdminSettings ? (
                  <>
                    <DropdownMenuItem asChild>
                      <Link to="/profile" className="flex items-center gap-2">
                        <Settings className="h-4 w-4" />
                        Profile Settings
                      </Link>
                    </DropdownMenuItem>
                    <Separator />
                  </>
                ) : null}
                <DropdownMenuItem onClick={() => logout()} className="text-destructive">
                  <LogOut className="h-4 w-4 mr-2" />
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>
        <main className="p-6">
          {children || <Outlet />}
        </main>
      </div>
    </div>
  );
}
