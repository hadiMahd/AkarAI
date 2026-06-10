import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Search, Heart, LayoutGrid, MessageSquare, Calendar } from "lucide-react";
import { useAuth } from "@/features/auth/useAuth";

export function HomePage() {
  const { user } = useAuth();

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-3xl font-bold mb-2">Welcome back, {user?.name || "User"}!</h1>
        <p className="text-muted-foreground">
          What would you like to do today?
        </p>
      </section>

      <section className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <Search className="h-8 w-8 text-primary mb-2" />
            <CardTitle>Browse Listings</CardTitle>
            <CardDescription>
              Search and filter available properties
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild className="w-full">
              <Link to="/listings">Browse Now</Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <Heart className="h-8 w-8 text-primary mb-2" />
            <CardTitle>Saved Listings</CardTitle>
            <CardDescription>
              View your saved properties
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline" className="w-full">
              <Link to="/listings?saved=true">View Saved</Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <LayoutGrid className="h-8 w-8 text-primary mb-2" />
            <CardTitle>Compare Properties</CardTitle>
            <CardDescription>
              Compare up to 4 properties side by side
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline" className="w-full">
              <Link to="/comparison">Compare</Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <MessageSquare className="h-8 w-8 text-primary mb-2" />
            <CardTitle>My Inquiries</CardTitle>
            <CardDescription>
              View your submitted inquiries
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline" className="w-full">
              <Link to="/profile?tab=inquiries">View Inquiries</Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <Calendar className="h-8 w-8 text-primary mb-2" />
            <CardTitle>My Viewings</CardTitle>
            <CardDescription>
              View your scheduled viewings
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline" className="w-full">
              <Link to="/profile?tab=viewings">View Viewings</Link>
            </Button>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}