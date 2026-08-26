import { useCallback, useState } from "react";
import { FileUp, Upload } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  onFiles: (files: File[]) => void;
  disabled?: boolean;
}

export function VoucherUploadDropzone({ onFiles, disabled }: Props) {
  const [dragging, setDragging] = useState(false);

  const handleFiles = useCallback(
    (list: FileList | null) => {
      if (!list || disabled) return;
      const files = Array.from(list).filter(
        (f) =>
          f.type.startsWith("image/") ||
          f.type === "application/pdf" ||
          f.name.toLowerCase().endsWith(".pdf"),
      );
      if (files.length) onFiles(files);
    },
    [disabled, onFiles],
  );

  return (
    <label
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center transition-colors",
        dragging && "border-primary bg-teal-50",
        disabled && "pointer-events-none opacity-60",
      )}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handleFiles(e.dataTransfer.files);
      }}
    >
      <div className="mb-3 rounded-full bg-primary/10 p-3 text-primary">
        {dragging ? <Upload className="h-6 w-6" /> : <FileUp className="h-6 w-6" />}
      </div>
      <p className="text-sm font-medium text-slate-800">Drop voucher images or PDFs here</p>
      <p className="mt-1 text-xs text-muted-foreground">or click to browse — batch upload supported</p>
      <input
        type="file"
        className="hidden"
        accept="image/*,application/pdf,.pdf"
        multiple
        disabled={disabled}
        onChange={(e) => {
          handleFiles(e.target.files);
          e.target.value = "";
        }}
      />
    </label>
  );
}
