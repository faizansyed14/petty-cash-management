import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Distribution(Base):
    __tablename__ = "distributions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    performed_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    total_distributed: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total_shortfall: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    lines: Mapped[list["DistributionLine"]] = relationship(
        back_populates="distribution", cascade="all, delete-orphan"
    )


class DistributionLine(Base):
    __tablename__ = "distribution_lines"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    distribution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("distributions.id"))
    distribution: Mapped["Distribution"] = relationship(back_populates="lines")
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id"))
    # Not unique: a voucher can be marked Unpaid again and re-distributed later.
    voucher_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vouchers.id"))
    amount_due: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    amount_given: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    shortfall: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    breakdown: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # Set once the notes/coins handed out for this line have been returned to
    # Physical Cash (voucher flipped back to Unpaid). Prevents double-refunding.
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
