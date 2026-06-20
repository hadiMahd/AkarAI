import { ReactNode } from "react";
import { Outlet, Link, useLocation } from "react-router-dom";
import { useAuth } from "@/features/auth/useAuth";
import { cn } from "@/lib/utils";
import { LogOut, Home, Search, Heart, MessageSquare, Calendar, LayoutGrid, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";

const navigation = [
  {
    name: "Home",
    href: "/home",
    icon: Home,
    isActive: (pathname: string) => pathname === "/home",
  },
  {
    name: "Browse",
    href: "/listings",
    icon: Search,
    isActive: (pathname: string, search: string) =>
      pathname === "/listings" && new URLSearchParams(search).get("saved") !== "true",
  },
  {
    name: "Saved",
    href: "/listings?saved=true",
    icon: Heart,
    isActive: (pathname: string, search: string) =>
      pathname === "/listings" && new URLSearchParams(search).get("saved") === "true",
  },
  {
    name: "Compare",
    href: "/comparison",
    icon: LayoutGrid,
    isActive: (pathname: string) => pathname === "/comparison",
  },
  {
    name: "Inquiries",
    href: "/profile?tab=inquiries",
    icon: MessageSquare,
    isActive: (pathname: string, search: string) =>
      pathname === "/profile" && new URLSearchParams(search).get("tab") === "inquiries",
  },
  {
    name: "Viewings",
    href: "/profile?tab=viewings",
    icon: Calendar,
    isActive: (pathname: string, search: string) =>
      pathname === "/profile" && new URLSearchParams(search).get("tab") === "viewings",
  },
];

interface ProtectedLayoutProps {
  children?: ReactNode;
}

export function ProtectedLayout({ children }: ProtectedLayoutProps) {
  const { user, logout } = useAuth();
  const location = useLocation();

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-8">
            <Link to="/home" className="font-bold text-xl">
              <span className="text-primary">Aqar</span>
              <span className="text-foreground">Ai</span>
            </Link>
            <nav className="hidden md:flex items-center gap-1">
              {navigation.map((item) => {
                const isActive = item.isActive(location.pathname, location.search);
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={cn(
                      "flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-md transition-colors",
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:text-foreground hover:bg-accent"
                    )}
                  >
                    <item.icon className="h-4 w-4" />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="relative h-9 w-9 rounded-full"
                  aria-label="Account menu"
                >
                  <Avatar className="h-9 w-9">
                    <AvatarImage src={user?.avatar_url || ""} alt={user?.name || "User"} />
                    <AvatarFallback>{user?.name?.[0]?.toUpperCase() || "U"}</AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="end" forceMount>
                <div className="px-2 py-1">
                  <p className="text-sm font-medium truncate">{user?.name}</p>
                  <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                </div>
                <Separator />
                <DropdownMenuItem asChild>
                  <Link to="/profile" className="flex items-center gap-2">
                    <User className="h-4 w-4" />
                    Profile
                  </Link>
                </DropdownMenuItem>
                <Separator />
                <DropdownMenuItem
                  onClick={() => {
                    logout();
                    window.location.href = "/";
                  }}
                  className="text-destructive focus:text-destructive"
                >
                  <LogOut className="h-4 w-4 mr-2" />
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>
      <main className="container py-6 px-4">
        {children || <Outlet />}
      </main>
    </div>
  );
}
