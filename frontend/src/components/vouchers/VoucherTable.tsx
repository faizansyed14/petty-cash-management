import { useState } from "react";
import { format } from "date-fns";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useDeleteVoucher } from "@/hooks/useVouchers";
import { formatMoney } from "@/lib/utils";
import { getErrorMessage } from "@/services/api";
import type { Voucher, VoucherStatus } from "@/types";

const statusVariant: Record<
  VoucherStatus,
  "default" | "secondary" | "success" | "warning" | "outline"
> = {
  EXTRACTED: "outline",
  VERIFIED: "secondary",
  PENDING_PAYMENT: "warning",
  PAID: "success",
  RECONCILED: "default",
};

interface Props {
  vouchers: Voucher[];
  loading?: boolean;
  emptyMessage?: string;
  selectable?: boolean;
  selectedIds?: string[];
  onToggle?: (id: string) => void;
  onToggleAll?: (ids: string[]) => void;
  showActions?: boolean;
}

export function VoucherTable({
  vouchers,
  loading,
  emptyMessage = "No vouchers found",
  selectable,
  selectedIds = [],
  onToggle,
  onToggleAll,
  showActions = true,
}: Props) {
  const deleteMutation = useDeleteVoucher();
  const [pendingDelete, setPendingDelete] = useState<Voucher | null>(null);

  if (loading) {
    return (
      <div className="space-y-2 p-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    );
  }

  if (!vouchers.length) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
        {emptyMessage}
      </div>
    );
  }

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            {selectable ? (
              <TableHead className="w-10">
                <input
                  type="checkbox"
                  checked={vouchers.length > 0 && selectedIds.length === vouchers.length}
                  onChange={() =>
                    onToggleAll?.(
                      selectedIds.length === vouchers.length ? [] : vouchers.map((v) => v.id),
                    )
                  }
                  className="h-4 w-4 accent-primary"
                  title="Select all"
                />
              </TableHead>
            ) : null}
            <TableHead>Voucher</TableHead>
            <TableHead>Date</TableHead>
            <TableHead>Employee</TableHead>
            <TableHead>Department</TableHead>
            <TableHead>Amount</TableHead>
            <TableHead>Status</TableHead>
            {showActions && !selectable ? <TableHead className="text-right">Actions</TableHead> : null}
          </TableRow>
        </TableHeader>
        <TableBody>
          {vouchers.map((v) => (
            <TableRow key={v.id} data-state={selectedIds.includes(v.id) ? "selected" : undefined}>
              {selectable ? (
                <TableCell>
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(v.id)}
                    onChange={() => onToggle?.(v.id)}
                    className="h-4 w-4 accent-primary"
                  />
                </TableCell>
              ) : null}
              <TableCell className="font-medium">{v.voucher_no}</TableCell>
              <TableCell>
                {v.voucher_date ? format(new Date(v.voucher_date), "dd MMM yyyy") : "—"}
              </TableCell>
              <TableCell>
                <div className="font-medium">{v.employee.name}</div>
                <div className="text-xs text-muted-foreground">{v.employee.employee_code}</div>
              </TableCell>
              <TableCell>{v.department_label}</TableCell>
              <TableCell className="font-medium">{formatMoney(v.total_amount, v.currency)}</TableCell>
              <TableCell>
                <Badge variant={statusVariant[v.status]}>{v.status.replaceAll("_", " ")}</Badge>
              </TableCell>
              {showActions && !selectable ? (
                <TableCell className="text-right">
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    className="text-destructive hover:text-destructive"
                    disabled={v.status === "RECONCILED"}
                    onClick={() => setPendingDelete(v)}
                    title={
                      v.status === "RECONCILED"
                        ? "Reconciled vouchers cannot be deleted"
                        : "Delete voucher"
                    }
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </TableCell>
              ) : null}
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Dialog open={!!pendingDelete} onOpenChange={(open) => !open && setPendingDelete(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete voucher?</DialogTitle>
            <DialogDescription>Permanently remove {pendingDelete?.voucher_no}.</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setPendingDelete(null)}>
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={deleteMutation.isPending}
              onClick={async () => {
                if (!pendingDelete) return;
                try {
                  await deleteMutation.mutateAsync(pendingDelete.id);
                  toast.success(`Deleted ${pendingDelete.voucher_no}`);
                  setPendingDelete(null);
                } catch (err) {
                  toast.error(getErrorMessage(err, "Delete failed"));
                }
              }}
            >
              {deleteMutation.isPending ? "Deleting…" : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
