import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatMoney, toNumber } from "@/lib/utils";
import type { DistributionPlan } from "@/types";

interface Props {
  plan: DistributionPlan;
}

/** Flatten nested coins if present; show only counts > 0. */
export function formatBreakdown(breakdown: Record<string, unknown> | null | undefined): string {
  if (!breakdown) return "—";
  const flat: Record<string, number> = {};
  for (const [key, value] of Object.entries(breakdown)) {
    if (key === "coins" && value && typeof value === "object") {
      for (const [ck, cv] of Object.entries(value as Record<string, unknown>)) {
        flat[ck] = toNumber(cv as string | number);
      }
    } else {
      flat[key] = toNumber(value as string | number);
    }
  }
  const parts = Object.entries(flat)
    .filter(([, c]) => c > 0)
    .sort((a, b) => Number(b[0]) - Number(a[0]))
    .map(([d, c]) => `${c}×${d}`);
  return parts.join(", ") || "—";
}

export function DistributionResultTable({ plan }: Props) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3 text-sm">
        <Badge variant="secondary">Given out {formatMoney(plan.total_distributed)}</Badge>
        <Badge variant={toNumber(plan.total_shortfall) > 0 ? "warning" : "success"}>
          Shortfall {formatMoney(plan.total_shortfall)}
        </Badge>
        <span className="text-muted-foreground">
          Cash left {formatMoney(plan.remaining_total)}
        </span>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Voucher</TableHead>
            <TableHead>Employee</TableHead>
            <TableHead>Due</TableHead>
            <TableHead>Give</TableHead>
            <TableHead>Short</TableHead>
            <TableHead>Notes to hand</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {plan.lines.map((line) => (
            <TableRow key={line.voucher_id}>
              <TableCell className="font-medium">{line.voucher_no || "—"}</TableCell>
              <TableCell>{line.employee_name || "—"}</TableCell>
              <TableCell>{formatMoney(line.amount_due)}</TableCell>
              <TableCell>{formatMoney(line.amount_given)}</TableCell>
              <TableCell>
                {toNumber(line.shortfall) > 0 ? (
                  <Badge variant="warning">{formatMoney(line.shortfall)}</Badge>
                ) : (
                  formatMoney(0)
                )}
              </TableCell>
              <TableCell className="text-sm font-medium text-slate-700">
                {formatBreakdown(line.breakdown as Record<string, unknown>)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

export function exportPlanCsv(plan: DistributionPlan) {
  const headers = ["voucher_no", "employee_name", "amount_due", "amount_given", "shortfall", "breakdown"];
  const rows = plan.lines.map((l) => [
    l.voucher_no,
    l.employee_name,
    String(l.amount_due),
    String(l.amount_given),
    String(l.shortfall),
    formatBreakdown(l.breakdown as Record<string, unknown>),
  ]);
  const csv = [headers, ...rows]
    .map((r) => r.map((c) => `"${String(c).replaceAll('"', '""')}"`).join(","))
    .join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `cash-distribution-${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
