import { DashboardCards } from "@/features/dashboard/DashboardCards";
import { TransactionsForecastChart } from "@/features/dashboard/TransactionsForecastChart";
import { useTenantSession } from "@/features/auth/useTenantSession";
import { isAgencyAdmin } from "@/lib/session/tenant-session";

export function DashboardPage() {
  const { session: tenantSession } = useTenantSession();
  const showForecast = isAgencyAdmin(tenantSession);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Dashboard</h2>
        <p className="text-muted-foreground">Overview of your agency operations</p>
      </div>
      <DashboardCards />
      {showForecast ? <TransactionsForecastChart /> : null}
    </div>
  );
}
