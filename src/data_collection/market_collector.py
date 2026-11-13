
import os
import csv
import requests

from datetime import datetime, timezone
from zoneinfo import ZoneInfo


# ==========================================
# CONFIGURATION
# ==========================================

OUTPUT_DIR = "data/raw"

# Six-month historical window
START_DATE = "2026-05-11"
END_DATE = "2026-11-17"  # Exclusive

STOCKS = {
    # Hong Kong stocks
    "tencent": "0700.HK",
    "alibaba": "9988.HK",
    "hsbc": "0005.HK",
    "xiaomi": "1810.HK",
    "byd": "1211.HK",

    # South Korean stocks
    "samsung": "005930.KS",
    "sk_hynix": "000660.KS",
    "hyundai": "005380.KS",
    "lg_energy_solution": "373220.KS",
    "kakao": "035720.KS"
}

REQUIRED_COLUMNS = [
    "Open",
    "High",
    "Low",
    "Close",
    "Volume"
]

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==========================================
# DOWNLOAD STOCK DATA
# ==========================================

def download_stock_data(company, ticker):

    start_timestamp = int(
        datetime.strptime(
            START_DATE, "%Y-%m-%d"
        ).replace(tzinfo=timezone.utc).timestamp()
    )

    end_timestamp = int(
        datetime.strptime(
            END_DATE, "%Y-%m-%d"
        ).replace(tzinfo=timezone.utc).timestamp()
    )

    url = (
        "https://query1.finance.yahoo.com/"
        f"v8/finance/chart/{ticker}"
    )

    params = {
        "period1": start_timestamp,
        "period2": end_timestamp,
        "interval": "1d"
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()
    chart = data.get("chart", {})

    if chart.get("error"):
        raise ValueError(chart["error"])

    results = chart.get("result")

    if not results:
        raise ValueError("No market data returned.")

    stock_data = results[0]

    timestamps = stock_data.get("timestamp", [])

    if not timestamps:
        raise ValueError("No trading timestamps returned.")

    quote = stock_data["indicators"]["quote"][0]

    timezone_name = stock_data["meta"].get(
        "exchangeTimezoneName", "UTC"
    )

    exchange_timezone = ZoneInfo(timezone_name)

    # ======================================
    # PROCESS RECORDS
    # ======================================

    records = []
    skipped_records = 0

    for index, timestamp in enumerate(timestamps):

        values = {}

        for column in REQUIRED_COLUMNS:

            column_values = quote.get(column.lower())

            value = (
                column_values[index]
                if column_values and index < len(column_values)
                else None
            )

            values[column] = value

        # Skip incomplete OHLCV records
        if any(
            value is None
            for value in values.values()
        ):

            skipped_records += 1

            date = datetime.fromtimestamp(
                timestamp,
                exchange_timezone
            ).strftime("%Y-%m-%d")

            print(
                f"Skipping incomplete record: "
                f"{ticker} on {date}"
            )

            continue

        date = datetime.fromtimestamp(
            timestamp,
            exchange_timezone
        ).strftime("%Y-%m-%d")

        record = {
            "Date": date,
            "Ticker": ticker,
            **values
        }

        records.append(record)

    # ======================================
    # REMOVE DUPLICATE DATES
    # ======================================

    unique_records = {}

    for record in records:
        unique_records[record["Date"]] = record

    records = sorted(
        unique_records.values(),
        key=lambda row: row["Date"]
    )

    duplicate_count = len(unique_records) - len(records)

    # ======================================
    # SAVE CSV
    # ======================================

    filename = os.path.join(
        OUTPUT_DIR,
        f"{company}_market_6months_raw.csv"
    )

    columns = [
        "Date",
        "Ticker",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"
    ]

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=columns
        )

        writer.writeheader()
        writer.writerows(records)

    return (
        len(records),
        skipped_records,
        duplicate_count,
        filename
    )


# ==========================================
# COLLECT ALL STOCKS
# ==========================================

def collect_market_data():

    successful = 0
    failed = []

    total_records = 0
    total_skipped = 0
    total_duplicates = 0

    print("=" * 60)
    print("SIX-MONTH HISTORICAL MARKET DATA COLLECTION")
    print("=" * 60)

    print(f"Start date: {START_DATE}")
    print(f"End date (exclusive): {END_DATE}")

    for company, ticker in STOCKS.items():

        print(f"\nDownloading {company} ({ticker})...")

        try:

            count, skipped, duplicates, filename = (
                download_stock_data(company, ticker)
            )

            if count == 0:
                print("No complete records available.")
                failed.append(company)
                continue

            print(f"Saved: {filename}")
            print(f"Complete records: {count}")
            print(f"Skipped incomplete records: {skipped}")
            print(f"Duplicate dates removed: {duplicates}")

            successful += 1
            total_records += count
            total_skipped += skipped
            total_duplicates += duplicates

        except Exception as error:

            print(f"Download failed: {error}")
            failed.append(company)

    # ======================================
    # FINAL SUMMARY
    # ======================================

    print("\n" + "=" * 60)
    print("COLLECTION SUMMARY")
    print("=" * 60)

    print(f"Total stocks: {len(STOCKS)}")
    print(f"Successful downloads: {successful}")
    print(f"Failed downloads: {len(failed)}")
    print(f"Complete records saved: {total_records}")
    print(f"Incomplete records skipped: {total_skipped}")
    print(f"Duplicate dates removed: {total_duplicates}")

    if failed:
        print("\nFailed stocks:")

        for company in failed:
            print("-", company)

    else:
        print("\nAll stocks downloaded successfully!")

    print("\nOutput folder:", OUTPUT_DIR)


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":
    collect_market_data()
