
import csv
from pathlib import Path
from collections import defaultdict


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data" / "processed"

SENTIMENT_FILE = DATA_DIR / "daily_sentiment_aggregated.csv"

OUTPUT_FILE = DATA_DIR / "integrated_sentiment_market.csv"


def read_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def main():

    print("\nSENTIMENT + MARKET DATA INTEGRATION")
    print("----------------------------------")

    sentiment_rows = read_csv(SENTIMENT_FILE)

    # Load all market records
    market_by_ticker = defaultdict(list)

    market_files = list(DATA_DIR.glob("*_market_features.csv"))

    for path in market_files:
        rows = read_csv(path)

        for row in rows:
            market_by_ticker[row["Ticker"]].append(row)

    # Sort each stock's market data by date
    for ticker in market_by_ticker:
        market_by_ticker[ticker].sort(
            key=lambda row: row["Date"]
        )

    # Create date lookup and next-day price lookup
    market_lookup = {}
    next_close_lookup = {}

    for ticker, rows in market_by_ticker.items():

        for index, row in enumerate(rows):

            date = row["Date"]
            market_lookup[(ticker, date)] = row

            if index + 1 < len(rows):
                next_row = rows[index + 1]

                next_close_lookup[(ticker, date)] = (
                    next_row["Date"],
                    next_row["Close"]
                )

    output = []
    unmatched = 0
    missing_target = 0

    for sentiment in sentiment_rows:

        ticker = sentiment["Ticker"]
        date = sentiment["Date"]

        key = (ticker, date)

        if key not in market_lookup:
            unmatched += 1
            continue

        if key not in next_close_lookup:
            missing_target += 1
            continue

        market = market_lookup[key]

        next_date, next_close = next_close_lookup[key]

        record = {
            **sentiment,
            "Open": market["Open"],
            "High": market["High"],
            "Low": market["Low"],
            "Close": market["Close"],
            "Volume": market["Volume"],
            "Price_Change": market["Price_Change"],
            "Daily_Return_Pct": market["Daily_Return_Pct"],
            "SMA_5": market["SMA_5"],
            "SMA_20": market["SMA_20"],
            "Volatility_5": market["Volatility_5"],
            "Volume_Change_Pct": market["Volume_Change_Pct"],
            "Target_Date": next_date,
            "Target_Close_Next_Day": next_close
        }

        output.append(record)

    if output:

        columns = list(output[0].keys())

        with open(
            OUTPUT_FILE,
            "w",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=columns
            )

            writer.writeheader()
            writer.writerows(output)

    print("Sentiment groups:", len(sentiment_rows))
    print("Market files:", len(market_files))
    print("Matched records:", len(output))
    print("Unmatched sentiment dates:", unmatched)
    print("Missing next-day targets:", missing_target)
    print("\nSaved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
