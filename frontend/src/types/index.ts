export type Role = "CASHIER" | "MANAGER" | "ADMIN";

export type VoucherStatus =
  | "EXTRACTED"
  | "VERIFIED"
  | "PENDING_PAYMENT"
  | "PAID"
  | "RECONCILED";

export type SettlementType = "DEPOSITED" | "CASH_COLLECTION";

export type SortOrder = "ascending" | "descending" | "voucher_order";

export const UAE_BANKS = [
  "Abu Dhabi Commercial Bank (ADCB)",
  "Abu Dhabi Islamic Bank (ADIB)",
  "Ajman Bank",
  "Al Ansari Exchange",
  "Al Fardan Exchange",
  "Al Hilal Bank",
  "Al Jazira Exchange",
  "Bank of Sharjah",
  "Commercial Bank of Dubai (CBD)",
  "Dubai Bank",
  "Dubai Islamic Bank (DIB)",
  "Emirates Islamic",
  "Emirates NBD",
  "First Abu Dhabi Bank (FAB)",
  "HSBC UAE",
  "Lulu Exchange",
  "Mashreq Bank",
  "National Bank of Fujairah",
  "RAKBANK",
  "Sharjah Islamic Bank",
  "Standard Chartered UAE",
  "United Arab Bank",
] as const;

export const NOTE_DENOMS = ["1000", "500", "200", "100", "50", "20", "10", "5"] as const;
export const COIN_DENOMS = ["1", "0.5", "0.25"] as const;
export const ALL_DENOMS = [...NOTE_DENOMS, ...COIN_DENOMS] as const;

export type DenomKey = (typeof ALL_DENOMS)[number];
export type DenominationMap = Record<string, number>;

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface EmployeeBrief {
  id: string;
  employee_code: string;
  name: string;
}

export interface Voucher {
  id: string;
  voucher_no: string;
  voucher_date: string;
  employee: EmployeeBrief;
  department_label: string;
  total_amount: string | number;
  currency: string;
  classification: string;
  details: string;
  extraction_source: string | null;
  status: VoucherStatus;
  settlement_type: SettlementType | null;
  bank_name: string | null;
  settlement_date: string | null;
  file_number: string | null;
  created_at: string;
}

export interface VoucherUpdate {
  settlement_type?: SettlementType | null;
  bank_name?: string | null;
  settlement_date?: string | null;
  clear_settlement?: boolean;
  status?: "PAID" | "PENDING_PAYMENT";
  file_number?: string | null;
}

export interface VoucherDraft {
  voucher_no: string;
  voucher_date: string;
  employee_code: string;
  employee_name: string;
  department_label: string;
  classification: string;
  details: string;
  amount: string;
  total_amount: string;
  currency: string;
  extraction_source: string;
  extracted_raw: Record<string, unknown>;
  already_exists?: boolean;
  existing_voucher_id?: string | null;
}

export interface VoucherCreate {
  voucher_no: string;
  voucher_date: string;
  employee_code: string;
  employee_name: string;
  department_label: string;
  total_amount: number | string;
  currency?: string;
  classification?: string;
  details?: string;
  extraction_source?: string | null;
  extracted_raw?: Record<string, unknown> | null;
  status?: VoucherStatus;
}

export interface VoucherListResponse {
  items: Voucher[];
  total: number;
}

export interface PayoutIn {
  voucher_id: string;
  employee_id: string;
  amount_due: number | string;
  employee_name?: string;
  voucher_no?: string;
}

export interface DistributionCalculateRequest {
  inventory: DenominationMap;
  payouts: PayoutIn[];
  sort_order?: SortOrder;
}

export interface DistributionLine {
  voucher_id: string;
  employee_id: string;
  employee_name: string;
  voucher_no: string;
  amount_due: string | number;
  amount_given: string | number;
  shortfall: string | number;
  breakdown: DenominationMap;
  insufficient_denominations: boolean;
}

export interface DistributionPlan {
  lines: DistributionLine[];
  total_distributed: string | number;
  total_shortfall: string | number;
  remaining_inventory: DenominationMap;
  starting_total: string | number;
  remaining_total: string | number;
  reconciles: boolean;
}

export interface DistributionConfirmRequest {
  inventory: DenominationMap;
  plan: DistributionPlan;
}

export interface DistributionConfirmResult {
  id: string;
  total_distributed: string;
  total_shortfall: string;
  created_at: string;
}

export interface PhysicalCash {
  id: string;
  denominations: DenominationMap;
  total_amount: string | number;
  updated_at: string;
}

export interface DashboardSummary {
  total_physical_cash: string | number;
  total_petty_cash: string | number;
  total_paid: string | number;
  total_left: string | number;
}

export interface DailySpendPoint {
  date: string;
  amount: string | number;
  paid: string | number;
  unpaid: string | number;
}

export interface DepartmentSpend {
  department: string;
  amount: string | number;
  count: number;
}

export interface DashboardCharts {
  daily: DailySpendPoint[];
  by_department: DepartmentSpend[];
}

export interface BatchQueueItem {
  id: string;
  file: File;
  previewUrl: string;
  status: "queued" | "extracting" | "ready" | "saving" | "saved" | "error";
  draft?: VoucherDraft;
  error?: string;
}
