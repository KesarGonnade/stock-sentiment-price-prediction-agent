
import json
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path("data/raw")

FILES = [
    "samsung_youtube_raw.json",
    "sk_hynix_youtube_raw.json",
    "hyundai_youtube_raw.json",
    "lg_energy_solution_youtube_raw.json",
    "kakao_youtube_raw.json",
]

total_comments = 0
total_empty = 0
total_duplicates = 0

for filename in FILES:
    path = DATA_DIR / filename

    print("\n" + "=" * 55)
    print(f"FILE: {filename}")

    if not path.exists():
        print("ERROR: File not found")
        continue

    with open(path, "r", encoding="utf-8") as f:
        records = json.load(f)

    if not isinstance(records, list):
        print("ERROR: Expected a JSON list")
        continue

    total = len(records)
    empty = 0
    duplicates = 0
    seen = set()
    valid_dates = []
    stock_values = set()
    source_values = set()

    for record in records:
        text = record.get("text")
        if not isinstance(text, str) or not text.strip():
            empty += 1

        key = (
            record.get("video_id"),
            record.get("author"),
            record.get("published_at"),
            text
        )

        if key in seen:
            duplicates += 1
        seen.add(key)

        stock_values.add(record.get("stock"))
        source_values.add(record.get("source"))

        date_value = record.get("published_at")
        if date_value:
            try:
                date = datetime.fromisoformat(
                    date_value.replace("Z", "+00:00")
                )
                valid_dates.append(date)
            except ValueError:
                pass

    total_comments += total
    total_empty += empty
    total_duplicates += duplicates

    print(f"Total comments: {total}")
    print(f"Empty comments: {empty}")
    print(f"Duplicate comments: {duplicates}")
    print(f"Stock labels: {stock_values}")
    print(f"Source labels: {source_values}")

    if valid_dates:
        print(f"Earliest comment: {min(valid_dates)}")
        print(f"Latest comment: {max(valid_dates)}")
    else:
        print("No valid comment dates found")

print("\n" + "=" * 55)
print("OVERALL AUDIT")
print(f"Total comments: {total_comments}")
print(f"Empty comments: {total_empty}")
print(f"Duplicate comments: {total_duplicates}")
print("Audit completed.")
