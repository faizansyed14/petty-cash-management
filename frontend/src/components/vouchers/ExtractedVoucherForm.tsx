import { useEffect, type ReactNode } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { parse as parseDate, isValid, format } from "date-fns";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toNumber } from "@/lib/utils";
import type { VoucherDraft } from "@/types";

const formSchema = z.object({
  voucher_no: z.string().min(1, "Required"),
  voucher_date: z.string().min(1, "Required"),
  employee_code: z.string().min(1, "Required"),
  employee_name: z.string().min(1, "Required"),
  department_label: z.string().min(1, "Required"),
  total_amount: z.coerce.number().positive("Must be > 0"),
  currency: z.string().min(1),
  classification: z.string().optional(),
  details: z.string().optional(),
  extraction_source: z.string().optional(),
});

export type ExtractedVoucherFormValues = z.infer<typeof formSchema>;

/** Convert extracted dates like "Aug 24 2026 4:08PM" into yyyy-mm-dd for <input type="date">. */
export function toDateInputValue(raw: string | null | undefined): string {
  if (!raw?.trim()) return "";
  const text = raw.trim();
  if (/^\d{4}-\d{2}-\d{2}/.test(text)) return text.slice(0, 10);

  const patterns = [
    "MMM d yyyy h:mma",
    "MMM d yyyy h:mm a",
    "MMM d yyyy",
    "MMMM d yyyy",
    "dd/MM/yyyy",
    "d/M/yyyy",
    "yyyy-MM-dd",
  ];
  for (const pattern of patterns) {
    const parsed = parseDate(text.replace(/\s+/g, " "), pattern, new Date());
    if (isValid(parsed)) return format(parsed, "yyyy-MM-dd");
  }

  const native = new Date(text);
  if (!Number.isNaN(native.getTime())) return format(native, "yyyy-MM-dd");
  return "";
}

interface Props {
  draft: VoucherDraft;
  onSubmit: (values: ExtractedVoucherFormValues) => void | Promise<void>;
  submitting?: boolean;
  disabled?: boolean;
}

export function draftToDefaults(draft: VoucherDraft): ExtractedVoucherFormValues {
  return {
    voucher_no: draft.voucher_no || "",
    voucher_date: toDateInputValue(draft.voucher_date),
    employee_code: draft.employee_code || "",
    employee_name: draft.employee_name || "",
    department_label: draft.department_label || "",
    total_amount: toNumber(draft.total_amount || draft.amount) || 0,
    currency: draft.currency || "AED",
    classification: draft.classification || "",
    details: draft.details || "",
    extraction_source: draft.extraction_source || "",
  };
}

export function ExtractedVoucherForm({ draft, onSubmit, submitting, disabled }: Props) {
  const form = useForm<ExtractedVoucherFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: draftToDefaults(draft),
  });

  useEffect(() => {
    form.reset(draftToDefaults(draft));
  }, [draft, form]);

  return (
    <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Voucher no" error={form.formState.errors.voucher_no?.message}>
          <Input {...form.register("voucher_no")} />
        </Field>
        <Field label="Date" error={form.formState.errors.voucher_date?.message}>
          <Input type="date" {...form.register("voucher_date")} />
        </Field>
        <Field label="Employee code" error={form.formState.errors.employee_code?.message}>
          <Input {...form.register("employee_code")} />
        </Field>
        <Field label="Employee name" error={form.formState.errors.employee_name?.message}>
          <Input {...form.register("employee_name")} />
        </Field>
        <Field label="Department" error={form.formState.errors.department_label?.message}>
          <Input {...form.register("department_label")} />
        </Field>
        <Field label="Total amount" error={form.formState.errors.total_amount?.message}>
          <Input type="number" step="0.01" {...form.register("total_amount")} />
        </Field>
        <Field label="Classification" error={form.formState.errors.classification?.message}>
          <Input {...form.register("classification")} />
        </Field>
        <Field label="Details / Notes" error={form.formState.errors.details?.message}>
          <Input {...form.register("details")} />
        </Field>
      </div>

      <Button type="submit" className="w-full" disabled={submitting || disabled}>
        {submitting ? "Saving…" : disabled ? "Already saved" : "Save voucher"}
      </Button>
    </form>
  );
}

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      {children}
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}
