import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/query-client";

interface Employee {
  id: string;
  agency_tenant_id: string;
  user_id: string;
  role_id: string;
  status: string;
  display_name: string | null;
  work_email: string | null;
  created_at: string;
  updated_at: string;
}

interface EmployeeCreateRequest {
  work_email: string;
  display_name: string;
  role_slug: string;
}

interface PaginatedEmployeesResponse {
  items: Employee[];
  page: number;
  page_size: number;
  total: number;
  has_next: boolean;
  has_previous: boolean;
}

async function fetchEmployees(page = 1, pageSize = 20): Promise<PaginatedEmployeesResponse> {
  return apiClient<PaginatedEmployeesResponse>("/agencies/me/employees", {
    params: { page, page_size: pageSize },
  });
}

async function createEmployee(data: EmployeeCreateRequest): Promise<Employee> {
  return apiClient<Employee>("/agencies/me/employees", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

async function deactivateEmployee(employeeId: string): Promise<void> {
  return apiClient<void>(`/agencies/me/employees/${employeeId}`, {
    method: "DELETE",
  });
}

export function useEmployees() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: queryKeys.employees.all,
    queryFn: () => fetchEmployees(),
  });

  const createMutation = useMutation({
    mutationFn: createEmployee,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.employees.all });
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: deactivateEmployee,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.employees.all });
    },
  });

  return {
    employees: query.data?.items ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    error: query.error,
    createEmployee: createMutation.mutateAsync,
    isCreating: createMutation.isPending,
    createError: createMutation.error,
    deactivateEmployee: deactivateMutation.mutateAsync,
    isDeactivating: deactivateMutation.isPending,
  };
}

export type { Employee, EmployeeCreateRequest };
