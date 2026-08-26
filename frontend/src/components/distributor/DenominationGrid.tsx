import { ALL_DENOMS, COIN_DENOMS, NOTE_DENOMS, type DenominationMap } from "@/types";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { formatMoney, roundMoney, toNumber } from "@/lib/utils";

interface Props {
  value: DenominationMap;
  onChange: (next: DenominationMap) => void;
  readOnly?: boolean;
}

export function DenominationGrid({ value, onChange, readOnly }: Props) {
  const setCount = (denom: string, count: number) => {
    onChange({ ...value, [denom]: Math.max(0, Math.floor(count) || 0) });
  };

  const total = roundMoney(
    ALL_DENOMS.reduce((sum, d) => sum + toNumber(value[d] ?? 0) * Number(d), 0),
  );

  return (
    <div className="space-y-4">
      <section>
        <h4 className="mb-2 text-sm font-semibold text-slate-700">How many of each note?</h4>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {NOTE_DENOMS.map((d) => (
            <DenomField
              key={d}
              denom={d}
              count={value[d] ?? 0}
              readOnly={readOnly}
              onChange={(n) => setCount(d, n)}
            />
          ))}
        </div>
      </section>
      <section>
        <h4 className="mb-2 text-sm font-semibold text-slate-700">How many of each coin?</h4>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {COIN_DENOMS.map((d) => (
            <DenomField
              key={d}
              denom={d}
              count={value[d] ?? 0}
              readOnly={readOnly}
              onChange={(n) => setCount(d, n)}
            />
          ))}
        </div>
      </section>
      <div className="rounded-lg bg-muted px-4 py-3 text-sm font-semibold">
        Total cash on hand: {formatMoney(total)}
      </div>
    </div>
  );
}

function DenomField({
  denom,
  count,
  onChange,
  readOnly,
}: {
  denom: string;
  count: number;
  onChange: (n: number) => void;
  readOnly?: boolean;
}) {
  const subtotal = roundMoney(count * Number(denom));
  return (
    <div className="space-y-1.5 rounded-lg border border-border bg-card p-3">
      <Label className="text-xs text-muted-foreground">AED {denom}</Label>
      <Input
        type="number"
        min={0}
        step={1}
        value={count}
        disabled={readOnly}
        onChange={(e) => onChange(Number(e.target.value))}
      />
      <p className="text-xs text-muted-foreground">{formatMoney(subtotal)}</p>
    </div>
  );
}
