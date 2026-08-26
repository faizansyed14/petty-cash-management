from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.schemas.physical_cash import DenomUpdate, PhysicalCashOut, PhysicalCashUpdate
from app.services import physical_cash_service

router = APIRouter(prefix="/physical-cash", tags=["physical-cash"])


@router.get("", response_model=PhysicalCashOut, summary="Get current physical cash counts")
def get_physical_cash(db: DbSession, user: CurrentUser):
    return physical_cash_service.get_or_create(db)


@router.put("", response_model=PhysicalCashOut, summary="Replace all denomination counts")
def replace_physical_cash(payload: PhysicalCashUpdate, db: DbSession, user: CurrentUser):
    return physical_cash_service.update_full(db, payload.denominations)


@router.patch("/{denom}", response_model=PhysicalCashOut, summary="Update one denomination count")
def update_physical_cash_denom(denom: str, payload: DenomUpdate, db: DbSession, user: CurrentUser):
    return physical_cash_service.update_denom(db, denom, payload.count)


@router.delete("/{denom}", response_model=PhysicalCashOut, summary="Clear one denomination (set to 0)")
def clear_physical_cash_denom(denom: str, db: DbSession, user: CurrentUser):
    return physical_cash_service.clear_denom(db, denom)
