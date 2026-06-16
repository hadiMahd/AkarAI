import { useState, type FormEvent } from "react";
import { useEmployees } from "./useEmployees";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle2, UserPlus } from "lucide-react";
import { getApiErrorMessage } from "@/lib/api/errors";

export function EmployeeInviteForm() {
  const { createEmployee, isCreating, createError } = useEmployees();
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSuccessMessage("");
    try {
      await createEmployee({
        work_email: email,
        display_name: displayName,
        role_slug: "support_employee",
      });
      setSuccessMessage(`Successfully created ${displayName}. Temporary password: 12345678`);
      setEmail("");
      setDisplayName("");
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch {
      // Error is handled by the mutation
    }
  };

  const errorMessage = createError ? getApiErrorMessage(createError, "employee.create") : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <UserPlus className="h-5 w-5" />
          Add Support Employee
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <p className="text-sm text-muted-foreground">
            This creates a dedicated employee account. Temporary password: 12345678
          </p>
          {successMessage && (
            <div className="flex items-center gap-2 p-3 rounded-md bg-green-50 text-green-700 text-sm">
              <CheckCircle2 className="h-4 w-4" />
              <span>{successMessage}</span>
            </div>
          )}
          {createError && (
            <div role="alert" className="flex items-center gap-2 p-3 rounded-md bg-destructive/10 text-destructive text-sm">
              <AlertCircle className="h-4 w-4" />
              <span>{errorMessage}</span>
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="email">Work Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="user@akarai.test"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="displayName">Display Name</Label>
            <Input
              id="displayName"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              required
            />
          </div>
          <Button type="submit" disabled={isCreating}>
            {isCreating ? "Adding..." : "Add Employee"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
