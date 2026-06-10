import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Search, Heart, Calendar, ArrowRight } from "lucide-react";
import { useAuth } from "@/features/auth/useAuth";

export function LandingPage() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <header className="container mx-auto px-4 py-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">
          <span className="text-primary">Akar</span>AI
        </h1>
        {isAuthenticated ? (
          <Button asChild>
            <Link to="/home">Go to Dashboard</Link>
          </Button>
        ) : (
          <div className="flex items-center gap-2">
            <Button variant="ghost" asChild>
              <Link to="/sign-in">Sign In</Link>
            </Button>
            <Button asChild>
              <Link to="/sign-up">Sign Up</Link>
            </Button>
          </div>
        )}
      </header>

      <main className="container mx-auto px-4 py-16">
        <section className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Find Your Perfect Home in Lebanon
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
            Browse listings, save your favorites, compare properties, and book viewings — all in one place.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Button size="lg" asChild>
              <Link to={isAuthenticated ? "/home" : "/sign-up"}>
                Get Started
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            {!isAuthenticated && (
              <Button variant="outline" size="lg" asChild>
                <Link to="/sign-in">Sign In</Link>
              </Button>
            )}
          </div>
        </section>

        <section className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          <Card>
            <CardHeader>
              <Search className="h-8 w-8 text-primary mb-2" />
              <CardTitle>Browse Listings</CardTitle>
              <CardDescription>
                Search through available properties with powerful filters and sorting options.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Filter by location, price, property type, and more.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Heart className="h-8 w-8 text-primary mb-2" />
              <CardTitle>Save & Compare</CardTitle>
              <CardDescription>
                Save your favorite listings and compare up to 4 properties side by side.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Keep track of properties you're interested in.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Calendar className="h-8 w-8 text-primary mb-2" />
              <CardTitle>Book Viewings</CardTitle>
              <CardDescription>
                Schedule property viewings directly from the listing page.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Choose available time slots that work for you.
              </p>
            </CardContent>
          </Card>
        </section>
      </main>

      <footer className="container mx-auto px-4 py-8 text-center text-sm text-muted-foreground">
        <p>&copy; 2026 AkarAI. All rights reserved.</p>
      </footer>
    </div>
  );
}