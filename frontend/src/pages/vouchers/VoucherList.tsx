import { useState } from "react";
import { Link } from "react-router-dom";
import { Download, Plus } from "lucide-react";
import { toast } from "sonner";
import { VoucherRegisterTable } from "@/components/vouchers/VoucherRegisterTable";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { downloadVoucherExcel, useVouchers } from "@/hooks/useVouchers";
import { getErrorMessage } from "@/services/api";
import type { VoucherStatus } from "@/types";

const statuses: Array<VoucherStatus | "ALL"> = ["ALL", "PENDING_PAYMENT", "PAID"];

export function VoucherList() {
  const [status, setStatus] = useState<VoucherStatus | "ALL">("ALL");
  const [search, setSearch] = useState("");
  const [exporting, setExporting] = useState(false);

  const filters = {
    status: status === "ALL" ? "" : status,
    search: search || undefined,
  };
  const query = useVouchers(filters);

  const onExport = async () => {
    setExporting(true);
    try {
      await downloadVoucherExcel(filters);
      toast.success("Excel downloaded");
    } catch (err) {
      toast.error(getErrorMessage(err, "Export failed"));
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">Vouchers</h2>
          <p className="text-sm text-muted-foreground">
            {query.data?.total ?? 0} vouchers · set deposited / cash collection · export Excel
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" onClick={onExport} disabled={exporting}>
            <Download className="h-4 w-4" />
            {exporting ? "Exporting…" : "Export Excel"}
          </Button>
          <Button asChild>
            <Link to="/vouchers/upload">
              <Plus className="h-4 w-4" /> Upload
            </Link>
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle className="text-base">Register</CardTitle>
          <div className="flex flex-wrap gap-2">
            <Input
              placeholder="Search…"
              className="w-[200px]"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <Select value={status} onValueChange={(v) => setStatus(v as VoucherStatus | "ALL")}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                {statuses.map((s) => (
                  <SelectItem key={s} value={s}>
                    {s === "ALL" ? "All" : s === "PENDING_PAYMENT" ? "Unpaid" : s === "PAID" ? "Paid" : s}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {query.isError ? (
            <div className="p-6 text-sm text-destructive">Failed to load</div>
          ) : (
            <VoucherRegisterTable vouchers={query.data?.items ?? []} loading={query.isLoading} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
