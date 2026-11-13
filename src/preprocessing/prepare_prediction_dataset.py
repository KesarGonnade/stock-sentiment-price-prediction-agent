
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "processed"

INPUT_FILE = DATA_DIR / "integrated_sentiment_market.csv"
OUTPUT_FILE = DATA_DIR / "prediction_dataset.csv"
REJECTED_FILE = DATA_DIR / "prediction_dataset_rejected.csv"

def to_float(value):
    if value is None or value.strip() == "":
        raise ValueError("Missing numeric value")
    return float(value)

def main():

    if not INPUT_FILE.exists():
        print("Integrated dataset not found:", INPUT_FILE)
        return

    features = [
        "Daily_Return_Pct",
        "SMA_5",
        "SMA_20",
        "Volatility_5",
        "Volume_Change_Pct",
        "Average_Sentiment_Score",
        "Net_Sentiment_Score",
        "Total_Mentions",
        "Social_Mentions",
        "News_Mentions"
    ]

    output_columns = [
        "Date",
        "Target_Date",
        "Ticker",
        "Stock_Name",
        "Exchange",
        "Close",
        "Daily_Return_Pct",
        "Close_vs_SMA5_Pct",
        "Close_vs_SMA20_Pct",
        "Volatility_5",
        "Volume_Change_Pct",
        "Average_Sentiment_Score",
        "Net_Sentiment_Score",
        "Total_Mentions",
        "Social_Mentions",
        "News_Mentions",
        "Target_Close_Next_Day",
        "Target_Return_Pct"
    ]

    valid_records = []
    rejected_records = []

    with open(INPUT_FILE, "r", encoding="utf-8-sig", newline="") as file:

        reader = csv.DictReader(file)

        for row in reader:

            try:
                current_close = to_float(row["Close"])
                next_close = to_float(row["Target_Close_Next_Day"])

                if current_close <= 0 or next_close <= 0:
                    raise ValueError("Invalid closing price")

                if row["Target_Date"] <= row["Date"]:
                    raise ValueError("Target date must be after current date")

                values = {
                    feature: to_float(row[feature])
                    for feature in features
                }

                sma_5 = values["SMA_5"]
                sma_20 = values["SMA_20"]

                if sma_5 <= 0 or sma_20 <= 0:
                    raise ValueError("Invalid moving average")

                close_vs_sma5 = (
                    (current_close - sma_5) / sma_5
                ) * 100

                close_vs_sma20 = (
                    (current_close - sma_20) / sma_20
                ) * 100

                target_return = (
                    (next_close - current_close) / current_close
                ) * 100

                record = {
                    "Date": row["Date"],
                    "Target_Date": row["Target_Date"],
                    "Ticker": row["Ticker"],
                    "Stock_Name": row["Stock_Name"],
                    "Exchange": row["Exchange"],
                    "Close": current_close,
                    "Daily_Return_Pct": values["Daily_Return_Pct"],
                    "Close_vs_SMA5_Pct": close_vs_sma5,
                    "Close_vs_SMA20_Pct": close_vs_sma20,
                    "Volatility_5": values["Volatility_5"],
                    "Volume_Change_Pct": values["Volume_Change_Pct"],
                    "Average_Sentiment_Score": values["Average_Sentiment_Score"],
                    "Net_Sentiment_Score": values["Net_Sentiment_Score"],
                    "Total_Mentions": int(values["Total_Mentions"]),
                    "Social_Mentions": int(values["Social_Mentions"]),
                    "News_Mentions": int(values["News_Mentions"]),
                    "Target_Close_Next_Day": next_close,
                    "Target_Return_Pct": target_return
                }

                valid_records.append(record)

            except (ValueError, KeyError) as error:

                rejected_records.append({
                    "Ticker": row.get("Ticker", ""),
                    "Date": row.get("Date", ""),
                    "Reason": str(error)
                })

    valid_records.sort(
        key=lambda r: (r["Date"], r["Ticker"])
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=output_columns)
        writer.writeheader()
        writer.writerows(valid_records)

    with open(REJECTED_FILE, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["Ticker", "Date", "Reason"]
        )
        writer.writeheader()
        writer.writerows(rejected_records)

    print("\nPREDICTION DATASET PREPARATION")
    print("--------------------------------")
    print("Integrated records:", len(valid_records) + len(rejected_records))
    print("Valid prediction records:", len(valid_records))
    print("Rejected records:", len(rejected_records))
    print("Features prepared:", len(features) + 2)
    print("\nSaved:", OUTPUT_FILE)
    print("Rejected records saved:", REJECTED_FILE)

if __name__ == "__main__":
    main()