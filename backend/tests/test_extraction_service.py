from app.services.extraction_service import (
    extract_voucher,
    extract_apv,
    clean_text,
    extract_vouchers_from_file,
    is_opv_petty_cash_page,
    is_apv_page,
)


SAMPLE = """
PETTY CASH VOUCHER
Voucher No : OPV2600951        Voucher Date : Aug 24 2026 4:08PM
Employee : E2507184   SYED FAIZAN UDDIN
Department : 51 Recruitment

Sl# Classification Claim Information Details Amount
1
OTHER
claude subscription (21$)
81
Total   Aed: Eighty one                                   81

Remarks:
Claimed By ______   Division Manager ______   Approved By ______
"""

OPV_PAGE = """
PETTY CASH VOUCHER
Voucher No : OPV2601185       Voucher Date : Oct 5 2026 4:49PM
Employee : E0702713       ZAKARIA IBBINI
Department : 51 Recruitment
Sl #
Classification
Claim Information Details
Amount
1
OTHER
AIRSOFT TOY PISTOL AND RIFLE
2550.42
Total
Aed :Two thousand five hundred fifty
2550.42
Remarks
:
COST TO PROJECT PGC
_____________________
Claimed By
Division Manager
Approved By
"""

APV_PAGE = """
APV2600892
Req Num
13-10-2026
Date
E25069
72
Employee
YOUSSEF ABOU KHURJ
51
Division
ALPHA DATA
RECRUITMENT
No. of Docs Attached
1
S. No.
Payroll Related
payments
Classification
Sep Salary 21 - 30 Jamal
Claim Details
      10,333.33
Amount
ALPHA DATA  (L.L.C.)
      10,333.33
Total :
Notes :
SALARY PAYABLE ACCOUNT
"""


def test_extract_sample_voucher():
    data = extract_voucher(SAMPLE)
    assert data["Voucher No"] == "OPV2600951"
    assert "Aug 24 2026" in data["Voucher Date"]
    assert data["Employee ID"] == "E2507184"
    assert "FAIZAN" in data["Employee Name"]
    assert "Recruitment" in data["Department"]
    assert data["Classification"] == "OTHER"
    assert "claude" in data["Claim Details"].lower()
    assert data["Amount"] == "81" or data["Total AED"] == "81"
    assert data["Total AED"] == "81"


def test_normalize_voucher_date_from_voucher_text():
    from app.services.voucher_service import normalize_voucher_date, map_extraction_to_draft

    assert normalize_voucher_date("Aug 24 2026 4:08PM") == "2026-08-24"
    assert normalize_voucher_date("2026-08-24") == "2026-08-24"
    draft = map_extraction_to_draft(
        {
            "Voucher No": "OPV2600951",
            "Voucher Date": "Aug 24 2026 4:08PM",
            "Employee ID": "E2507184",
            "Employee Name": "SYED FAIZAN UDDIN",
            "Department": "51 Recruitment",
            "Classification": "OTHER",
            "Claim Details": "claude subscription (21$)",
            "Amount": "81",
            "Total AED": "81",
            "Remarks": "",
            "Source": "PDF Text Extraction",
        },
        "/uploads/x.pdf",
    )
    assert draft.voucher_date == "2026-08-24"
    assert draft.details == "claude subscription (21$)"
    assert draft.classification == "OTHER"


def test_extract_same_line_voucher_date():
    text = (
        "PETTY CASH VOUCHER\n"
        "Voucher No : OPV2600951        Voucher Date : Aug 24 2026 4:08PM\n"
        "Employee : E2507184   SYED FAIZAN UDDIN\n"
        "Department : 51 Recruitment\n"
    )
    data = extract_voucher(text)
    assert "Aug 24 2026" in data["Voucher Date"]


def test_clean_text_strips_blank_lines():
    cleaned = clean_text("a\n\n  b  \n\xa0c")
    assert "a" in cleaned
    assert "b" in cleaned


def test_extract_apv_fields():
    assert is_apv_page(APV_PAGE)
    assert not is_opv_petty_cash_page(APV_PAGE)
    data = extract_apv(APV_PAGE)
    assert data["Voucher No"] == "APV2600892"
    assert data["Employee ID"] == "E2506972"
    assert "YOUSSEF" in data["Employee Name"]
    assert data["Department"].startswith("51")
    assert "Payroll" in data["Classification"]
    assert data["Total AED"] == "10333.33"


def test_opv_page():
    assert is_opv_petty_cash_page(OPV_PAGE)
    data = extract_voucher(OPV_PAGE)
    assert data["Voucher No"] == "OPV2601185"
    assert data["Employee ID"] == "E0702713"
    assert "2550.42" in (data["Total AED"] or data["Amount"])


def test_w39_pdf_extracts_apv_and_opv():
    from pathlib import Path

    pdf = Path(__file__).resolve().parents[2] / "W39 VOUCHERS.pdf"
    if not pdf.exists():
        pdf = Path(__file__).resolve().parents[3] / "W39 VOUCHERS.pdf"
    if not pdf.exists():
        return
    rows = extract_vouchers_from_file(str(pdf))
    nos = [r["Voucher No"] for r in rows]
    assert "APV2600892" in nos
    assert "OPV2601185" in nos
    assert len(nos) == 11
    apv = next(r for r in rows if r["Voucher No"] == "APV2600892")
    assert apv["Employee ID"] == "E2506972"
    assert "Payroll" in apv["Classification"]
