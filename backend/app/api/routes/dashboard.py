from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.schemas.dashboard import DashboardCharts, DashboardSummary
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary, summary="Aggregated cash summary")
def get_summary(db: DbSession, user: CurrentUser):
    return dashboard_service.get_summary(db)


@router.get("/charts", response_model=DashboardCharts, summary="Line + department chart data")
def get_charts(db: DbSession, user: CurrentUser):
    return dashboard_service.get_charts(db)
