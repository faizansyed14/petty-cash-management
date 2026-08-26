import { useEffect, useState } from "react";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  useClearPhysicalCashDenom,
  usePhysicalCash,
  useUpdatePhysicalCashDenom,
} from "@/hooks/usePhysicalCash";
import { formatMoney, roundMoney, toNumber } from "@/lib/utils";
import { getErrorMessage } from "@/services/api";
import { ALL_DENOMS, COIN_DENOMS, NOTE_DENOMS, type DenominationMap } from "@/types";

export function PhysicalCashPage() {
  const { data, isLoading } = usePhysicalCash();
  const updateDenom = useUpdatePhysicalCashDenom();
  const clearDenom = useClearPhysicalCashDenom();
  const [local, setLocal] = useState<DenominationMap>({});

  useEffect(() => {
    if (data?.denominations) setLocal(data.denominations);
  }, [data?.denominations]);

  const total = roundMoney(
    ALL_DENOMS.reduce((sum, d) => sum + toNumber(local[d] ?? 0) * Number(d), 0),
  );

  const save = async (denom: string) => {
    const count = Math.max(0, Math.floor(toNumber(local[denom])) || 0);
    setLocal((s) => ({ ...s, [denom]: count }));
    if (count === toNumber(data?.denominations?.[denom] ?? 0)) return;
    try {
      await updateDenom.mutateAsync({ denom, count });
    } catch (err) {
      toast.error(getErrorMessage(err, "Save failed"));
    }
  };

  const clear = async (denom: string) => {
    setLocal((s) => ({ ...s, [denom]: 0 }));
    try {
      await clearDenom.mutateAsync(denom);
      toast.success(`Cleared AED ${denom}`);
    } catch (err) {
      toast.error(getErrorMessage(err, "Clear failed"));
    }
  };

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted-foreground">
        Count what&apos;s physically in the drawer. This feeds straight into the Distribute cash page —
        no need to enter it again.
      </p>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Notes</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {NOTE_DENOMS.map((d) => (
              <DenomRow
                key={d}
                denom={d}
                value={local[d] ?? 0}
                onChange={(n) => setLocal((s) => ({ ...s, [d]: n }))}
                onBlur={() => save(d)}
                onClear={() => clear(d)}
              />
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Coins</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {COIN_DENOMS.map((d) => (
              <DenomRow
                key={d}
                denom={d}
                value={local[d] ?? 0}
                onChange={(n) => setLocal((s) => ({ ...s, [d]: n }))}
                onBlur={() => save(d)}
                onClear={() => clear(d)}
              />
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="rounded-lg bg-muted px-4 py-3 text-sm font-semibold">
        Total physical cash: {isLoading ? "…" : formatMoney(total)}
      </div>
    </div>
  );
}

function DenomRow({
  denom,
  value,
  onChange,
  onBlur,
  onClear,
}: {
  denom: string;
  value: number;
  onChange: (n: number) => void;
  onBlur: () => void;
  onClear: () => void;
}) {
  const subtotal = roundMoney(value * Number(denom));
  return (
    <div className="space-y-1.5 rounded-lg border border-border bg-card p-3">
      <div className="flex items-center justify-between">
        <Label className="text-xs text-muted-foreground">AED {denom}</Label>
        <button
          type="button"
          onClick={onClear}
          className="text-muted-foreground transition-colors hover:text-destructive"
          title="Clear to 0"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>
      <Input
        type="number"
        inputMode="numeric"
        min={0}
        placeholder="0"
        value={value === 0 ? "" : value}
        className="[-moz-appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
        onChange={(e) => onChange(e.target.value === "" ? 0 : Number(e.target.value))}
        onBlur={onBlur}
      />
      <p className="text-xs text-muted-foreground">{formatMoney(subtotal)}</p>
    </div>
  );
}
