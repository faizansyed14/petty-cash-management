from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.utils.money import to_decimal


class PayoutIn(BaseModel):
    voucher_id: UUID
    employee_id: UUID
    amount_due: Decimal
    employee_name: str = ""
    voucher_no: str = ""

    @field_validator("amount_due", mode="before")
    @classmethod
    def coerce_amount(cls, v):
        return to_decimal(v)


class DistributionCalculateRequest(BaseModel):
    inventory: dict[str, Any]
    payouts: list[PayoutIn] = Field(min_length=1)
    sort_order: Literal["ascending", "descending", "voucher_order"] = "ascending"


class DistributionLineOut(BaseModel):
    voucher_id: str
    employee_id: str
    employee_name: str = ""
    voucher_no: str = ""
    amount_due: Decimal
    amount_given: Decimal
    shortfall: Decimal
    breakdown: dict[str, Any]
    insufficient_denominations: bool = False


class DistributionPlanOut(BaseModel):
    lines: list[DistributionLineOut]
    total_distributed: Decimal
    total_shortfall: Decimal
    remaining_inventory: dict[str, Any]
    starting_total: Decimal
    remaining_total: Decimal
    reconciles: bool


class DistributionConfirmRequest(BaseModel):
    inventory: dict[str, Any]
    plan: DistributionPlanOut
