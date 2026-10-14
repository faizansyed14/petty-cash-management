"""Deterministic petty cash voucher extraction — PDF text layer only. No OCR."""

import re

import fitz

# Real OPV form: "Voucher No : OPV…"
VOUCHER_NO_RE = re.compile(r"Voucher\s*No\s*:\s*([A-Z0-9\-]+)", re.IGNORECASE)
# APV / payment sheets (different form — skip)
APV_MARKER_RE = re.compile(r"\bReq\s*Num\b|\bAPV\d+\b", re.IGNORECASE)
PETTY_HEADER_RE = re.compile(r"PETTY\s*CASH\s*VOUCHER", re.IGNORECASE)


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


def find_value(text: str, pattern: str) -> str:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def is_opv_petty_cash_page(text: str) -> bool:
    """True only for printable OPV petty-cash forms (not APV sheets / blank / scanned)."""
    if len(text.strip()) < 40:
        return False
    if not VOUCHER_NO_RE.search(text):
        return False
    # Prefer pages that look like the online PrintPettyCash form
    if PETTY_HEADER_RE.search(text):
        return True
    # Still accept if clear Voucher No + Employee + Department
    return bool(
        re.search(r"Employee\s*:", text, re.IGNORECASE)
        and re.search(r"Department\s*:", text, re.IGNORECASE)
    )


def is_apv_or_other_sheet(text: str) -> bool:
    """APV payroll/payment sheets that say PETTY CASH but are not OPV forms."""
    if VOUCHER_NO_RE.search(text):
        return False
    return bool(APV_MARKER_RE.search(text))


def extract_voucher(text: str) -> dict:
    text = clean_text(text)
    result = {
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

    # Line item: "1" then classification (+ optional wrap) + details + amount
    claim_match = re.search(
        r"\n1\s*\n(.+?)\n([0-9,]+(?:\.[0-9]+)?)\s*(?=\nTotal|\nRemarks)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if claim_match:
        body_lines = [ln.strip() for ln in claim_match.group(1).split("\n") if ln.strip()]
        result["Amount"] = claim_match.group(2).strip()
        if len(body_lines) == 1:
            result["Classification"] = "OTHER"
            result["Claim Details"] = body_lines[0]
        elif len(body_lines) == 2:
            result["Classification"] = body_lines[0]
            result["Claim Details"] = body_lines[1]
        else:
            # e.g. TRAVEL AND / ACCOMMODATION / Travel cost…
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
            result["Amount"] = amount_match.group(1)

    # Total amount is often on its own line after "Aed :…"
    total_match = re.search(
        r"Total\s*\n?\s*Aed\s*:[^\n]*\n\s*([0-9,]+(?:\.[0-9]+)?)",
        text,
        re.IGNORECASE,
    )
    if total_match:
        result["Total AED"] = total_match.group(1).strip()
    else:
        total_match = re.search(
            r"Total\s*Aed\s*:[^0-9\n]*([0-9,]+(?:\.[0-9]+)?)", text, re.IGNORECASE
        )
        if total_match:
            result["Total AED"] = total_match.group(1).strip()

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
        # Prefer remarks as notes when claim details empty
        if not result["Claim Details"] and remarks:
            result["Claim Details"] = remarks

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


def extract_vouchers_from_file(file_path: str) -> list[dict]:
    """Extract all OPV petty-cash vouchers from a multi-page PDF.

    - Keeps pages with ``Voucher No : …`` (OPV form)
    - Skips APV / Req Num sheets and blank/scanned pages (no text layer)
    - No OCR
    """
    page_texts = extract_pdf_page_texts(file_path)
    if not page_texts:
        raise ValueError("Could not read PDF text — file may be scanned or unsupported")

    results: list[dict] = []
    seen: set[str] = set()

    for idx, page_text in enumerate(page_texts):
        if not page_text.strip():
            continue  # blank / scanned image page
        if is_apv_or_other_sheet(page_text):
            continue  # ignore APV payment sheets
        if not is_opv_petty_cash_page(page_text):
            continue

        data = extract_voucher(page_text)
        data["Source"] = "PDF Text Extraction"
        data["_page"] = idx + 1
        vn = (data.get("Voucher No") or "").strip().upper()
        if not vn:
            continue
        if vn in seen:
            continue
        seen.add(vn)
        results.append(data)

    if not results:
        # Whole-file fallback: single OPV pasted as one page of text
        full = clean_text("\n".join(page_texts))
        if is_opv_petty_cash_page(full) and not is_apv_or_other_sheet(full):
            data = extract_voucher(full)
            data["Source"] = "PDF Text Extraction"
            if data.get("Voucher No"):
                return [data]
        raise ValueError(
            "No petty cash vouchers found. "
            "Upload a PDF with OPV forms (Voucher No : OPV…). "
            "APV sheets, blank, or scanned pages are skipped."
        )

    return results


def extract_voucher_from_file(file_path: str) -> dict:
    """Backward-compatible: first voucher only."""
    rows = extract_vouchers_from_file(file_path)
    return rows[0]
