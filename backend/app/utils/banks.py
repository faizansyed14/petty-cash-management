UAE_BANKS = [
    "ADCB",
    "ADIB",
    "Ajman Bank",
    "Al Ansari",
    "Al Fardan",
    "Al Hilal",
    "Al Jazira",
    "Bank of Sharjah",
    "CBD",
    "Dubai Bank",
    "DIB",
    "Emirates Islamic",
    "ENBD",
    "FAB",
    "HSBC",
    "Lulu",
    "Mashreq",
    "National Bank of Fujairah",
    "RAKBANK",
    "Sharjah Islamic Bank",
    "Standard Chartered UAE",
    "United Arab Bank",
]

# Map legacy long labels → short codes (existing rows)
BANK_NAME_ALIASES = {
    "Abu Dhabi Commercial Bank (ADCB)": "ADCB",
    "Abu Dhabi Islamic Bank (ADIB)": "ADIB",
    "Ajman Bank": "Ajman",
    "Al Ansari Exchange": "Al Ansari",
    "Al Fardan Exchange": "Al Fardan",
    "Al Hilal Bank": "Al Hilal",
    "Al Jazira Exchange": "Al Jazira",
    "Commercial Bank of Dubai (CBD)": "CBD",
    "Dubai Islamic Bank (DIB)": "DIB",
    "Emirates NBD": "ENBD",
    "First Abu Dhabi Bank (FAB)": "FAB",
    "HSBC UAE": "HSBC",
    "Lulu Exchange": "Lulu",
    "Mashreq Bank": "Mashreq",
    "National Bank of Fujairah": "NBF",
    "Sharjah Islamic Bank": "SIB",
    "Standard Chartered UAE": "SC",
    "United Arab Bank": "UAB",
}


def normalize_bank_name(name: str | None) -> str | None:
    if name is None:
        return None
    text = str(name).strip()
    if not text:
        return None
    if text in UAE_BANKS:
        return text
    return BANK_NAME_ALIASES.get(text, text)
