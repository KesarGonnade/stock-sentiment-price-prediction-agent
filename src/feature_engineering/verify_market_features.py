
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "processed"

STOCKS = [
    "tencent", "alibaba", "hsbc", "xiaomi", "byd",
    "samsung", "sk_hynix", "hyundai",
    "lg_energy_solution", "kakao"
]

REQUIRED_FEATURES = [
    "Price_Change",
    "Daily_Return_Pct",
    "SMA_5",
    "SMA_20",
    "Volatility_5",
    "Volume_Change_Pct"
]

total_records = 0
failed = []

print("=" * 65)
print("MARKET FEATURE VERIFICATION")
print("=" * 65)

for stock in STOCKS:

    filename = f"{stock}_market_features.csv"
    path = DATA_DIR / filename

    if not path.exists():
        print(f"\nMISSING FILE: {filename}")
        failed.append(stock)
        continue

    with open(path, "r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    total_records += len(rows)

    invalid_values = 0

    for row in rows:

        for feature in REQUIRED_FEATURES:

            value = row.get(feature, "").strip()

            if value:
                try:
                    float(value)
                except ValueError:
                    invalid_values += 1

    print(f"\nStock: {stock}")
    print("Records:", len(rows))
    print("Invalid feature values:", invalid_values)

    if len(rows) == 0 or invalid_values > 0:
        failed.append(stock)

print("\n" + "=" * 65)
print("FINAL SUMMARY")
print("=" * 65)

print("Stocks expected:", len(STOCKS))
print("Total records:", total_records)
print("Stocks needing attention:", len(set(failed)))

if not failed and total_records > 0:
    print("STATUS: PASSED")
else:
    print("STATUS: NEEDS ATTENTION")
