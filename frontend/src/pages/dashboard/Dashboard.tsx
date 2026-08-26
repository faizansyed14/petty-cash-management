import { Banknote, HandCoins, ListChecks, Wallet } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useDashboardCharts, useDashboardSummary } from "@/hooks/useDashboard";
import { formatMoney, toNumber } from "@/lib/utils";
import type { DashboardSummary } from "@/types";

const cards: { key: keyof DashboardSummary; label: string; icon: LucideIcon }[] = [
  { key: "total_physical_cash", label: "Total physical cash", icon: Wallet },
  { key: "total_petty_cash", label: "Total petty cash (all vouchers)", icon: ListChecks },
  { key: "total_paid", label: "Total paid out", icon: HandCoins },
  { key: "total_left", label: "Total left (unpaid)", icon: Banknote },
];

const DEPT_COLORS = [
  "#0d9488",
  "#0284c7",
  "#059669",
  "#d97706",
  "#7c3aed",
  "#e11d48",
  "#4f46e5",
  "#ca8a04",
];

export function Dashboard() {
  const { data, isLoading } = useDashboardSummary();
  const charts = useDashboardCharts();

  const deptData = (charts.data?.by_department ?? []).map((d) => ({
    name: d.department,
    shortName: d.department.length > 18 ? `${d.department.slice(0, 16)}…` : d.department,
    value: toNumber(d.amount),
    count: d.count,
  }));

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted-foreground">Snapshot of cash on hand and voucher payouts.</p>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((c) => (
          <Card key={c.key}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{c.label}</CardTitle>
              <c.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {isLoading || !data ? "…" : formatMoney(data[c.key])}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Department distribution</CardTitle>
            <p className="text-xs text-muted-foreground">Petty cash by department</p>
          </CardHeader>
          <CardContent className="h-80 pt-2">
            {charts.isLoading ? (
              <p className="text-sm text-muted-foreground">Loading…</p>
            ) : deptData.length === 0 ? (
              <p className="flex h-full items-center justify-center text-sm text-muted-foreground">
                No departments yet
              </p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={deptData} margin={{ top: 16, right: 16, left: 8, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                  <XAxis dataKey="shortName" tick={{ fontSize: 12, fill: "#64748b" }} />
                  <YAxis
                    tick={{ fontSize: 12, fill: "#64748b" }}
                    width={64}
                    tickFormatter={(v) => `${v}`}
                  />
                  <Tooltip
                    cursor={{ fill: "rgba(148, 163, 184, 0.12)" }}
                    formatter={(value: number, _name, item) => [
                      `${formatMoney(value)} · ${item?.payload?.count ?? 0} vouchers`,
                      item?.payload?.name ?? "Department",
                    ]}
                    labelFormatter={() => ""}
                    contentStyle={{
                      borderRadius: 8,
                      border: "1px solid #e2e8f0",
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="value" name="Amount" radius={[8, 8, 0, 0]} maxBarSize={72}>
                    {deptData.map((_, i) => (
                      <Cell key={i} fill={DEPT_COLORS[i % DEPT_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">By department</CardTitle>
            <p className="text-xs text-muted-foreground">Share of total petty cash</p>
          </CardHeader>
          <CardContent className="h-80 pt-2">
            {charts.isLoading ? (
              <p className="text-sm text-muted-foreground">Loading…</p>
            ) : deptData.length === 0 ? (
              <p className="flex h-full items-center justify-center text-sm text-muted-foreground">
                No departments yet
              </p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={deptData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="46%"
                    innerRadius={58}
                    outerRadius={92}
                    paddingAngle={2}
                    labelLine={false}
                    label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
                  >
                    {deptData.map((_, i) => (
                      <Cell key={i} fill={DEPT_COLORS[i % DEPT_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number, _name, item) => [
                      `${formatMoney(value)} · ${item?.payload?.count ?? 0} vouchers`,
                      item?.payload?.name ?? "Department",
                    ]}
                    contentStyle={{
                      borderRadius: 8,
                      border: "1px solid #e2e8f0",
                      fontSize: 12,
                    }}
                  />
                  <Legend verticalAlign="bottom" height={36} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
