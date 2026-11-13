
import csv
from pathlib import Path
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "processed" / "sentiment_analysis_results.csv"
MARKET_DIR = BASE_DIR / "data" / "processed"
OUTPUT_FILE = MARKET_DIR / "daily_sentiment_aggregated.csv"

TIMEZONES = {
    "HK": ZoneInfo("Asia/Hong_Kong"),
    "KS": ZoneInfo("Asia/Seoul")
}

# Conservative daily cutoff.
# Sentiment after this time is assigned to the next trading session.
MARKET_CUTOFF = {
    "HK": time(16, 0),
    "KS": time(15, 30)
}


def safe_number(value):
    try:
        return float(value) if value else 0.0
    except (ValueError, TypeError):
        return 0.0


def load_market_dates():
    """Load actual available trading dates for each ticker."""
    market_dates = defaultdict(list)

    for path in MARKET_DIR.glob("*_market_features.csv"):
        with open(path, "r", encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                market_dates[row["Ticker"]].append(row["Date"])

    for ticker in market_dates:
        market_dates[ticker] = sorted(set(market_dates[ticker]))

    return market_dates


def assign_session(timestamp, ticker, market_dates):
    """Assign sentiment to the next eligible trading session."""
    dt = datetime.fromisoformat(
        timestamp.strip().replace("Z", "+00:00")
    )

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))

    exchange = "HK" if ticker.endswith(".HK") else "KS"
    local_dt = dt.astimezone(TIMEZONES[exchange])

    cutoff = MARKET_CUTOFF[exchange]

    # After-close sentiment cannot belong to that day's session.
    if local_dt.time() > cutoff:
        local_dt = local_dt + timedelta(days=1)

    eligible_dates = [
        date for date in market_dates.get(ticker, [])
        if date >= local_dt.strftime("%Y-%m-%d")
    ]

    return eligible_dates[0] if eligible_dates else None


def main():
    market_dates = load_market_dates()
    groups = defaultdict(list)

    completed = 0
    excluded = 0
    invalid = 0
    no_session = 0

    with open(INPUT_FILE, "r", encoding="utf-8-sig", newline="") as file:
        for record in csv.DictReader(file):

            if record.get("sentiment_status") != "completed":
                excluded += 1
                continue

            if record.get("sentiment") not in {
                "positive", "negative", "neutral"
            }:
                excluded += 1
                continue

            try:
                ticker = record["ticker"]

                session_date = assign_session(
                    record["published_at"],
                    ticker,
                    market_dates
                )

                if session_date is None:
                    no_session += 1
                    continue

                groups[(ticker, session_date)].append(record)
                completed += 1

            except Exception as error:
                invalid += 1
                print("Skipped:", record.get("record_id"), error)

    columns = [
        "Date", "Ticker", "Stock_Name", "Exchange",
        "Total_Mentions", "Social_Mentions", "News_Mentions",
        "Positive_Count", "Negative_Count", "Neutral_Count",
        "Average_Sentiment_Score", "Net_Sentiment_Score",
        "Total_Likes", "Total_Views", "Total_Reactions", "Sources"
    ]

    with open(OUTPUT_FILE, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()

        for (ticker, date), records in sorted(groups.items()):
            positive = sum(r["sentiment"] == "positive" for r in records)
            negative = sum(r["sentiment"] == "negative" for r in records)
            neutral = sum(r["sentiment"] == "neutral" for r in records)

            scores = [safe_number(r["sentiment_score"]) for r in records]

            social = [r for r in records if r["source"].lower() != "exa"]
            news = [r for r in records if r["source"].lower() == "exa"]

            writer.writerow({
                "Date": date,
                "Ticker": ticker,
                "Stock_Name": records[0]["stock_name"],
                "Exchange": records[0]["exchange"],
                "Total_Mentions": len(records),
                "Social_Mentions": len(social),
                "News_Mentions": len(news),
                "Positive_Count": positive,
                "Negative_Count": negative,
                "Neutral_Count": neutral,
                "Average_Sentiment_Score": round(
                    sum(scores) / len(scores), 4
                ),
                "Net_Sentiment_Score": sum(scores),
                "Total_Likes": sum(safe_number(r.get("likes")) for r in records),
                "Total_Views": sum(safe_number(r.get("views")) for r in records),
                "Total_Reactions": sum(
                    safe_number(r.get("reactions_total")) for r in records
                ),
                "Sources": ", ".join(sorted({r["source"] for r in records}))
            })

    print("\nSESSION-ALIGNED SENTIMENT AGGREGATION")
    print("-------------------------------------")
    print("Completed records assigned:", completed)
    print("Excluded records:", excluded)
    print("Invalid records:", invalid)
    print("Records without a future market session:", no_session)
    print("Daily stock-session groups:", len(groups))
    print("Saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
