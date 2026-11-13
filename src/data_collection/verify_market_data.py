
import csv
import os

FOLDER = "data/raw"

FILES = [
    "tencent_market_raw.csv",
    "alibaba_market_raw.csv",
    "hsbc_market_raw.csv",
    "xiaomi_market_raw.csv",
    "byd_market_raw.csv",
    "samsung_market_raw.csv",
    "sk_hynix_market_raw.csv",
    "hyundai_market_raw.csv",
    "lg_energy_solution_market_raw.csv",
    "kakao_market_raw.csv"
]

REQUIRED_COLUMNS = [
    "Open", "High", "Low", "Close", "Volume"
]

total_records = 0
total_missing = 0

print("=" * 65)
print("HISTORICAL MARKET DATA VERIFICATION")
print("=" * 65)

for filename in FILES:

    path = os.path.join(FOLDER, filename)

    if not os.path.exists(path):
        print(f"\n{filename}: FILE MISSING")
        continue

    with open(path, "r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    missing_count = 0

    for row in rows:
        for column in REQUIRED_COLUMNS:
            if not row.get(column, "").strip():
                missing_count += 1

    total_records += len(rows)
    total_missing += missing_count

    print(f"\n{filename}")
    print("Records:", len(rows))

    if rows:
        print("First date:", rows[0]["Date"])
        print("Last date:", rows[-1]["Date"])

    print("Missing values:", missing_count)

print("\n" + "=" * 65)
print("FINAL VERIFICATION")
print("=" * 65)

print("Total stocks:", len(FILES))
print("Total records:", total_records)
print("Total missing values:", total_missing)

if total_missing == 0 and total_records > 0:
    print("STATUS: PASSED")
else:
    print("STATUS: NEEDS ATTENTION")
