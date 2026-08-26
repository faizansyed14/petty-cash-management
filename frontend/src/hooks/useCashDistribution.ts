import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/services/api";
import type {
  DistributionCalculateRequest,
  DistributionConfirmRequest,
  DistributionConfirmResult,
  DistributionPlan,
} from "@/types";

export function useCalculateDistribution() {
  return useMutation({
    mutationFn: async (payload: DistributionCalculateRequest) => {
      const { data } = await api.post<DistributionPlan>("/api/cash-distribution/calculate", payload);
      return data;
    },
  });
}

export function useConfirmDistribution() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: DistributionConfirmRequest) => {
      const { data } = await api.post<DistributionConfirmResult>(
        "/api/cash-distribution/confirm",
        payload,
      );
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["vouchers"] });
    },
  });
}
