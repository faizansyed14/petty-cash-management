# Petty Cash — simple cashier app

Upload voucher PDFs → review → save. Voucher register with **Deposited** (UAE bank) / **Cash Collection** + date. Export Excel matching ALPHA DATA RECRUITMENT sheet. Distribute cash by note counts.

## Run

```bash
# Backend
cd backend
.\.venv\Scripts\activate
$env:PYTHONPATH="."
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npx vite --host 127.0.0.1 --port 5173
```

Login: `admin` / `admin`

## App

| Page | What |
|------|------|
| **Dashboard** | Totals: physical cash, petty cash (all vouchers), paid out, left (unpaid) |
| **Vouchers** | Register: notes, deposited (UAE banks) / cash collection, date · preview/delete · **Export Excel** |
| **Upload** | Drop PDF → extract → save |
| **Physical cash** | Count each note/coin you hold · CRUD per denomination |
| **Distribute cash** | Pulls counts from Physical cash (no re-entry) → pick vouchers → hand out notes → confirm |

Excel columns: `S.NO | VOUCHER NO | NAME | AMOUNT | NOTES | DEPOSITED | CASH COLLECTION | DATE | FILE NUMBER`

Confirming a distribution automatically deducts the handed-out notes/coins from the Physical cash counts.
