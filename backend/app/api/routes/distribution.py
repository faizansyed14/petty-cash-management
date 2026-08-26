from fastapi import APIRouter, HTTPException

from app.core.deps import CurrentUser, DbSession
from app.schemas.distribution import (
    DistributionCalculateRequest,
    DistributionConfirmRequest,
    DistributionPlanOut,
)
from app.services.distribution_service import calculate_distribution
from app.services.distribution_persist import confirm_distribution

router = APIRouter(prefix="/cash-distribution", tags=["cash-distribution"])


@router.post(
    "/calculate",
    response_model=DistributionPlanOut,
    summary="Calculate note distribution plan (not persisted)",
)
def calculate(payload: DistributionCalculateRequest, user: CurrentUser):
    payouts = [p.model_dump() for p in payload.payouts]
    result = calculate_distribution(payload.inventory, payouts, sort_order=payload.sort_order)
    return result


@router.post("/confirm", summary="Confirm and persist distribution")
def confirm(payload: DistributionConfirmRequest, db: DbSession, user: CurrentUser):
    try:
        dist = confirm_distribution(db, payload, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "id": str(dist.id),
        "total_distributed": str(dist.total_distributed),
        "total_shortfall": str(dist.total_shortfall),
        "created_at": dist.created_at.isoformat(),
    }
