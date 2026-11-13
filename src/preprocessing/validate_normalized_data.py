
import json
from pathlib import Path
from collections import Counter


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "normalized_sentiment_data.json"
)


EXPECTED_TICKERS = {
    "0700.HK",
    "9988.HK",
    "0005.HK",
    "1810.HK",
    "1211.HK",
    "005930.KS",
    "000660.KS",
    "005380.KS",
    "373220.KS",
    "035720.KS"
}


def main():

    print("=" * 60)
    print("NORMALIZED DATA VALIDATION")
    print("=" * 60)

    if not DATA_FILE.exists():
        print("ERROR: Normalized dataset not found.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        print("ERROR: Dataset must contain a JSON list.")
        return

    print("\nTotal records:", len(records))

    required_fields = [
        "record_id",
        "source",
        "stock_name",
        "ticker",
        "exchange",
        "text",
        "published_at",
        "language",
        "engagement",
        "relevance_status"
    ]

    missing_fields = Counter()
    missing_text = 0
    missing_timestamp = 0
    invalid_timestamps = 0
    missing_ticker = 0
    missing_ids = 0

    source_counts = Counter()
    ticker_counts = Counter()
    relevance_counts = Counter()
    record_ids = []

    for record in records:

        for field in required_fields:
            if field not in record:
                missing_fields[field] += 1

        if not record.get("text", "").strip():
            missing_text += 1

        if not record.get("published_at"):
            missing_timestamp += 1

        if not record.get("ticker"):
            missing_ticker += 1

        if not record.get("record_id"):
            missing_ids += 1
        else:
            record_ids.append(record["record_id"])

        source_counts[record.get("source", "Unknown")] += 1
        ticker_counts[record.get("ticker", "Unknown")] += 1
        relevance_counts[
            record.get("relevance_status", "Unknown")
        ] += 1

        # Check UTC timestamp format
        timestamp = record.get("published_at")

        if timestamp:
            try:
                from datetime import datetime

                parsed = datetime.fromisoformat(
                    timestamp.replace("Z", "+00:00")
                )

                if parsed.utcoffset() is None:
                    invalid_timestamps += 1

            except (ValueError, TypeError):
                invalid_timestamps += 1

    duplicate_ids = len(record_ids) - len(set(record_ids))

    print("\n--- Required Field Check ---")

    if missing_fields:
        for field, count in missing_fields.items():
            print(f"Missing {field}: {count}")
    else:
        print("All required fields are present.")

    print("\n--- Data Quality ---")
    print("Missing text:", missing_text)
    print("Missing timestamps:", missing_timestamp)
    print("Invalid timestamps:", invalid_timestamps)
    print("Missing tickers:", missing_ticker)
    print("Missing record IDs:", missing_ids)
    print("Duplicate record IDs:", duplicate_ids)

    print("\n--- Source Distribution ---")

    for source, count in sorted(source_counts.items()):
        print(f"{source}: {count}")

    print("\n--- Stock Distribution ---")

    for ticker, count in sorted(ticker_counts.items()):
        print(f"{ticker}: {count}")

    print("\n--- Relevance Status ---")

    for status, count in sorted(relevance_counts.items()):
        print(f"{status}: {count}")

    missing_stocks = EXPECTED_TICKERS - set(ticker_counts.keys())

    print("\n--- Coverage Check ---")

    if missing_stocks:
        print("Stocks without records:", sorted(missing_stocks))
    else:
        print("All 10 stocks have records.")

    print("\n--- Final Status ---")

    has_structural_errors = (
        bool(missing_fields)
        or missing_ids > 0
        or duplicate_ids > 0
        or missing_ticker > 0
    )

    if has_structural_errors:
        print("STATUS: ISSUES FOUND")
    else:
        print("STATUS: STRUCTURAL CHECK PASSED")

    print("\nNote: Missing timestamps and text quality")
    print("need separate review before sentiment analysis.")


if __name__ == "__main__":
    main()
