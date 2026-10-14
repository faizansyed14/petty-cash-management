from datetime import date, datetime
from decimal import Decimal
import re
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.db.models.voucher import SettlementType, VoucherStatus
from app.utils.banks import UAE_BANKS
from app.utils.money import to_decimal

FILE_NUMBER_RE = re.compile(r"^[0-9/\-]*$")


def _validate_file_number(v: str | None) -> str | None:
    if v is None:
        return None
    text = str(v).strip()
    if not text:
        return None
    if not FILE_NUMBER_RE.match(text):
        raise ValueError("File number: digits, / and - only")
    return text


class VoucherCreate(BaseModel):
    voucher_no: str
    voucher_date: datetime
    employee_code: str
    employee_name: str
    department_label: str
    total_amount: Decimal
    currency: str = "AED"
    classification: str = ""
    details: str = ""
    extraction_source: str | None = None
    extracted_raw: dict[str, Any] | None = None
    status: VoucherStatus = VoucherStatus.VERIFIED

    @field_validator("total_amount", mode="before")
    @classmethod
    def coerce_total(cls, v):
        return to_decimal(v)


class VoucherUpdate(BaseModel):
    settlement_type: SettlementType | None = None
    bank_name: str | None = None
    settlement_date: date | None = None
    clear_settlement: bool = False
    status: Literal["PAID", "PENDING_PAYMENT"] | None = None
    file_number: str | None = None

    @field_validator("file_number", mode="before")
    @classmethod
    def coerce_file_number(cls, v):
        return _validate_file_number(v)

    @model_validator(mode="after")
    def validate_settlement(self):
        if self.clear_settlement:
            return self
        if self.settlement_type == SettlementType.DEPOSITED:
            if self.bank_name and self.bank_name not in UAE_BANKS:
                raise ValueError(f"Unknown bank. Choose one of: {', '.join(UAE_BANKS)}")
        if self.settlement_type == SettlementType.CASH_COLLECTION:
            self.bank_name = None
        return self


class EmployeeBrief(BaseModel):
    id: UUID
    employee_code: str
    name: str

    model_config = {"from_attributes": True}


class VoucherOut(BaseModel):
    id: UUID
    voucher_no: str
    voucher_date: datetime
    employee: EmployeeBrief
    department_label: str
    total_amount: Decimal
    currency: str
    classification: str = ""
    details: str = ""
    extraction_source: str | None
    status: VoucherStatus
    settlement_type: SettlementType | None = None
    bank_name: str | None = None
    settlement_date: date | None = None
    file_number: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class VoucherDraft(BaseModel):
    voucher_no: str = ""
    voucher_date: str = ""
    employee_code: str = ""
    employee_name: str = ""
    department_label: str = ""
    classification: str = ""
    details: str = ""
    amount: str = ""
    total_amount: str = ""
    currency: str = "AED"
    extraction_source: str = ""
    extracted_raw: dict[str, Any] = Field(default_factory=dict)
    already_exists: bool = False
    existing_voucher_id: str | None = None


class VoucherListResponse(BaseModel):
    items: list[VoucherOut]
    total: int


class VoucherExtractResponse(BaseModel):
    """One PDF can contain many OPV petty-cash vouchers."""

    items: list[VoucherDraft]
    count: int


class BanksResponse(BaseModel):
    banks: list[str]
