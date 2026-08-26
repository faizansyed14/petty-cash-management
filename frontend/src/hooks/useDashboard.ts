import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";
import type { DashboardCharts, DashboardSummary } from "@/types";

export function useDashboardSummary() {
  return useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: async () => {
      const { data } = await api.get<DashboardSummary>("/api/dashboard/summary");
      return data;
    },
  });
}

export function useDashboardCharts() {
  return useQuery({
    queryKey: ["dashboard-charts"],
    queryFn: async () => {
      const { data } = await api.get<DashboardCharts>("/api/dashboard/charts");
      return data;
    },
  });
}
