import { create } from "zustand";
import type { DistributionPlan, SortOrder } from "@/types";

interface DistributorSession {
  selectedVoucherIds: string[];
  sortOrder: SortOrder;
  plan: DistributionPlan | null;
}

interface AppState {
  sidebarCollapsed: boolean;
  distributorSession: DistributorSession;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setSelectedVoucherIds: (ids: string[]) => void;
  setSortOrder: (order: SortOrder) => void;
  setDistributionPlan: (plan: DistributionPlan | null) => void;
  resetDistributorSession: () => void;
}

const initialSession = (): DistributorSession => ({
  selectedVoucherIds: [],
  sortOrder: "ascending",
  plan: null,
});

export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  distributorSession: initialSession(),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
  setSelectedVoucherIds: (ids) =>
    set((s) => ({
      distributorSession: { ...s.distributorSession, selectedVoucherIds: ids, plan: null },
    })),
  setSortOrder: (order) =>
    set((s) => ({
      distributorSession: { ...s.distributorSession, sortOrder: order, plan: null },
    })),
  setDistributionPlan: (plan) =>
    set((s) => ({
      distributorSession: { ...s.distributorSession, plan },
    })),
  resetDistributorSession: () => set({ distributorSession: initialSession() }),
}));
