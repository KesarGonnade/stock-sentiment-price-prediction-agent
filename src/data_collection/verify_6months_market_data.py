
import csv
import os

FOLDER = "data/raw"

STOCKS = [
    "tencent",
    "alibaba",
    "hsbc",
    "xiaomi",
    "byd",
    "samsung",
    "sk_hynix",
    "hyundai",
    "lg_energy_solution",
    "kakao"
]

REQUIRED_COLUMNS = [
    "Date", "Ticker", "Open",
    "High", "Low", "Close", "Volume"
]

total_records = 0
total_missing = 0
total_duplicates = 0

print("=" * 65)
print("SIX-MONTH MARKET DATA VERIFICATION")
print("=" * 65)

for stock in STOCKS:

    filename = f"{stock}_market_6months_raw.csv"
    path = os.path.join(FOLDER, filename)

    if not os.path.exists(path):
        print(f"\n{filename}: FILE MISSING")
        continue

    with open(path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    missing = 0

    for row in rows:
        for column in REQUIRED_COLUMNS:
            if not row.get(column, "").strip():
                missing += 1

    dates = [row["Date"] for row in rows]
    duplicates = len(dates) - len(set(dates))

    total_records += len(rows)
    total_missing += missing
    total_duplicates += duplicates

    print(f"\n{filename}")
    print("Records:", len(rows))
    print("First date:", min(dates) if dates else "N/A")
    print("Last date:", max(dates) if dates else "N/A")
    print("Missing values:", missing)
    print("Duplicate dates:", duplicates)

print("\n" + "=" * 65)
print("FINAL SUMMARY")
print("=" * 65)

print("Stocks expected:", len(STOCKS))
print("Total records:", total_records)
print("Missing values:", total_missing)
print("Duplicate dates:", total_duplicates)

if (
    total_records > 0
    and total_missing == 0
    and total_duplicates == 0
):
    print("STATUS: PASSED")
else:
    print("STATUS: NEEDS ATTENTION")
