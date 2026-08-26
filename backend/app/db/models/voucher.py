import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import String, DateTime, Date, Enum, ForeignKey, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class VoucherStatus(str, enum.Enum):
    EXTRACTED = "EXTRACTED"
    VERIFIED = "VERIFIED"
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    RECONCILED = "RECONCILED"


class SettlementType(str, enum.Enum):
    DEPOSITED = "DEPOSITED"
    CASH_COLLECTION = "CASH_COLLECTION"


class Voucher(Base):
    __tablename__ = "vouchers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    voucher_no: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    voucher_date: Mapped[datetime] = mapped_column(DateTime)
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id"))
    employee: Mapped["Employee"] = relationship()
    department_label: Mapped[str] = mapped_column(String(200))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(10), default="AED")
    classification: Mapped[str] = mapped_column(String(100), default="")
    details: Mapped[str] = mapped_column(String(500), default="")
    extraction_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    extracted_raw: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[VoucherStatus] = mapped_column(Enum(VoucherStatus), default=VoucherStatus.EXTRACTED)
    settlement_type: Mapped[SettlementType | None] = mapped_column(Enum(SettlementType), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    settlement_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    file_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
