from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.distribution import Distribution, DistributionLine
from app.db.models.voucher import Voucher, VoucherStatus
from app.schemas.distribution import DistributionConfirmRequest
from app.services import physical_cash_service
from app.utils.money import to_decimal


def confirm_distribution(
    db: Session, payload: DistributionConfirmRequest, user_id: UUID
) -> Distribution:
    plan = payload.plan

    dist = Distribution(
        performed_by_id=user_id,
        total_distributed=to_decimal(plan.total_distributed),
        total_shortfall=to_decimal(plan.total_shortfall),
    )
    db.add(dist)
    db.flush()

    for line in plan.lines:
        db.add(
            DistributionLine(
                distribution_id=dist.id,
                employee_id=UUID(line.employee_id),
                voucher_id=UUID(line.voucher_id),
                amount_due=to_decimal(line.amount_due),
                amount_given=to_decimal(line.amount_given),
                shortfall=to_decimal(line.shortfall),
                breakdown=line.breakdown,
            )
        )
        voucher = db.get(Voucher, UUID(line.voucher_id))
        if voucher:
            if to_decimal(line.shortfall) == Decimal("0.00"):
                voucher.status = VoucherStatus.PAID
            else:
                voucher.status = VoucherStatus.PENDING_PAYMENT

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError(f"Could not save distribution: {exc.orig}") from exc
    db.refresh(dist)

    # Sync physical cash drawer with what's left after handing out notes/coins,
    # so the cashier never has to re-enter counts.
    physical_cash_service.update_full(db, plan.remaining_inventory)

    return dist
