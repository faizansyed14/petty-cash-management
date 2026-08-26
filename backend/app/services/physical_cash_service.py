from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.physical_cash import PhysicalCash
from app.utils.money import DEFAULT_COIN_DENOMS, DEFAULT_NOTE_DENOMS, denom_to_fils, from_fils

ALL_DENOMS = DEFAULT_NOTE_DENOMS + DEFAULT_COIN_DENOMS


def _compute_total(denominations: dict[str, Any]) -> Decimal:
    fils = sum(denom_to_fils(d) * int(c or 0) for d, c in denominations.items())
    return from_fils(fils)


def get_or_create(db: Session) -> PhysicalCash:
    row = db.query(PhysicalCash).first()
    if row:
        return row
    row = PhysicalCash(denominations={d: 0 for d in ALL_DENOMS}, total_amount=Decimal("0.00"))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_full(db: Session, denominations: dict[str, Any]) -> PhysicalCash:
    row = get_or_create(db)
    clean = {str(k): max(0, int(v or 0)) for k, v in denominations.items()}
    row.denominations = clean
    row.total_amount = _compute_total(clean)
    db.commit()
    db.refresh(row)
    return row


def update_denom(db: Session, denom: str, count: int) -> PhysicalCash:
    row = get_or_create(db)
    current = dict(row.denominations or {})
    current[str(denom)] = max(0, int(count or 0))
    row.denominations = current
    row.total_amount = _compute_total(current)
    db.commit()
    db.refresh(row)
    return row


def clear_denom(db: Session, denom: str) -> PhysicalCash:
    return update_denom(db, denom, 0)


def add_counts(db: Session, breakdown: dict[str, Any]) -> PhysicalCash:
    """Add notes/coins back into the drawer (e.g. a paid voucher was reverted to unpaid)."""
    row = get_or_create(db)
    current = dict(row.denominations or {})
    for denom, count in (breakdown or {}).items():
        key = str(denom)
        current[key] = max(0, int(current.get(key, 0) or 0) + int(count or 0))
    row.denominations = current
    row.total_amount = _compute_total(current)
    db.commit()
    db.refresh(row)
    return row
