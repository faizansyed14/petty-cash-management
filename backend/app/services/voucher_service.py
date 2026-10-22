from datetime import date, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from dateutil import parser as date_parser
from sqlalchemy.orm import Session, joinedload

from app.db.models.department import Department
from app.db.models.distribution import DistributionLine
from app.db.models.employee import Employee
from app.db.models.voucher import Voucher, VoucherStatus, SettlementType
from app.schemas.voucher import VoucherCreate, VoucherDraft, VoucherUpdate
from app.services import physical_cash_service
from app.services.extraction_service import extract_vouchers_from_file


def normalize_voucher_date(raw: str | None) -> str:
    """Convert extracted date strings (e.g. 'Aug 24 2026 4:08PM') to yyyy-mm-dd for date inputs."""
    if not raw or not str(raw).strip():
        return ""
    text = str(raw).strip()
    try:
        return date_parser.parse(text).date().isoformat()
    except (ValueError, OverflowError, TypeError):
        return text


def map_extraction_to_draft(raw: dict, source_file_url: str = "") -> VoucherDraft:
    amount = str(raw.get("Amount") or raw.get("Total AED") or "")
    total = str(raw.get("Total AED") or amount)
    return VoucherDraft(
        voucher_no=raw.get("Voucher No") or "",
        voucher_date=normalize_voucher_date(raw.get("Voucher Date") or ""),
        employee_code=raw.get("Employee ID") or "",
        employee_name=raw.get("Employee Name") or "",
        department_label=raw.get("Department") or "",
        classification=raw.get("Classification") or "",
        details=raw.get("Claim Details") or "",
        amount=amount,
        total_amount=total,
        currency="AED",
        extraction_source=raw.get("Source") or "",
        extracted_raw=raw,
    )


def _mark_existing(db: Session | None, draft: VoucherDraft) -> VoucherDraft:
    if db is not None and draft.voucher_no:
        existing = db.query(Voucher).filter(Voucher.voucher_no == draft.voucher_no).first()
        if existing:
            draft.already_exists = True
            draft.existing_voucher_id = str(existing.id)
    return draft


def extract_and_map_many(
    file_path: str, source_file_url: str = "", db: Session | None = None
) -> list[VoucherDraft]:
    rows = extract_vouchers_from_file(file_path)
    return [_mark_existing(db, map_extraction_to_draft(raw, "")) for raw in rows]


def extract_and_map(file_path: str, source_file_url: str = "", db: Session | None = None) -> VoucherDraft:
    drafts = extract_and_map_many(file_path, source_file_url, db=db)
    return drafts[0]


def extract_from_bytes(filename: str, content: bytes, db: Session | None = None) -> list[VoucherDraft]:
    """Extract one or many OPV vouchers from a temp file — nothing stored under /uploads."""
    suffix = Path(filename).suffix or ".pdf"
    tmp_path: str | None = None
    try:
        with NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        return extract_and_map_many(tmp_path, "", db=db)
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)


def _get_or_create_department(db: Session, label: str) -> Department:
    code = label.split()[0] if label else "UNK"
    name = label or "Unknown"
    dept = db.query(Department).filter(Department.code == code).first()
    if dept:
        return dept
    dept = Department(code=code, name=name)
    db.add(dept)
    db.flush()
    return dept


def _get_or_create_employee(db: Session, code: str, name: str, dept_label: str) -> Employee:
    emp = db.query(Employee).filter(Employee.employee_code == code).first()
    if emp:
        if name and emp.name != name:
            emp.name = name
        return emp
    dept = _get_or_create_department(db, dept_label)
    emp = Employee(employee_code=code, name=name or code, department_id=dept.id)
    db.add(emp)
    db.flush()
    return emp


def _parse_voucher_date(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return value
    return date_parser.parse(str(value))


def create_voucher(db: Session, payload: VoucherCreate) -> Voucher:
    existing = db.query(Voucher).filter(Voucher.voucher_no == payload.voucher_no).first()
    if existing:
        raise ValueError(
            f"Voucher {payload.voucher_no} already exists "
            f"(saved {existing.voucher_date.date().isoformat()}, status {existing.status.value}). "
            f"Each voucher number can only be saved once — open it from the Vouchers list, "
            f"or delete it first if you need to re-import."
        )

    employee = _get_or_create_employee(
        db, payload.employee_code, payload.employee_name, payload.department_label
    )

    voucher = Voucher(
        voucher_no=payload.voucher_no,
        voucher_date=_parse_voucher_date(payload.voucher_date),
        employee_id=employee.id,
        department_label=payload.department_label,
        total_amount=payload.total_amount,
        currency=payload.currency,
        classification=(payload.classification or "").strip(),
        details=(payload.details or "").strip(),
        extraction_source=payload.extraction_source,
        extracted_raw=payload.extracted_raw,
        status=payload.status or VoucherStatus.VERIFIED,
    )
    db.add(voucher)
    db.commit()
    db.refresh(voucher)
    return (
        db.query(Voucher)
        .options(joinedload(Voucher.employee))
        .filter(Voucher.id == voucher.id)
        .one()
    )


def list_vouchers(
    db: Session,
    month: int | None = None,
    year: int | None = None,
    status: VoucherStatus | None = None,
    statuses: list[VoucherStatus] | None = None,
    search: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Voucher], int]:
    q = db.query(Voucher).options(joinedload(Voucher.employee))
    if date_from:
        q = q.filter(Voucher.settlement_date >= date_from)
    if date_to:
        q = q.filter(Voucher.settlement_date <= date_to)
    if month and year:
        start = datetime(year, month, 1)
        end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
        q = q.filter(Voucher.voucher_date >= start, Voucher.voucher_date < end)
    if statuses:
        q = q.filter(Voucher.status.in_(statuses))
    elif status:
        q = q.filter(Voucher.status == status)
    if search:
        like = f"%{search}%"
        q = q.outerjoin(Employee).filter(
            (Voucher.voucher_no.ilike(like))
            | (Voucher.department_label.ilike(like))
            | (Voucher.details.ilike(like))
            | (Employee.name.ilike(like))
            | (Employee.employee_code.ilike(like))
        )
    total = q.count()
    items = q.order_by(Voucher.voucher_date.desc()).offset(skip).limit(limit).all()
    return items, total


def get_voucher(db: Session, voucher_id) -> Voucher | None:
    return (
        db.query(Voucher)
        .options(joinedload(Voucher.employee))
        .filter(Voucher.id == voucher_id)
        .first()
    )


def _refund_last_distribution(db: Session, voucher_id) -> None:
    """Return the notes/coins handed out for this voucher's last (un-reversed)
    distribution line back into Physical Cash, and mark that line reversed
    so it can't be refunded twice."""
    line = (
        db.query(DistributionLine)
        .filter(DistributionLine.voucher_id == voucher_id, DistributionLine.reversed_at.is_(None))
        .order_by(DistributionLine.created_at.desc())
        .first()
    )
    if not line:
        return
    physical_cash_service.add_counts(db, line.breakdown)
    line.reversed_at = datetime.utcnow()


def update_voucher(db: Session, voucher_id, payload: VoucherUpdate) -> Voucher:
    voucher = get_voucher(db, voucher_id)
    if not voucher:
        raise ValueError("Voucher not found")

    data = payload.model_dump(exclude_unset=True)
    clear = data.pop("clear_settlement", False)

    if "file_number" in data:
        voucher.file_number = data["file_number"]

    if "status" in data and data["status"]:
        new_status = VoucherStatus(data["status"])
        if new_status == VoucherStatus.PENDING_PAYMENT and voucher.status == VoucherStatus.PAID:
            _refund_last_distribution(db, voucher.id)
        voucher.status = new_status

    if clear:
        voucher.settlement_type = None
        voucher.bank_name = None
        voucher.settlement_date = None
    else:
        if "settlement_type" in data:
            st = data["settlement_type"]
            voucher.settlement_type = st
            if st == SettlementType.CASH_COLLECTION:
                voucher.bank_name = None
            elif st is None:
                voucher.bank_name = None
        if "bank_name" in data and voucher.settlement_type == SettlementType.DEPOSITED:
            voucher.bank_name = data["bank_name"]
        if "settlement_date" in data:
            voucher.settlement_date = data["settlement_date"]

        if voucher.settlement_type == SettlementType.DEPOSITED and not voucher.bank_name:
            raise ValueError("Select a UAE bank when settlement is Deposited")

    db.commit()
    return get_voucher(db, voucher_id)  # type: ignore[return-value]


def delete_voucher(db: Session, voucher_id) -> None:
    from app.db.models.distribution import DistributionLine

    voucher = get_voucher(db, voucher_id)
    if not voucher:
        raise ValueError("Voucher not found")

    if voucher.status == VoucherStatus.RECONCILED:
        raise ValueError("Cannot delete a reconciled voucher")

    db.query(DistributionLine).filter(DistributionLine.voucher_id == voucher.id).delete()

    db.delete(voucher)
    db.commit()
