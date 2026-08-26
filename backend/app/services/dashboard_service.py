from collections import defaultdict
from decimal import Decimal
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.voucher import Voucher, VoucherStatus
from app.services import physical_cash_service
from app.utils.money import to_decimal


def get_summary(db: Session) -> dict:
    total_petty_cash_raw = db.query(func.coalesce(func.sum(Voucher.total_amount), 0)).scalar()
    total_paid_raw = (
        db.query(func.coalesce(func.sum(Voucher.total_amount), 0))
        .filter(Voucher.status == VoucherStatus.PAID)
        .scalar()
    )

    total_petty_cash = to_decimal(total_petty_cash_raw or Decimal("0.00"))
    total_paid = to_decimal(total_paid_raw or Decimal("0.00"))
    total_left = to_decimal(total_petty_cash - total_paid)

    physical = physical_cash_service.get_or_create(db)
    total_physical_cash = to_decimal(physical.total_amount or Decimal("0.00"))

    return {
        "total_physical_cash": total_physical_cash,
        "total_petty_cash": total_petty_cash,
        "total_paid": total_paid,
        "total_left": total_left,
    }


def get_charts(db: Session) -> dict:
    vouchers = db.query(Voucher).all()

    daily_map: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"amount": Decimal("0.00"), "paid": Decimal("0.00"), "unpaid": Decimal("0.00")}
    )
    dept_map: dict[str, dict[str, Decimal | int]] = defaultdict(
        lambda: {"amount": Decimal("0.00"), "count": 0}
    )

    for v in vouchers:
        amt = to_decimal(v.total_amount or 0)
        vd = v.voucher_date
        if isinstance(vd, datetime):
            day = vd.date().isoformat()
        elif vd is not None:
            day = str(vd)[:10]
        else:
            day = "unknown"

        daily_map[day]["amount"] += amt
        if v.status == VoucherStatus.PAID:
            daily_map[day]["paid"] += amt
        else:
            daily_map[day]["unpaid"] += amt

        dept = (v.department_label or "Unknown").strip() or "Unknown"
        dept_map[dept]["amount"] = to_decimal(dept_map[dept]["amount"]) + amt
        dept_map[dept]["count"] = int(dept_map[dept]["count"]) + 1

    daily = [
        {
            "date": day,
            "amount": to_decimal(vals["amount"]),
            "paid": to_decimal(vals["paid"]),
            "unpaid": to_decimal(vals["unpaid"]),
        }
        for day, vals in sorted(daily_map.items())
    ]

    by_department = sorted(
        [
            {
                "department": dept,
                "amount": to_decimal(vals["amount"]),
                "count": int(vals["count"]),
            }
            for dept, vals in dept_map.items()
        ],
        key=lambda x: x["amount"],
        reverse=True,
    )

    return {"daily": daily, "by_department": by_department}
