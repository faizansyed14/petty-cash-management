import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/services/api";
import type { DenominationMap, PhysicalCash } from "@/types";

export function usePhysicalCash() {
  return useQuery({
    queryKey: ["physical-cash"],
    queryFn: async () => {
      const { data } = await api.get<PhysicalCash>("/api/physical-cash");
      return data;
    },
  });
}

export function useReplacePhysicalCash() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (denominations: DenominationMap) => {
      const { data } = await api.put<PhysicalCash>("/api/physical-cash", { denominations });
      return data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["physical-cash"], data);
      void queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
    },
  });
}

export function useUpdatePhysicalCashDenom() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ denom, count }: { denom: string; count: number }) => {
      const { data } = await api.patch<PhysicalCash>(`/api/physical-cash/${denom}`, { count });
      return data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["physical-cash"], data);
      void queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
    },
  });
}

export function useClearPhysicalCashDenom() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (denom: string) => {
      const { data } = await api.delete<PhysicalCash>(`/api/physical-cash/${denom}`);
      return data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["physical-cash"], data);
      void queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
    },
  });
}
