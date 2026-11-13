
import csv
import os
import statistics

from pathlib import Path
from collections import deque


# ==========================================
# CONFIGURATION
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

os.makedirs(OUTPUT_DIR, exist_ok=True)


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


# ==========================================
# FEATURE CALCULATION
# ==========================================

def calculate_features(company):

    input_file = RAW_DIR / f"{company}_market_6months_raw.csv"

    output_file = OUTPUT_DIR / f"{company}_market_features.csv"

    if not input_file.exists():
        raise FileNotFoundError(
            f"Market data not found: {input_file}"
        )

    # Read historical market data
    with open(
        input_file,
        "r",
        encoding="utf-8",
        newline=""
    ) as file:

        reader = csv.DictReader(file)
        records = list(reader)

    if not records:
        raise ValueError(f"No records found for {company}")

    # Sort records chronologically
    records.sort(key=lambda row: row["Date"])

    # Rolling windows
    close_window = deque(maxlen=20)
    return_window = deque(maxlen=5)

    previous_close = None
    previous_volume = None

    processed_records = []

    for row in records:

        close = float(row["Close"])
        volume = float(row["Volume"])

        # ----------------------------------
        # 1. DAILY PRICE CHANGE
        # ----------------------------------

        if previous_close is not None:
            price_change = close - previous_close
        else:
            price_change = None

        # ----------------------------------
        # 2. DAILY RETURN (%)
        # ----------------------------------

        if previous_close is not None and previous_close != 0:

            daily_return = (
                (close - previous_close)
                / previous_close
            ) * 100

            return_window.append(daily_return)

        else:
            daily_return = None

        # ----------------------------------
        # 3. SIMPLE MOVING AVERAGE (5 DAYS)
        # ----------------------------------

        close_window.append(close)

        sma_5 = None

        if len(close_window) >= 5:

            last_5 = list(close_window)[-5:]

            sma_5 = statistics.mean(last_5)

        # ----------------------------------
        # 4. SIMPLE MOVING AVERAGE (20 DAYS)
        # ----------------------------------

        sma_20 = None

        if len(close_window) >= 20:

            sma_20 = statistics.mean(close_window)

        # ----------------------------------
        # 5. VOLATILITY (5 DAYS)
        # ----------------------------------

        volatility_5 = None

        if len(return_window) == 5:

            volatility_5 = statistics.stdev(return_window)

        # ----------------------------------
        # 6. VOLUME CHANGE (%)
        # ----------------------------------

        if previous_volume is not None and previous_volume != 0:

            volume_change = (
                (volume - previous_volume)
                / previous_volume
            ) * 100

        else:
            volume_change = None

        # ----------------------------------
        # CREATE FEATURE RECORD
        # ----------------------------------

        feature_record = {
            "Date": row["Date"],
            "Ticker": row["Ticker"],
            "Open": row["Open"],
            "High": row["High"],
            "Low": row["Low"],
            "Close": row["Close"],
            "Volume": row["Volume"],
            "Price_Change": price_change,
            "Daily_Return_Pct": daily_return,
            "SMA_5": sma_5,
            "SMA_20": sma_20,
            "Volatility_5": volatility_5,
            "Volume_Change_Pct": volume_change
        }

        processed_records.append(feature_record)

        # Update previous values
        previous_close = close
        previous_volume = volume

    # ======================================
    # SAVE FEATURE DATASET
    # ======================================

    columns = [
        "Date",
        "Ticker",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "Price_Change",
        "Daily_Return_Pct",
        "SMA_5",
        "SMA_20",
        "Volatility_5",
        "Volume_Change_Pct"
    ]

    with open(
        output_file,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=columns
        )

        writer.writeheader()
        writer.writerows(processed_records)

    return len(processed_records), output_file


# ==========================================
# PROCESS ALL STOCKS
# ==========================================

def main():

    successful = 0
    failed = []

    total_records = 0

    print("=" * 65)
    print("MARKET DATA FEATURE ENGINEERING")
    print("=" * 65)

    for company in STOCKS:

        print(f"\nProcessing: {company}")

        try:

            count, output_file = calculate_features(company)

            print(f"Records processed: {count}")
            print(f"Saved: {output_file}")

            successful += 1
            total_records += count

        except Exception as error:

            print(f"Error: {error}")
            failed.append(company)

    # ======================================
    # FINAL SUMMARY
    # ======================================

    print("\n" + "=" * 65)
    print("FEATURE ENGINEERING SUMMARY")
    print("=" * 65)

    print(f"Total stocks: {len(STOCKS)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(failed)}")
    print(f"Total records processed: {total_records}")

    if failed:
        print("\nFailed stocks:")

        for company in failed:
            print("-", company)

    else:
        print("\nAll market features generated successfully!")


if __name__ == "__main__":
    main()
