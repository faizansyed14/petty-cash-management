import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "@/routes/ProtectedRoute";
import { AppShell } from "@/layouts/AppShell";
import { Login } from "@/pages/auth/Login";
import { UploadVoucher } from "@/pages/vouchers/UploadVoucher";
import { VoucherList } from "@/pages/vouchers/VoucherList";
import { CashDistributor } from "@/pages/distributor/CashDistributor";
import { PhysicalCashPage } from "@/pages/cash/PhysicalCash";
import { Dashboard } from "@/pages/dashboard/Dashboard";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="physical-cash" element={<PhysicalCashPage />} />
          <Route path="vouchers" element={<VoucherList />} />
          <Route path="vouchers/upload" element={<UploadVoucher />} />
          <Route path="distributor" element={<CashDistributor />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
