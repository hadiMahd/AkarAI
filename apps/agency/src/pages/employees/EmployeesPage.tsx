import { EmployeeInviteForm } from "@/features/employees/EmployeeInviteForm";
import { EmployeeTable } from "@/features/employees/EmployeeTable";

export function EmployeesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Employees</h2>
        <p className="text-muted-foreground">Manage your agency support employees</p>
      </div>
      <EmployeeInviteForm />
      <EmployeeTable />
    </div>
  );
}
