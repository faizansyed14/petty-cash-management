import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/services/api";
import type {
  Voucher,
  VoucherCreate,
  VoucherDraft,
  VoucherListResponse,
  VoucherStatus,
  VoucherUpdate,
} from "@/types";

export interface VoucherFilters {
  month?: number;
  year?: number;
  status?: VoucherStatus | "" | string;
  search?: string;
}

export function useVouchers(filters: VoucherFilters = {}) {
  return useQuery({
    queryKey: ["vouchers", filters],
    queryFn: async () => {
      const { data } = await api.get<VoucherListResponse>("/api/vouchers", {
        params: {
          month: filters.month || undefined,
          year: filters.year || undefined,
          status: filters.status || undefined,
          search: filters.search || undefined,
        },
      });
      return data;
    },
  });
}

export interface VoucherExtractResponse {
  items: VoucherDraft[];
  count: number;
}

export function useExtractVoucher() {
  return useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      const { data } = await api.post<VoucherExtractResponse>("/api/vouchers/extract", form);
      return data.items?.length ? data.items : [];
    },
  });
}

export function useCreateVoucher() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: VoucherCreate) => {
      const { data } = await api.post<Voucher>("/api/vouchers", payload);
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["vouchers"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard-charts"] });
    },
  });
}

export function useUpdateVoucher() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: VoucherUpdate }) => {
      const { data } = await api.patch<Voucher>(`/api/vouchers/${id}`, payload);
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["vouchers"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard-charts"] });
      void queryClient.invalidateQueries({ queryKey: ["physical-cash"] });
    },
  });
}

export function useDeleteVoucher() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/vouchers/${id}`);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["vouchers"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard-charts"] });
    },
  });
}

export async function downloadVoucherExcel() {
  const token = localStorage.getItem("pc_token");
  const base = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const res = await fetch(`${base}/api/vouchers/export/excel`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Export failed");
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "ALPHA_DATA_RECRUITMENT_vouchers.xlsx";
  a.click();
  URL.revokeObjectURL(url);
}
