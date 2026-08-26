from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine, SessionLocal
import app.db.models  # noqa: F401 — register models

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Petty Cash",
        description="Upload vouchers, preview/delete, distribute cash by denomination",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        detail = exc.detail
        message = detail if isinstance(detail, str) else str(detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"message": message, "code": exc.status_code}},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"error": {"message": str(exc), "code": 500}},
        )

    @app.on_event("startup")
    def on_startup():
        Base.metadata.create_all(bind=engine)
        from app.db.migrate_columns import (
            drop_cash_counts,
            ensure_distribution_line_reversal_columns,
            ensure_distribution_line_voucher_not_unique,
            ensure_voucher_settlement_columns,
            flatten_vouchers_drop_line_items,
        )

        ensure_voucher_settlement_columns(engine)
        ensure_distribution_line_voucher_not_unique(engine)
        ensure_distribution_line_reversal_columns(engine)
        drop_cash_counts(engine)
        flatten_vouchers_drop_line_items(engine)
        if settings.seed_on_startup:
            from app.db.seed import run_seed

            db = SessionLocal()
            try:
                run_seed(db)
            finally:
                db.close()

    app.include_router(api_router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
