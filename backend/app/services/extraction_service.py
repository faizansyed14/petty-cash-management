"""Deterministic voucher extraction — PDF text layer only. No OCR.

Supports:
- OPV petty-cash forms (``Voucher No : OPV…``)
- APV payment sheets (``APV…`` / ``Req Num``) mapped into the same fields
"""

from __future__ import annotations

import re

import fitz

VOUCHER_NO_RE = re.compile(r"Voucher\s*No\s*:\s*([A-Z0-9\-]+)", re.IGNORECASE)
APV_NO_RE = re.compile(r"\b(APV\d+)\b", re.IGNORECASE)
PETTY_HEADER_RE = re.compile(r"PETTY\s*CASH\s*VOUCHER", re.IGNORECASE)
MONEY_RE = re.compile(r"([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)")


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


def find_value(text: str, pattern: str) -> str:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _empty_result() -> dict:
    return {
        "Voucher No": "",
        "Voucher Date": "",
        "Employee ID": "",
        "Employee Name": "",
        "Department": "",
        "Classification": "",
        "Claim Details": "",
        "Amount": "",
        "Total AED": "",
        "Remarks": "",
        "Claimed By": "",
        "Division Manager": "",
        "Approved By": "",
        "Source": "PDF Text Extraction",
    }


def _normalize_money(raw: str) -> str:
    return raw.replace(",", "").strip()


def is_opv_petty_cash_page(text: str) -> bool:
    if len(text.strip()) < 40:
        return False
    if not VOUCHER_NO_RE.search(text):
        return False
    if PETTY_HEADER_RE.search(text):
        return True
    return bool(
        re.search(r"Employee\s*:", text, re.IGNORECASE)
        and re.search(r"Department\s*:", text, re.IGNORECASE)
    )


def is_apv_page(text: str) -> bool:
    """APV / Req Num sheets (not OPV forms)."""
    if VOUCHER_NO_RE.search(text):
        return False
    if APV_NO_RE.search(text) and re.search(r"Req\s*Num", text, re.IGNORECASE):
        return True
    return bool(APV_NO_RE.search(text) and re.search(r"\bDivision\b", text, re.IGNORECASE))


def extract_voucher(text: str) -> dict:
    """Extract classic OPV petty-cash form."""
    text = clean_text(text)
    result = _empty_result()

    result["Voucher No"] = find_value(text, r"Voucher\s*No\s*:\s*([A-Z0-9\-]+)")
    result["Voucher Date"] = find_value(
        text,
        r"Voucher\s*Date\s*:\s*(.+?)(?=\s*\n?\s*Employee\s*:|\s*\n\s*Department\s*:|$)",
    )
    if not result["Voucher Date"]:
        result["Voucher Date"] = find_value(
            text,
            r"Voucher\s*Date\s*:\s*([A-Za-z]{3}\s+\d{1,2}\s+\d{4}(?:\s+\d{1,2}:\d{2}\s*[APap][Mm])?)",
        )

    employee_match = re.search(
        r"Employee\s*:\s*([A-Z0-9]+)\s+(.+?)(?=\nDepartment)", text, re.IGNORECASE
    )
    if employee_match:
        result["Employee ID"] = employee_match.group(1).strip()
        result["Employee Name"] = re.sub(r"\s+", " ", employee_match.group(2)).strip()

    result["Department"] = find_value(
        text, r"Department\s*:\s*(.+?)(?=\nSl\s*#|\nClassification)"
    )

    claim_match = re.search(
        r"\n1\s*\n(.+?)\n([0-9,]+(?:\.[0-9]+)?)\s*(?=\nTotal|\nRemarks)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if claim_match:
        body_lines = [ln.strip() for ln in claim_match.group(1).split("\n") if ln.strip()]
        result["Amount"] = _normalize_money(claim_match.group(2))
        if len(body_lines) == 1:
            result["Classification"] = "OTHER"
            result["Claim Details"] = body_lines[0]
        elif len(body_lines) == 2:
            result["Classification"] = body_lines[0]
            result["Claim Details"] = body_lines[1]
        else:
            classification = body_lines[0]
            rest_start = 1
            if len(body_lines[1]) <= 25 and body_lines[1].upper() == body_lines[1]:
                classification = f"{body_lines[0]} {body_lines[1]}"
                rest_start = 2
            result["Classification"] = classification
            result["Claim Details"] = " ".join(body_lines[rest_start:])

    if not result["Amount"]:
        amount_match = re.search(r"\n([0-9,]+(?:\.[0-9]+)?)\s*\nTotal", text, re.IGNORECASE)
        if amount_match:
            result["Amount"] = _normalize_money(amount_match.group(1))

    total_match = re.search(
        r"Total\s*\n?\s*Aed\s*:[^\n]*\n\s*([0-9,]+(?:\.[0-9]+)?)",
        text,
        re.IGNORECASE,
    )
    if total_match:
        result["Total AED"] = _normalize_money(total_match.group(1))
    else:
        total_match = re.search(
            r"Total\s*Aed\s*:[^0-9\n]*([0-9,]+(?:\.[0-9]+)?)", text, re.IGNORECASE
        )
        if total_match:
            result["Total AED"] = _normalize_money(total_match.group(1))

    if not result["Total AED"] and result["Amount"]:
        result["Total AED"] = result["Amount"]

    remarks_match = re.search(
        r"Remarks\s*:?\s*\n?(.*?)(?=\n_{3,}|\nClaimed By|\nDivision Manager|\nApproved By|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if remarks_match:
        remarks = remarks_match.group(1).strip()
        remarks = re.sub(r"_+", "", remarks).strip()
        remarks = re.sub(r"\s+", " ", remarks).strip()
        result["Remarks"] = remarks
        if not result["Claim Details"] and remarks:
            result["Claim Details"] = remarks

    return result


def extract_apv(text: str) -> dict:
    """Extract APV payment sheet into the same voucher field shape.

    Mapping (W39 layout — labels often sit *below* values):
    - Req Num / APV… → Voucher No
    - Date value → Voucher Date
    - Employee id (split lines) + name → Employee ID / Name
    - Division code + name → Department (e.g. ``51 Recruitment``)
    - Classification block → Classification + Claim Details
    - Amount / Total → Amount / Total AED
    """
    text = clean_text(text)
    result = _empty_result()
    result["Source"] = "PDF Text Extraction (APV)"

    apv = APV_NO_RE.search(text)
    if apv:
        result["Voucher No"] = apv.group(1).upper()

    date_match = re.search(
        r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s*\n\s*Date",
        text,
        re.IGNORECASE,
    )
    if date_match:
        result["Voucher Date"] = date_match.group(1).strip()

    # E25069\n72\nEmployee\nNAME…\n51\nDivision
    emp_match = re.search(
        r"(E\d+)\s*\n\s*(\d{2})\s*\n\s*Employee\s*\n"
        r"(.+?)\s*\n\s*(\d{2})\s*\n\s*Division\s*\n"
        r"(.+?)(?=\nNo\.\s*of Docs|\nS\.\s*No\.|\nPayroll|\nClassification)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if emp_match:
        result["Employee ID"] = f"{emp_match.group(1).strip()}{emp_match.group(2).strip()}"
        name = re.sub(r"\s+", " ", emp_match.group(3)).strip()
        result["Employee Name"] = name
        div_code = emp_match.group(4).strip()
        div_name = re.sub(r"\s+", " ", emp_match.group(5)).strip()
        # Prefer "51 Recruitment" style
        if re.search(r"recruit", div_name, re.IGNORECASE):
            result["Department"] = f"{div_code} Recruitment"
        else:
            result["Department"] = f"{div_code} {div_name}".strip()

    # Values sit above labels: "Payroll Related payments" then Classification, then claim text
    class_match = re.search(
        r"S\.\s*No\.\s*\n(.+?)\nClassification\s*\n(.+?)\nClaim Details",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if class_match:
        classification = re.sub(r"\s+", " ", class_match.group(1)).strip()
        details = re.sub(r"\s+", " ", class_match.group(2)).strip()
        result["Classification"] = classification
        result["Claim Details"] = details

    # Amount line above "Amount" label; Total above/near "Total :"
    amount_match = re.search(
        r"([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*\n\s*Amount\b",
        text,
        re.IGNORECASE,
    )
    if amount_match:
        result["Amount"] = _normalize_money(amount_match.group(1))

    total_match = re.search(
        r"([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*\n\s*Total\s*:",
        text,
        re.IGNORECASE,
    )
    if total_match:
        result["Total AED"] = _normalize_money(total_match.group(1))
    elif result["Amount"]:
        result["Total AED"] = result["Amount"]

    notes_match = re.search(
        r"Notes\s*:\s*(.+?)(?=\nEmployee\b|\nRemarks\b|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if notes_match:
        notes = re.sub(r"\s+", " ", notes_match.group(1)).strip()
        result["Remarks"] = notes
        if not result["Claim Details"]:
            result["Claim Details"] = notes

    return result


def extract_pdf_page_texts(file_path: str) -> list[str]:
    pages: list[str] = []
    try:
        doc = fitz.open(file_path)
        for page in doc:
            pages.append(clean_text(page.get_text("text") or ""))
        doc.close()
    except Exception as e:
        print("PDF page text extraction error:", e)
    return pages


def extract_pdf_text(file_path: str) -> str:
    return "\n".join(extract_pdf_page_texts(file_path))


def _append_unique(results: list[dict], seen: set[str], data: dict, page: int) -> None:
    data = dict(data)
    data["_page"] = page
    vn = (data.get("Voucher No") or "").strip().upper()
    if not vn or vn in seen:
        return
    # Require at least amount or employee to count as usable
    if not (data.get("Total AED") or data.get("Amount") or data.get("Employee ID")):
        return
    seen.add(vn)
    results.append(data)


def extract_vouchers_from_file(file_path: str) -> list[dict]:
    """Extract OPV + APV vouchers from a multi-page PDF. Skip blank/scanned pages."""
    page_texts = extract_pdf_page_texts(file_path)
    if not page_texts:
        raise ValueError("Could not read PDF text — file may be scanned or unsupported")

    results: list[dict] = []
    seen: set[str] = set()

    for idx, page_text in enumerate(page_texts):
        if not page_text.strip():
            continue
        page_no = idx + 1

        if is_opv_petty_cash_page(page_text):
            data = extract_voucher(page_text)
            data["Source"] = "PDF Text Extraction"
            _append_unique(results, seen, data, page_no)
            continue

        if is_apv_page(page_text):
            data = extract_apv(page_text)
            _append_unique(results, seen, data, page_no)
            continue

    if not results:
        full = clean_text("\n".join(page_texts))
        if is_opv_petty_cash_page(full):
            data = extract_voucher(full)
            if data.get("Voucher No"):
                return [data]
        if is_apv_page(full):
            data = extract_apv(full)
            if data.get("Voucher No"):
                return [data]
        raise ValueError(
            "No vouchers found. "
            "Expected OPV (Voucher No : OPV…) and/or APV (Req Num / APV…) text pages. "
            "Blank or scanned pages are skipped."
        )

    return results


def extract_voucher_from_file(file_path: str) -> dict:
    rows = extract_vouchers_from_file(file_path)
    return rows[0]
