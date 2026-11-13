
import json
import csv

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT / "data" / "processed"
    / "normalized_sentiment_data.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT / "data" / "processed"
    / "sentiment_relevance_review.csv"
)


def main():

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        records = json.load(file)

    columns = [
        "record_id",
        "stock_name",
        "ticker",
        "exchange",
        "source",
        "published_at",
        "language",
        "text",
        "likes",
        "dislikes",
        "views",
        "reactions_total",
        "relevance_status",
        "review_notes"
    ]

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=columns
        )

        writer.writeheader()

        for record in records:

            engagement = record.get("engagement", {})

            writer.writerow({
                "record_id": record.get("record_id"),
                "stock_name": record.get("stock_name"),
                "ticker": record.get("ticker"),
                "exchange": record.get("exchange"),
                "source": record.get("source"),
                "published_at": record.get("published_at"),
                "language": record.get("language"),
                "text": record.get("text"),
                "likes": engagement.get("likes"),
                "dislikes": engagement.get("dislikes"),
                "views": engagement.get("views"),
                "reactions_total": engagement.get("reactions_total"),
                "relevance_status": "",
                "review_notes": ""
            })

    print("=" * 55)
    print("RELEVANCE REVIEW SHEET CREATED")
    print("=" * 55)
    print("Records exported:", len(records))
    print("Output:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
