from app.api.routes import auth, vouchers, distribution
from fastapi import APIRouter

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(vouchers.router)
api_router.include_router(distribution.router)
