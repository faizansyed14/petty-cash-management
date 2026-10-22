import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatMoney(value: string | number, currency = "AED") {
  const num = typeof value === "string" ? Number(value) : value;
  if (Number.isNaN(num)) return `${currency} 0.00`;
  return `${currency} ${num.toLocaleString("en-AE", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export function toNumber(value: string | number | null | undefined) {
  if (value == null || value === "") return 0;
  const n = typeof value === "number" ? value : Number(value);
  return Number.isNaN(n) ? 0 : n;
}

export function roundMoney(value: number) {
  return Math.round((value + Number.EPSILON) * 100) / 100;
}

/** ISO yyyy-mm-dd → dd/mm/yyyy */
export function toDisplayDate(iso: string | null | undefined): string {
  if (!iso) return "";
  const match = iso.slice(0, 10).match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!match) return "";
  return `${match[3]}/${match[2]}/${match[1]}`;
}

/** dd/mm/yyyy → ISO yyyy-mm-dd. Empty → null. Invalid → undefined. */
export function parseDisplayDate(text: string): string | null | undefined {
  const trimmed = text.trim();
  if (!trimmed) return null;
  const match = trimmed.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (!match) return undefined;
  const day = Number(match[1]);
  const month = Number(match[2]);
  const year = Number(match[3]);
  if (month < 1 || month > 12 || day < 1 || day > 31) return undefined;
  const iso = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
  const dt = new Date(`${iso}T00:00:00`);
  if (dt.getFullYear() !== year || dt.getMonth() + 1 !== month || dt.getDate() !== day) return undefined;
  return iso;
}
