import { useMemo, useState } from "react";
import { Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useDeleteVoucher, useUpdateVoucher } from "@/hooks/useVouchers";
import { formatMoney, parseDisplayDate, toDisplayDate } from "@/lib/utils";
import { getErrorMessage } from "@/services/api";
import { UAE_BANKS, type SettlementType, type Voucher } from "@/types";

interface Props {
  vouchers: Voucher[];
  loading?: boolean;
}

export function VoucherRegisterTable({ vouchers, loading }: Props) {
  const update = useUpdateVoucher();
  const del = useDeleteVoucher();
  const [pendingDelete, setPendingDelete] = useState<Voucher | null>(null);
  const [dateOrder, setDateOrder] = useState<"desc" | "asc">("desc");

  const sorted = useMemo(() => {
    const rows = [...vouchers];
    rows.sort((a, b) => {
      const da = a.settlement_date?.slice(0, 10) || "";
      const db = b.settlement_date?.slice(0, 10) || "";
      if (!da && !db) return 0;
      if (!da) return 1;
      if (!db) return -1;
      return dateOrder === "desc" ? db.localeCompare(da) : da.localeCompare(db);
    });
    return rows;
  }, [vouchers, dateOrder]);

  const save = async (id: string, payload: Parameters<typeof update.mutateAsync>[0]["payload"]) => {
    try {
      await update.mutateAsync({ id, payload });
      toast.success("Saved");
    } catch (err) {
      toast.error(getErrorMessage(err, "Update failed"));
    }
  };

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
        No vouchers yet — upload a PDF
      </div>
    );
  }

  return (
    <>
      <div className="overflow-x-auto">
        <div className="border-b border-dashed border-slate-300 bg-white px-4 py-3 text-center">
          <h3 className="text-lg font-bold tracking-wide text-green-700">ALPHA DATA RECRUITMENT</h3>
        </div>
        <Table>
          <TableHeader>
            <TableRow className="border-dashed">
              <TableHead className="h-9 px-3 py-2 font-bold uppercase">S.No:</TableHead>
              <TableHead className="h-9 px-3 py-2 font-bold uppercase">Voucher No:</TableHead>
              <TableHead className="h-9 px-3 py-2 font-bold uppercase">Name</TableHead>
              <TableHead className="h-9 px-3 py-2 font-bold uppercase">Amount</TableHead>
              <TableHead className="h-9 min-w-[180px] px-3 py-2 font-bold uppercase">Notes</TableHead>
              <TableHead className="h-9 min-w-[320px] px-3 py-2 font-bold uppercase">Deposited</TableHead>
              <TableHead className="h-9 px-3 py-2 font-bold uppercase">Cash Collection</TableHead>
              <TableHead className="h-9 px-3 py-2 font-bold uppercase">
                <button
                  type="button"
                  className="inline-flex items-center gap-1 uppercase"
                  onClick={() => setDateOrder((o) => (o === "desc" ? "asc" : "desc"))}
                  title={dateOrder === "desc" ? "Latest first — click for oldest" : "Oldest first — click for latest"}
                >
                  Date {dateOrder === "desc" ? "↓" : "↑"}
                </button>
              </TableHead>
              <TableHead className="h-9 min-w-[120px] px-3 py-2 font-bold uppercase">File Number</TableHead>
              <TableHead className="h-9 px-3 py-2 font-bold uppercase">Status</TableHead>
              <TableHead className="h-9 px-3 py-2 text-right font-bold uppercase">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sorted.map((v, idx) => {
              const settlementValue =
                v.settlement_type === "DEPOSITED"
                  ? "DEPOSITED"
                  : v.settlement_type === "CASH_COLLECTION"
                    ? "CASH_COLLECTION"
                    : "NONE";

              const noteText = v.details || "—";

              return (
                <TableRow key={v.id} className="whitespace-nowrap">
                  <TableCell className="px-3 py-1.5 text-center">{idx + 1}</TableCell>
                  <TableCell className="px-3 py-1.5 font-medium">{v.voucher_no}</TableCell>
                  <TableCell className="px-3 py-1.5">{v.employee.name}</TableCell>
                  <TableCell className="px-3 py-1.5 font-medium">
                    {formatMoney(v.total_amount, v.currency)}
                  </TableCell>
                  <TableCell className="max-w-[240px] px-3 py-1.5">
                    <span className="block truncate text-sm" title={noteText}>
                      {noteText}
                    </span>
                  </TableCell>
                  <TableCell className="px-3 py-1.5">
                    <div className="flex items-center gap-1.5">
                      <Select
                        value={settlementValue}
                        onValueChange={(val) => {
                          if (val === "NONE") {
                            void save(v.id, { clear_settlement: true });
                            return;
                          }
                          if (val === "CASH_COLLECTION") {
                            void save(v.id, {
                              settlement_type: "CASH_COLLECTION",
                              bank_name: null,
                              settlement_date: v.settlement_date || new Date().toISOString().slice(0, 10),
                            });
                            return;
                          }
                          void save(v.id, {
                            settlement_type: "DEPOSITED" as SettlementType,
                            bank_name: v.bank_name || UAE_BANKS[0],
                            settlement_date: v.settlement_date || new Date().toISOString().slice(0, 10),
                          });
                        }}
                      >
                        <SelectTrigger className="h-8 w-[150px] shrink-0">
                          <SelectValue placeholder="Type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="NONE">—</SelectItem>
                          <SelectItem value="DEPOSITED">Deposited</SelectItem>
                          <SelectItem value="CASH_COLLECTION">Cash collection</SelectItem>
                        </SelectContent>
                      </Select>
                      {v.settlement_type === "DEPOSITED" ? (
                        <Select
                          value={v.bank_name || UAE_BANKS[0]}
                          onValueChange={(bank) =>
                            void save(v.id, {
                              settlement_type: "DEPOSITED",
                              bank_name: bank,
                              settlement_date: v.settlement_date || new Date().toISOString().slice(0, 10),
                            })
                          }
                        >
                          <SelectTrigger className="h-8 w-[170px] shrink-0">
                            <SelectValue placeholder="UAE bank" />
                          </SelectTrigger>
                          <SelectContent>
                            {UAE_BANKS.map((b) => (
                              <SelectItem key={b} value={b}>
                                {b}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      ) : null}
                    </div>
                  </TableCell>
                  <TableCell className="px-3 py-1.5">
                    {v.settlement_type === "CASH_COLLECTION" ? (
                      <span className="text-sm font-medium">Cash Collection</span>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell className="px-3 py-1.5">
                    <Input
                      className="h-8 w-[120px]"
                      placeholder="dd/mm/yyyy"
                      disabled={!v.settlement_type}
                      defaultValue={toDisplayDate(v.settlement_date)}
                      key={`${v.id}-date-${v.settlement_date ?? ""}`}
                      onBlur={(e) => {
                        if (!v.settlement_type) return;
                        const parsed = parseDisplayDate(e.target.value);
                        if (parsed === undefined) {
                          toast.error("Use date as dd/mm/yyyy");
                          e.target.value = toDisplayDate(v.settlement_date);
                          return;
                        }
                        const current = v.settlement_date ? v.settlement_date.slice(0, 10) : null;
                        if (parsed !== current) {
                          void save(v.id, {
                            settlement_type: v.settlement_type,
                            bank_name: v.bank_name,
                            settlement_date: parsed,
                          });
                        }
                      }}
                    />
                  </TableCell>
                  <TableCell className="px-3 py-1.5">
                    <Input
                      className="h-8 w-[130px]"
                      inputMode="text"
                      placeholder="e.g. 12/34-5"
                      defaultValue={v.file_number ?? ""}
                      key={`${v.id}-file-${v.file_number ?? ""}`}
                      onChange={(e) => {
                        const cleaned = e.target.value.replace(/[^0-9/\-]/g, "");
                        if (cleaned !== e.target.value) e.target.value = cleaned;
                      }}
                      onBlur={(e) => {
                        const next = e.target.value.trim() || null;
                        if (next !== (v.file_number ?? null)) {
                          void save(v.id, { file_number: next });
                        }
                      }}
                    />
                  </TableCell>
                  <TableCell className="px-3 py-1.5">
                    <Select
                      value={v.status === "PAID" ? "PAID" : "PENDING_PAYMENT"}
                      onValueChange={(val) => void save(v.id, { status: val as "PAID" | "PENDING_PAYMENT" })}
                    >
                      <SelectTrigger
                        className={cn(
                          "h-8 w-[110px] font-medium",
                          v.status === "PAID"
                            ? "border-emerald-300 text-emerald-700"
                            : "border-amber-300 text-amber-700",
                        )}
                      >
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="PENDING_PAYMENT">Unpaid</SelectItem>
                        <SelectItem value="PAID">Paid</SelectItem>
                      </SelectContent>
                    </Select>
                  </TableCell>
                  <TableCell className="px-3 py-1.5 text-right">
                    <Button
                      type="button"
                      size="icon"
                      variant="outline"
                      title="Delete voucher"
                      className="h-8 w-8 border-destructive/30 text-destructive hover:bg-destructive/10 hover:text-destructive"
                      onClick={() => setPendingDelete(v)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      <Dialog open={!!pendingDelete} onOpenChange={(open) => !open && setPendingDelete(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete voucher?</DialogTitle>
            <DialogDescription>Permanently remove {pendingDelete?.voucher_no}.</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPendingDelete(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={del.isPending}
              onClick={async () => {
                if (!pendingDelete) return;
                try {
                  await del.mutateAsync(pendingDelete.id);
                  toast.success("Deleted");
                  setPendingDelete(null);
                } catch (err) {
                  toast.error(getErrorMessage(err, "Delete failed"));
                }
              }}
            >
              {del.isPending ? "Deleting…" : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
