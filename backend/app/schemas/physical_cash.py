from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class PhysicalCashOut(BaseModel):
    id: UUID
    denominations: dict[str, Any]
    total_amount: Decimal
    updated_at: datetime

    model_config = {"from_attributes": True}


class PhysicalCashUpdate(BaseModel):
    denominations: dict[str, Any]


class DenomUpdate(BaseModel):
    count: int
