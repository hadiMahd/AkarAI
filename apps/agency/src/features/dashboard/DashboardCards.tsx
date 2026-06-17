import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Building2, MessageSquare, CheckCircle2, Calendar, AlertCircle, TrendingUp, Users } from "lucide-react";
import { useDashboardSummary } from "./useDashboardSummary";
import { getApiErrorMessage } from "@/lib/api/errors";

export function DashboardCards() {
  const { data, isLoading, error } = useDashboardSummary();

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-24 bg-muted animate-pulse rounded" />
              <div className="h-4 w-4 bg-muted animate-pulse rounded" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-16 bg-muted animate-pulse rounded" />
              <div className="h-3 w-20 bg-muted animate-pulse rounded mt-2" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
          <AlertCircle className="h-4 w-4 text-destructive" />
          <CardTitle className="text-sm font-medium">Dashboard unavailable</CardTitle>
        </CardHeader>
        <CardContent>
          <p role="alert" className="text-sm text-muted-foreground">
            {getApiErrorMessage(error, "dashboard.summary")}
          </p>
        </CardContent>
      </Card>
    );
  }

  const cards = [
    {
      title: "Total Listings",
      value: data?.listings_total ?? 0,
      description: "Active listings",
      icon: Building2,
    },
    {
      title: "Active Leads",
      value: data?.active_leads_total ?? 0,
      description: "Non-reviewed leads",
      icon: MessageSquare,
    },
    {
      title: "Reviewed Leads",
      value: data?.reviewed_leads_total ?? 0,
      description: "Processed leads",
      icon: CheckCircle2,
    },
    {
      title: "Scheduled Viewings",
      value: data?.scheduled_viewings_total ?? 0,
      description: "Upcoming viewings",
      icon: Calendar,
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <Card key={card.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
            <card.icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{card.value}</div>
            <p className="text-xs text-muted-foreground">{card.description}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}


import { useLeadProcessingTrends } from "./useDashboardSummary";

export function LeadProcessingTrendsCards() {
  const { data, isLoading, error } = useLeadProcessingTrends();

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mt-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-24 bg-muted animate-pulse rounded" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-16 bg-muted animate-pulse rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error || !data) return null;

  const percent = (v: number) => `${(v * 100).toFixed(1)}%`;
  const summary = data.summary ?? {
    total_leads: 0,
    spam_count: 0,
    not_spam_count: 0,
    hot_count: 0,
    normal_count: 0,
    pending_count: 0,
    reviewed_count: 0,
  };

  return (
    <div className="space-y-4 mt-6">
      <h3 className="text-lg font-semibold">Lead Processing Trends</h3>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Spam Rate</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{percent(data.spam_rate)}</div>
            <p className="text-xs text-muted-foreground">
              {summary.spam_count} spam / {summary.total_leads} leads
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Hot Lead Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{percent(data.hot_rate)}</div>
            <p className="text-xs text-muted-foreground">
              {summary.hot_count} hot / {summary.not_spam_count} non-spam
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Review Rate</CardTitle>
            <Users className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{percent(data.review_rate)}</div>
            <p className="text-xs text-muted-foreground">
              {summary.reviewed_count} reviewed / {summary.total_leads} leads
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Fallbacks</CardTitle>
            <AlertCircle className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.fallback_count}</div>
            <p className="text-xs text-muted-foreground">
              Classification fallback events
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
