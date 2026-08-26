from app.services.extraction_service import extract_voucher, clean_text


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
