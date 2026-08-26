import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PhysicalCash(Base):
    """Singleton row holding the cashier's current physical note/coin counts."""

    __tablename__ = "physical_cash"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    denominations: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
