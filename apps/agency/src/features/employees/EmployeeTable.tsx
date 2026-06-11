import { useEmployees, type Employee } from "./useEmployees";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, Trash2 } from "lucide-react";

export function EmployeeTable() {
  const { employees, isLoading, deactivateEmployee, isDeactivating } = useEmployees();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Loading employees...</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-16 bg-muted animate-pulse rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (employees.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Employee Directory
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">No employees found. Add your first support employee above.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="h-5 w-5" />
          Employee Directory
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-3 px-2 font-medium">Name</th>
                <th className="text-left py-3 px-2 font-medium">Email</th>
                <th className="text-left py-3 px-2 font-medium">Status</th>
                <th className="text-left py-3 px-2 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {employees.map((employee: Employee) => (
                <tr key={employee.id} className="border-b">
                  <td className="py-3 px-2">{employee.display_name || "—"}</td>
                  <td className="py-3 px-2">{employee.work_email || "—"}</td>
                  <td className="py-3 px-2">
                    <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs ${
                      employee.status === "active"
                        ? "bg-green-100 text-green-700"
                        : "bg-gray-100 text-gray-700"
                    }`}>
                      {employee.status}
                    </span>
                  </td>
                  <td className="py-3 px-2">
                    {employee.status === "active" && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deactivateEmployee(employee.id)}
                        disabled={isDeactivating}
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
