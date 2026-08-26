"""Deterministic petty cash voucher extraction — PDF text layer + OCR fallback. No AI/LLM."""

import re

import fitz
import pytesseract
from PIL import Image


def extract_pdf_text(file_path: str) -> str:
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text("text") + "\n"
        doc.close()
    except Exception as e:
        print("PDF text extraction error:", e)
    return text


def extract_ocr_text(file_path: str) -> str:
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text += pytesseract.image_to_string(img, config="--psm 6") + "\n"
        doc.close()
    except Exception as e:
        print("OCR error:", e)
    return text


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


def find_value(text: str, pattern: str) -> str:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


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
    # Same-line layout: "Voucher No : X    Voucher Date : Aug 24 2026 4:08PM"
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
        result["Employee Name"] = employee_match.group(2).strip()

    result["Department"] = find_value(
        text, r"Department\s*:\s*(.+?)(?=\nSl\s*#|\nClassification)"
    )

    claim_match = re.search(
        r"(?:Sl\s*#\s*Classification\s*Claim Information Details\s*Amount\s*)?"
        r"\d+\s*\n"
        r"([A-Za-z][^\n]*)\n"
        r"(.+?)\n"
        r"([0-9,]+(?:\.[0-9]+)?)"
        r"(?=\nTotal|\nRemarks)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if claim_match:
        result["Classification"] = claim_match.group(1).strip()
        result["Claim Details"] = claim_match.group(2).strip()
        result["Amount"] = claim_match.group(3).strip()

    if not result["Amount"]:
        amount_match = re.search(r"\n([0-9,]+(?:\.[0-9]+)?)\s*\nTotal", text, re.IGNORECASE)
        if amount_match:
            result["Amount"] = amount_match.group(1)

    total_match = re.search(
        r"Total\s*Aed\s*:[^0-9\n]*([0-9,]+(?:\.[0-9]+)?)", text, re.IGNORECASE
    )
    if total_match:
        result["Total AED"] = total_match.group(1)
    else:
        total_match = re.search(
            r"Total\s*Aed\s*:[^\n]*\n\s*([0-9,]+(?:\.[0-9]+)?)", text, re.IGNORECASE
        )
        if total_match:
            result["Total AED"] = total_match.group(1)

    if not result["Total AED"] and result["Amount"]:
        result["Total AED"] = result["Amount"]

    remarks_match = re.search(
        r"Remarks\s*:\s*(.*?)(?=\nClaimed By|\nDivision Manager|\nApproved By|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if remarks_match:
        result["Remarks"] = re.sub(r"_+", "", remarks_match.group(1).strip()).strip()

    return result


def extract_voucher_from_file(file_path: str) -> dict:
    """Single entry point the FastAPI route calls."""
    text = clean_text(extract_pdf_text(file_path))

    if len(text.strip()) < 50:
        text = extract_ocr_text(file_path)
        source = "OCR"
    else:
        source = "PDF Text Extraction"

    data = extract_voucher(text)
    data["Source"] = source
    return data
