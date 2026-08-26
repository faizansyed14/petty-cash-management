import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Download, Pencil } from "lucide-react";
import { toast } from "sonner";
import {
  DistributionResultTable,
  exportPlanCsv,
} from "@/components/distributor/DistributionResultTable";
import { DenominationGrid } from "@/components/distributor/DenominationGrid";
import { VoucherTable } from "@/components/vouchers/VoucherTable";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useCalculateDistribution, useConfirmDistribution } from "@/hooks/useCashDistribution";
import { usePhysicalCash } from "@/hooks/usePhysicalCash";
import { useVouchers } from "@/hooks/useVouchers";
import { formatMoney, toNumber } from "@/lib/utils";
import { getErrorMessage } from "@/services/api";
import { useAppStore } from "@/store/useAppStore";
import type { DenominationMap } from "@/types";

const noop = (_next: DenominationMap) => {};

export function CashDistributor() {
  const session = useAppStore((s) => s.distributorSession);
  const setSelected = useAppStore((s) => s.setSelectedVoucherIds);
  const setPlan = useAppStore((s) => s.setDistributionPlan);
  const reset = useAppStore((s) => s.resetDistributorSession);

  const physicalCash = usePhysicalCash();
  const unpaid = useVouchers({ status: "PENDING_PAYMENT" });
  const calculate = useCalculateDistribution();
  const confirm = useConfirmDistribution();
  const [confirmOpen, setConfirmOpen] = useState(false);

  const inventory = physicalCash.data?.denominations ?? {};

  const selectedVouchers = useMemo(
    () => (unpaid.data?.items ?? []).filter((v) => session.selectedVoucherIds.includes(v.id)),
    [unpaid.data, session.selectedVoucherIds],
  );

  const toggle = (id: string) => {
    setSelected(
      session.selectedVoucherIds.includes(id)
        ? session.selectedVoucherIds.filter((x) => x !== id)
        : [...session.selectedVoucherIds, id],
    );
  };

  const selectAll = () => setSelected((unpaid.data?.items ?? []).map((v) => v.id));
  const deselectAll = () => setSelected([]);

  const runCalculate = async () => {
    if (!selectedVouchers.length) {
      toast.error("Select vouchers to pay");
      return;
    }
    try {
      const plan = await calculate.mutateAsync({
        inventory,
        sort_order: "ascending",
        payouts: selectedVouchers.map((v) => ({
          voucher_id: v.id,
          employee_id: v.employee.id,
          amount_due: v.total_amount,
          employee_name: v.employee.name,
          voucher_no: v.voucher_no,
        })),
      });
      setPlan(plan);
      toast.success("Ready — check notes per person below");
    } catch (err) {
      toast.error(getErrorMessage(err, "Calculate failed"));
    }
  };

  const runConfirm = async () => {
    if (!session.plan) return;
    try {
      await confirm.mutateAsync({
        inventory,
        plan: session.plan,
      });
      await physicalCash.refetch();
      toast.success("Marked as paid — physical cash updated");
      setConfirmOpen(false);
      reset();
    } catch (err) {
      toast.error(getErrorMessage(err, "Confirm failed"));
    }
  };

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted-foreground">
        Select vouchers → calculate → hand out the notes shown → confirm. Cash counts come from the
        Physical Cash page.
      </p>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Cash in your drawer</CardTitle>
            <Button variant="outline" size="sm" asChild>
              <Link to="/physical-cash">
                <Pencil className="h-3.5 w-3.5" /> Edit counts
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            {physicalCash.isLoading ? (
              <p className="text-sm text-muted-foreground">Loading…</p>
            ) : (
              <DenominationGrid value={inventory} onChange={noop} readOnly />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">
              Unpaid vouchers
              {session.selectedVoucherIds.length ? (
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  {session.selectedVoucherIds.length} selected
                </span>
              ) : null}
            </CardTitle>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={!unpaid.data?.items?.length}
                onClick={selectAll}
              >
                Select all
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={!session.selectedVoucherIds.length}
                onClick={deselectAll}
              >
                Deselect all
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <VoucherTable
              vouchers={unpaid.data?.items ?? []}
              loading={unpaid.isLoading}
              emptyMessage="No unpaid vouchers — upload some first"
              selectable
              selectedIds={session.selectedVoucherIds}
              onToggle={toggle}
              onToggleAll={setSelected}
              showActions={false}
            />
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button onClick={runCalculate} disabled={calculate.isPending}>
          {calculate.isPending ? "Working…" : "Calculate notes to give"}
        </Button>
        <Button
          variant="outline"
          disabled={!session.plan}
          onClick={() => session.plan && exportPlanCsv(session.plan)}
        >
          <Download className="h-4 w-4" /> CSV
        </Button>
        <Button
          disabled={!session.plan}
          onClick={() => setConfirmOpen(true)}
          className="bg-orange-500 text-white hover:bg-orange-600"
        >
          Confirm paid
        </Button>
      </div>

      {session.plan ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">What to hand each person</CardTitle>
          </CardHeader>
          <CardContent>
            <DistributionResultTable plan={session.plan} />
          </CardContent>
        </Card>
      ) : null}

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Mark as paid?</DialogTitle>
            <DialogDescription>
              Confirms you handed out the cash. Selected vouchers will be marked paid and the Physical
              Cash page will be updated automatically.
            </DialogDescription>
          </DialogHeader>
          {session.plan ? (
            <p className="text-sm">
              Total: {formatMoney(session.plan.total_distributed)}
              {toNumber(session.plan.total_shortfall) > 0
                ? ` · Shortfall ${formatMoney(session.plan.total_shortfall)}`
                : ""}
            </p>
          ) : null}
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmOpen(false)}>
              Cancel
            </Button>
            <Button onClick={runConfirm} disabled={confirm.isPending}>
              {confirm.isPending ? "Saving…" : "Yes, paid"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
