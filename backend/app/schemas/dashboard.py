from decimal import Decimal

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_physical_cash: Decimal
    total_petty_cash: Decimal
    total_paid: Decimal
    total_left: Decimal


class DailySpendPoint(BaseModel):
    date: str
    amount: Decimal
    paid: Decimal
    unpaid: Decimal


class DepartmentSpend(BaseModel):
    department: str
    amount: Decimal
    count: int


class DashboardCharts(BaseModel):
    daily: list[DailySpendPoint]
    by_department: list[DepartmentSpend]
