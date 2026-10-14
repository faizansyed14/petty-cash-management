import { useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Trash2 } from "lucide-react";
import { toast } from "sonner";
import {
  ExtractedVoucherForm,
  draftToDefaults,
  type ExtractedVoucherFormValues,
} from "@/components/vouchers/ExtractedVoucherForm";
import { VoucherUploadDropzone } from "@/components/vouchers/VoucherUploadDropzone";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCreateVoucher, useExtractVoucher } from "@/hooks/useVouchers";
import { getErrorMessage } from "@/services/api";
import type { BatchQueueItem, VoucherCreate, VoucherDraft } from "@/types";

function draftToCreatePayload(draft: VoucherDraft): VoucherCreate {
  const values = draftToDefaults(draft);
  return {
    voucher_no: values.voucher_no,
    voucher_date: new Date(values.voucher_date).toISOString(),
    employee_code: values.employee_code,
    employee_name: values.employee_name,
    department_label: values.department_label,
    total_amount: values.total_amount,
    currency: values.currency,
    classification: values.classification || "",
    details: values.details || "",
    extraction_source: values.extraction_source || draft.extraction_source || null,
    extracted_raw: draft.extracted_raw ?? null,
  };
}

function canBulkSave(item: BatchQueueItem) {
  return item.status === "ready" && !!item.draft && !item.draft.already_exists;
}

export function UploadVoucher() {
  const extract = useExtractVoucher();
  const create = useCreateVoucher();
  const [queue, setQueue] = useState<BatchQueueItem[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [savingAll, setSavingAll] = useState(false);

  const active = useMemo(() => queue.find((q) => q.id === activeId) ?? null, [queue, activeId]);
  const activeIndex = useMemo(
    () => (activeId ? queue.findIndex((q) => q.id === activeId) : -1),
    [queue, activeId],
  );

  const goPrev = () => {
    if (activeIndex <= 0) return;
    setActiveId(queue[activeIndex - 1].id);
  };
  const goNext = () => {
    if (activeIndex < 0 || activeIndex >= queue.length - 1) return;
    setActiveId(queue[activeIndex + 1].id);
  };

  const counts = useMemo(() => {
    const c = { total: queue.length, ready: 0, saved: 0, error: 0, extracting: 0, skipped: 0 };
    for (const q of queue) {
      if (q.status === "ready" && q.draft?.already_exists) c.skipped += 1;
      else if (q.status === "ready") c.ready += 1;
      else if (q.status === "saved") c.saved += 1;
      else if (q.status === "error") c.error += 1;
      else if (q.status === "extracting" || q.status === "queued" || q.status === "saving")
        c.extracting += 1;
    }
    return c;
  }, [queue]);

  const clearAll = () => {
    setQueue((prev) => {
      const urls = new Set(prev.map((q) => q.previewUrl));
      urls.forEach((url) => URL.revokeObjectURL(url));
      return [];
    });
    setActiveId(null);
    toast.message("Cleared upload queue");
  };

  const enqueue = async (files: File[]) => {
    const placeholders: BatchQueueItem[] = files.map((file) => ({
      id: crypto.randomUUID(),
      file,
      previewUrl: URL.createObjectURL(file),
      status: "queued",
    }));
    setQueue((prev) => [...prev, ...placeholders]);
    setActiveId((prev) => prev ?? placeholders[0]?.id ?? null);
    toast.message(`Queued ${files.length} file${files.length === 1 ? "" : "s"}`);

    for (const placeholder of placeholders) {
      setQueue((prev) =>
        prev.map((q) => (q.id === placeholder.id ? { ...q, status: "extracting" } : q)),
      );
      try {
        const drafts = await extract.mutateAsync(placeholder.file);
        if (!drafts.length) {
          setQueue((prev) =>
            prev.map((q) =>
              q.id === placeholder.id
                ? { ...q, status: "error", error: "No OPV vouchers found in file" }
                : q,
            ),
          );
          continue;
        }

        const [first, ...rest] = drafts;
        const extra: BatchQueueItem[] = rest.map((draft) => ({
          id: crypto.randomUUID(),
          file: placeholder.file,
          previewUrl: placeholder.previewUrl,
          status: "ready" as const,
          draft,
        }));

        setQueue((prev) => {
          const updated = prev.map((q) =>
            q.id === placeholder.id ? { ...q, status: "ready" as const, draft: first } : q,
          );
          const idx = updated.findIndex((q) => q.id === placeholder.id);
          if (idx < 0 || !extra.length) return [...updated, ...extra];
          return [...updated.slice(0, idx + 1), ...extra, ...updated.slice(idx + 1)];
        });

        toast.success(
          `${placeholder.file.name}: ${drafts.length} OPV voucher${drafts.length === 1 ? "" : "s"}`,
        );
      } catch (err) {
        setQueue((prev) =>
          prev.map((q) =>
            q.id === placeholder.id
              ? { ...q, status: "error", error: getErrorMessage(err) }
              : q,
          ),
        );
        toast.error(`Extract failed: ${placeholder.file.name}`);
      }
    }
  };

  const saveOne = async (item: BatchQueueItem, values?: ExtractedVoucherFormValues) => {
    if (!item.draft) throw new Error("No extracted data");
    if (item.draft.already_exists) throw new Error("Already exists");

    const payload: VoucherCreate = values
      ? {
          voucher_no: values.voucher_no,
          voucher_date: new Date(values.voucher_date).toISOString(),
          employee_code: values.employee_code,
          employee_name: values.employee_name,
          department_label: values.department_label,
          total_amount: values.total_amount,
          currency: values.currency,
          classification: values.classification || "",
          details: values.details || "",
          extraction_source: values.extraction_source || item.draft.extraction_source || null,
          extracted_raw: item.draft.extracted_raw ?? null,
        }
      : draftToCreatePayload(item.draft);

    if (!payload.voucher_no || !payload.voucher_date || !payload.employee_code) {
      throw new Error("Missing required fields — open and fix this voucher first");
    }

    setQueue((prev) => prev.map((q) => (q.id === item.id ? { ...q, status: "saving" } : q)));
    try {
      await create.mutateAsync(payload);
      setQueue((prev) => prev.map((q) => (q.id === item.id ? { ...q, status: "saved" } : q)));
    } catch (err) {
      setQueue((prev) =>
        prev.map((q) =>
          q.id === item.id ? { ...q, status: "error", error: getErrorMessage(err) } : q,
        ),
      );
      throw err;
    }
  };

  const save = async (values: ExtractedVoucherFormValues) => {
    if (!active) return;
    try {
      await saveOne(active, values);
      toast.success(`Saved ${values.voucher_no}`);
      setQueue((prev) => {
        const next = prev.find(
          (q) => q.id !== active.id && (q.status === "ready" || q.status === "queued"),
        );
        if (next) setActiveId(next.id);
        return prev;
      });
    } catch (err) {
      toast.error(getErrorMessage(err, "Save failed"));
    }
  };

  const saveAll = async () => {
    const targets = queue.filter(canBulkSave);
    if (!targets.length) {
      toast.error("No ready vouchers to save");
      return;
    }
    setSavingAll(true);
    let ok = 0;
    let fail = 0;
    for (const item of targets) {
      try {
        await saveOne(item);
        ok += 1;
      } catch {
        fail += 1;
      }
    }
    setSavingAll(false);
    if (ok) toast.success(`Saved ${ok} voucher${ok === 1 ? "" : "s"}`);
    if (fail) toast.error(`${fail} failed — open those chips to fix`);
  };

  return (
    <div className="space-y-6">
      <VoucherUploadDropzone
        onFiles={enqueue}
        disabled={extract.isPending || savingAll}
      />

      {queue.length > 0 ? (
        <Card>
          <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle className="text-base">Batch queue · {counts.total} vouchers</CardTitle>
              <p className="text-xs text-muted-foreground">
                Ready {counts.ready} · Saved {counts.saved} · Skipped (duplicate) {counts.skipped} ·
                Working {counts.extracting} · Errors {counts.error}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={clearAll}
                disabled={savingAll || extract.isPending}
              >
                <Trash2 className="h-4 w-4" />
                Clear
              </Button>
              <Button
                type="button"
                onClick={saveAll}
                disabled={savingAll || counts.ready === 0}
                className="bg-orange-500 text-white hover:bg-orange-600"
              >
                {savingAll
                  ? "Saving all…"
                  : `Save all vouchers${counts.ready ? ` (${counts.ready})` : ""}`}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex max-h-40 flex-wrap gap-2 overflow-y-auto">
              {queue.map((item) => (
                <Button
                  key={item.id}
                  size="sm"
                  variant={item.id === activeId ? "default" : "outline"}
                  onClick={() => setActiveId(item.id)}
                  className="max-w-[220px]"
                >
                  <span className="truncate">
                    {item.draft?.voucher_no || item.file.name.slice(0, 18)}
                  </span>
                  <Badge
                    variant={
                      item.status === "saved"
                        ? "success"
                        : item.status === "error"
                          ? "destructive"
                          : item.draft?.already_exists
                            ? "warning"
                            : "secondary"
                    }
                    className="ml-1 shrink-0"
                  >
                    {item.draft?.already_exists && item.status === "ready"
                      ? "duplicate"
                      : item.status}
                  </Badge>
                </Button>
              ))}
            </div>
            <p className="mt-2 text-xs text-muted-foreground">
              Click any chip to preview + review extracted fields (same as single upload). Save all
              uses extracted data for every ready voucher that is not a duplicate.
            </p>
          </CardContent>
        </Card>
      ) : null}

      {active ? (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border bg-card px-3 py-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={activeIndex <= 0}
              onClick={goPrev}
            >
              <ChevronLeft className="h-4 w-4" /> Previous
            </Button>
            <span className="text-sm font-medium text-muted-foreground">
              Voucher {activeIndex + 1} of {queue.length}
              {active.draft?.voucher_no ? (
                <span className="ml-2 text-foreground">· {active.draft.voucher_no}</span>
              ) : null}
            </span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={activeIndex < 0 || activeIndex >= queue.length - 1}
              onClick={goNext}
            >
              Next <ChevronRight className="h-4 w-4" />
            </Button>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
          <Card className="overflow-hidden">
            <CardHeader>
              <CardTitle className="text-base">Preview — {active.file.name}</CardTitle>
            </CardHeader>
            <CardContent>
              {active.file.type.startsWith("image/") ? (
                <img
                  src={active.previewUrl}
                  alt="Voucher preview"
                  className="max-h-[70vh] w-full rounded-lg object-contain"
                />
              ) : (
                <iframe
                  title="Voucher preview"
                  src={active.previewUrl}
                  className="h-[70vh] w-full rounded-lg border border-border"
                />
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Review extracted fields</CardTitle>
            </CardHeader>
            <CardContent>
              {active.status === "extracting" || active.status === "queued" ? (
                <p className="text-sm text-muted-foreground">Extracting voucher data…</p>
              ) : active.status === "error" && !active.draft ? (
                <p className="text-sm text-destructive">{active.error}</p>
              ) : active.draft ? (
                <div className="space-y-4">
                  {active.draft.already_exists ? (
                    <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
                      Voucher <strong>{active.draft.voucher_no}</strong> is already saved.
                      Employees can have many vouchers, but each voucher number is unique.
                      Open it from{" "}
                      <a className="font-medium underline" href="/vouchers">
                        Vouchers
                      </a>
                      , or delete the old one before re-importing.
                    </div>
                  ) : null}
                  <ExtractedVoucherForm
                    draft={active.draft}
                    onSubmit={save}
                    submitting={active.status === "saving" || create.isPending || savingAll}
                    disabled={!!active.draft.already_exists || active.status === "saved"}
                  />
                  {active.draft.already_exists ? (
                    <p className="text-xs text-muted-foreground">
                      Save disabled — this voucher number already exists in the system.
                    </p>
                  ) : null}
                </div>
              ) : active.status === "saved" ? (
                <p className="text-sm text-emerald-700">
                  Voucher saved. Go to <strong>Distribute cash</strong> to pay it out.
                </p>
              ) : null}
            </CardContent>
          </Card>
          </div>
        </div>
      ) : (
        <Card>
          <CardContent className="flex h-40 items-center justify-center text-sm text-muted-foreground">
            Drop 1–200 PDFs/images — each extracts, then review or Save all
          </CardContent>
        </Card>
      )}
    </div>
  );
}
