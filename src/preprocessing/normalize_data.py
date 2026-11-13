
import json
import hashlib

from pathlib import Path
from datetime import datetime, timezone


# ==========================================
# CONFIGURATION
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_FILE = PROCESSED_DIR / "normalized_sentiment_data.json"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# Stock metadata for files that do not contain stock information
STOCK_METADATA = {
    "tencent": ("Tencent Holdings", "0700.HK", "HKEX"),
    "alibaba": ("Alibaba Group", "9988.HK", "HKEX"),
    "hsbc": ("HSBC Holdings", "0005.HK", "HKEX"),
    "xiaomi": ("Xiaomi Corporation", "1810.HK", "HKEX"),
    "byd": ("BYD Company", "1211.HK", "HKEX"),
    "samsung": ("Samsung Electronics", "005930.KS", "KRX"),
    "sk_hynix": ("SK Hynix", "000660.KS", "KRX"),
    "hyundai": ("Hyundai Motor", "005380.KS", "KRX"),
    "lg_energy_solution": (
        "LG Energy Solution", "373220.KS", "KRX"
    ),
    "kakao": ("Kakao", "035720.KS", "KRX")
}


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_value(record, fields, default=None):

    for field in fields:
        value = record.get(field)

        if value is not None and str(value).strip():
            return value

    return default


def detect_source(filename):

    name = filename.lower()

    if "telegram" in name:
        return "Telegram"

    if "naver" in name:
        return "Naver"

    if "youtube" in name:
        return "YouTube"

    if "lihkg" in name:
        return "LIHKG"

    if "_news_reviewed" in name:
        return "Exa"

    return None


def detect_stock(filename, record):

    # Prefer metadata provided by the record
    ticker = get_value(record, ["ticker"])

    if ticker:
        for name, metadata in STOCK_METADATA.items():
            if ticker == metadata[1]:
                return metadata

    stock_name = get_value(
        record,
        ["stock_name", "stockName", "stock"]
    )

    if stock_name:
        stock_name_lower = str(stock_name).lower()

        for name, metadata in STOCK_METADATA.items():
            if (
                name.replace("_", " ") in stock_name_lower
                or metadata[0].lower() in stock_name_lower
            ):
                return metadata

    # Infer from filename
    filename_lower = filename.lower()

    for name, metadata in STOCK_METADATA.items():
        if name in filename_lower:
            return metadata

    return None


def normalize_timestamp(value):

    if value is None:
        return None

    try:
        timestamp = str(value).strip()

        if timestamp.endswith("Z"):
            timestamp = timestamp[:-1] + "+00:00"

        parsed = datetime.fromisoformat(timestamp)

        # Preserve UTC for timestamps that already specify a timezone.
        # Naive timestamps are not assumed to be UTC.
        if parsed.tzinfo is None:
            return None

        return parsed.astimezone(
            timezone.utc
        ).isoformat().replace("+00:00", "Z")

    except (ValueError, TypeError):
        return None


def extract_text(record, source):

    if source == "Exa":

        title = get_value(
            record,
            ["translated_title", "original_title", "title"],
            ""
        )

        body = get_value(
            record,
            ["translated_text", "original_text", "text"],
            ""
        )

        # Avoid adding the title twice if it already begins the body
        if title and body:
            if str(body).strip().lower().startswith(
                str(title).strip().lower()
            ):
                return str(body).strip()

            return f"{title}\n{body}".strip()

        return str(title or body).strip()

    title = get_value(
        record,
        ["title", "video_title"],
        ""
    )

    body = get_value(
        record,
        ["text", "content", "message", "body", "own_text"],
        ""
    )

    if title and body:
        return f"{title}\n{body}".strip()

    return str(title or body or "").strip()


def create_record_id(record):

    identity = "|".join([
        str(record.get("source", "")),
        str(record.get("ticker", "")),
        str(record.get("published_at", "")),
        str(record.get("text", "")).strip().lower()
    ])

    return hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()


def extract_engagement(record):

    return {
        "likes": get_value(record, ["likes", "like_count"]),
        "dislikes": get_value(
            record, ["dislikes", "dislike_count"]
        ),
        "views": get_value(record, ["views", "view_count"]),
        "reactions_total": get_value(
            record, ["reactionsTotal", "reaction_count"]
        ),
        "channel_subscribers": get_value(
            record, ["channelSubscribers", "subscribers"]
        )
    }


# ==========================================
# READ JSON FILES
# ==========================================

def read_json_records(path):

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):

        for key in [
            "data", "items", "results",
            "posts", "messages", "articles"
        ]:
            if isinstance(data.get(key), list):
                return data[key]

        return [data]

    return []


# ==========================================
# NORMALIZE ONE RECORD
# ==========================================

def normalize_record(record, filename):

    if not isinstance(record, dict):
        return None

    source = detect_source(filename)

    if source is None:
        return None

    stock = detect_stock(filename, record)

    if stock is None:
        return None

    stock_name, ticker, exchange = stock

    # Use the record's explicit ticker if available
    ticker = get_value(record, ["ticker"], ticker)

    text = extract_text(record, source)

    if not text:
        return None

    timestamp = get_value(
        record,
        [
            "published_date",
            "published_at",
            "writtenAt",
            "date",
            "created_at",
            "timestamp"
        ]
    )

    normalized_timestamp = normalize_timestamp(timestamp)

    relevance = get_value(
        record,
        ["relevance_status"],
        "pending_review"
    )

    # Preserve original news review status
    if source == "Exa" and relevance == "pending_manual_review":
        relevance = "pending_review"

    normalized = {
        "source": source,
        "stock_name": stock_name,
        "ticker": ticker,
        "exchange": exchange,
        "text": text,
        "published_at": normalized_timestamp,
        "original_timestamp": timestamp,
        "language": get_value(
            record,
            ["original_language", "language"],
            "unknown"
        ),
        "engagement": extract_engagement(record),
        "author": get_value(
            record,
            ["author", "authorSignature", "replyToAuthor"]
        ),
        "channel": get_value(
            record,
            ["channelTitle", "channel", "source_domain"]
        ),
        "url": get_value(record, ["url"]),
        "relevance_status": relevance
    }

    normalized["record_id"] = create_record_id(normalized)

    return normalized


# ==========================================
# COLLECT INPUT FILES
# ==========================================

def get_input_files():

    files = []

    # Raw social-media records
    if RAW_DIR.exists():

        for path in RAW_DIR.glob("*.json"):

            if detect_source(path.name):
                files.append(path)

    # Only reviewed Exa news files.
    # This avoids counting reviewed, translated and
    # language-detected versions of the same articles.
    if PROCESSED_DIR.exists():

        for path in PROCESSED_DIR.glob("*_news_reviewed.json"):
            files.append(path)

    return sorted(files)


# ==========================================
# MAIN NORMALIZATION
# ==========================================

def main():

    all_records = []
    skipped_records = 0

    print("=" * 65)
    print("SENTIMENT DATA NORMALIZATION")
    print("=" * 65)

    files = get_input_files()

    print("Input files found:", len(files))

    for path in files:

        print(f"\nReading: {path.name}")

        try:

            records = read_json_records(path)

            file_success = 0

            for record in records:

                normalized = normalize_record(
                    record,
                    path.name
                )

                if normalized is None:
                    skipped_records += 1
                    continue

                all_records.append(normalized)
                file_success += 1

            print("Records found:", len(records))
            print("Records normalized:", file_success)

        except Exception as error:

            print("File processing error:", error)

    # ======================================
    # REMOVE EXACT DUPLICATES
    # ======================================

    unique_records = []
    seen_ids = set()

    for record in all_records:

        record_id = record["record_id"]

        if record_id in seen_ids:
            continue

        seen_ids.add(record_id)
        unique_records.append(record)

    duplicate_count = (
        len(all_records) - len(unique_records)
    )

    # Sort by timestamp, keeping undated records last
    unique_records.sort(
        key=lambda record: (
            record["published_at"] is None,
            record["published_at"] or ""
        )
    )

    # ======================================
    # SAVE OUTPUT
    # ======================================

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            unique_records,
            file,
            ensure_ascii=False,
            indent=4
        )

    # ======================================
    # SUMMARY
    # ======================================

    print("\n" + "=" * 65)
    print("NORMALIZATION SUMMARY")
    print("=" * 65)

    print("Input files:", len(files))
    print("Records normalized:", len(all_records))
    print("Exact duplicates removed:", duplicate_count)
    print("Records skipped:", skipped_records)
    print("Final unique records:", len(unique_records))

    print("\nSource-wise counts:")

    source_counts = {}

    for record in unique_records:
        source = record["source"]

        source_counts[source] = (
            source_counts.get(source, 0) + 1
        )

    for source, count in sorted(source_counts.items()):
        print(f"{source}: {count}")

    print("\nSaved to:", OUTPUT_FILE)
    print("\nNormalization completed!")


if __name__ == "__main__":
    main()
