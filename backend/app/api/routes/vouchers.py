from uuid import UUID

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response

from app.core.deps import CurrentUser, DbSession
from app.db.models.voucher import VoucherStatus
from app.schemas.voucher import (
    BanksResponse,
    VoucherCreate,
    VoucherDraft,
    VoucherListResponse,
    VoucherOut,
    VoucherUpdate,
)
from app.services import voucher_service
from app.services.excel_export_service import build_voucher_register_excel
from app.utils.banks import UAE_BANKS

router = APIRouter(prefix="/vouchers", tags=["vouchers"])


@router.post("/extract", response_model=VoucherDraft, summary="Upload and extract voucher (no persist)")
async def extract_voucher(db: DbSession, user: CurrentUser, file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    content = await file.read()
    try:
        return voucher_service.extract_from_bytes(file.filename, content, db=db)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Extraction failed: {exc}") from exc


@router.post("", response_model=VoucherOut, status_code=status.HTTP_201_CREATED, summary="Persist reviewed voucher")
def create_voucher(payload: VoucherCreate, db: DbSession, user: CurrentUser):
    try:
        data = payload.model_copy(update={"status": VoucherStatus.PENDING_PAYMENT})
        return voucher_service.create_voucher(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=VoucherListResponse, summary="List vouchers")
def list_vouchers(
    db: DbSession,
    user: CurrentUser,
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2000),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = None,
    skip: int = 0,
    limit: int = Query(500, le=1000),
):
    statuses: list[VoucherStatus] | None = None
    single: VoucherStatus | None = None
    if status_filter:
        parts = [p.strip() for p in status_filter.split(",") if p.strip()]
        try:
            parsed = [VoucherStatus(p) for p in parts]
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid status: {exc}") from exc
        if len(parsed) == 1:
            single = parsed[0]
        else:
            statuses = parsed

    items, total = voucher_service.list_vouchers(
        db,
        month=month,
        year=year,
        status=single,
        statuses=statuses,
        search=search,
        skip=skip,
        limit=limit,
    )
    return VoucherListResponse(items=items, total=total)


@router.get("/meta/banks", response_model=BanksResponse, summary="UAE bank list for deposits")
def list_banks(user: CurrentUser):
    return BanksResponse(banks=UAE_BANKS)


@router.get("/export/excel", summary="Export voucher register Excel (ALPHA DATA RECRUITMENT layout)")
def export_excel(db: DbSession, user: CurrentUser):
    content = build_voucher_register_excel(db)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="ALPHA_DATA_RECRUITMENT_vouchers.xlsx"'},
    )


@router.get("/{voucher_id}", response_model=VoucherOut, summary="Get voucher detail")
def get_voucher(voucher_id: UUID, db: DbSession, user: CurrentUser):
    voucher = voucher_service.get_voucher(db, voucher_id)
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    return voucher


@router.patch("/{voucher_id}", response_model=VoucherOut, summary="Update settlement / status fields")
def patch_voucher(voucher_id: UUID, payload: VoucherUpdate, db: DbSession, user: CurrentUser):
    try:
        return voucher_service.update_voucher(db, voucher_id, payload)
    except ValueError as exc:
        msg = str(exc)
        code = 404 if msg == "Voucher not found" else 400
        raise HTTPException(status_code=code, detail=msg) from exc


@router.delete("/{voucher_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete voucher")
def delete_voucher(voucher_id: UUID, db: DbSession, user: CurrentUser):
    try:
        voucher_service.delete_voucher(db, voucher_id)
    except ValueError as exc:
        msg = str(exc)
        code = 404 if msg == "Voucher not found" else 400
        raise HTTPException(status_code=code, detail=msg) from exc
