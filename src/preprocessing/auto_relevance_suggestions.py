
import csv
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT / "data" / "processed"
    / "sentiment_relevance_review.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT / "data" / "processed"
    / "sentiment_relevance_suggestions.csv"
)


# Strong investment and trading indicators
FINANCIAL_KEYWORDS = [
    "stock", "share price", "stock price", "shares",
    "investor", "investment", "trading", "trader",
    "buy", "sell", "bought", "sold", "hold",
    "bullish", "bearish", "bull", "bear",
    "undervalued", "overvalued", "valuation",
    "profit", "loss", "earnings", "revenue",
    "dividend", "target price", "price target",
    "support level", "resistance level",
    "market cap", "breakout", "rally",
    "short selling", "portfolio", "analyst",
    "forecast", "shares rise", "shares fall",
    "price increase", "price decrease"
]


# Company-related topics that may not express investor sentiment
COMPANY_KEYWORDS = [
    "product launch", "software update", "new product",
    "partnership", "acquisition", "merger",
    "factory", "production", "technology",
    "smartphone", "vehicle", "battery",
    "employee", "hiring", "expansion",
    "research and development", "launches",
    "official announcement", "new model"
]


# Obvious low-value content indicators
LOW_VALUE_KEYWORDS = [
    "subscribe to my channel",
    "follow my page",
    "like and subscribe",
    "free giveaway",
    "click this link",
    "visit my website"
]


def contains_non_english_script(text):

    # Korean Hangul, Chinese Han characters, Japanese scripts
    pattern = r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]"

    return bool(re.search(pattern, text))


def find_matches(text, keywords):

    text_lower = text.lower()

    return [
        keyword
        for keyword in keywords
        if keyword in text_lower
    ]


def suggest_relevance(record):

    text = record.get("text", "").strip()
    source = record.get("source", "")

    if not text:
        return "ambiguous", "Text is missing."

    # Do not guess sentiment relevance for multilingual text
    if contains_non_english_script(text):
        return (
            "manual_review",
            "Contains Korean, Chinese or Japanese text; "
            "requires multilingual review."
        )

    financial_matches = find_matches(
        text, FINANCIAL_KEYWORDS
    )

    company_matches = find_matches(
        text, COMPANY_KEYWORDS
    )

    low_value_matches = find_matches(
        text, LOW_VALUE_KEYWORDS
    )

    if low_value_matches:
        return (
            "ambiguous",
            "Contains possible promotional or low-value content: "
            + ", ".join(low_value_matches)
        )

    if financial_matches:
        return (
            "relevant",
            "Contains investment or trading terms: "
            + ", ".join(financial_matches)
        )

    if company_matches or source == "Exa":
        matches = company_matches or ["financial news article"]

        return (
            "ambiguous",
            "Company-related content; investor sentiment "
            "is not established: " + ", ".join(matches)
        )

    return (
        "manual_review",
        "No strong investment or company-related keywords found."
    )


def main():

    if not INPUT_FILE.exists():
        print("ERROR: Review CSV not found:", INPUT_FILE)
        return

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)
        records = list(reader)
        original_columns = reader.fieldnames or []

    new_columns = [
        "suggested_status",
        "suggestion_reason"
    ]

    output_columns = original_columns + [
        column
        for column in new_columns
        if column not in original_columns
    ]

    counts = {
        "relevant": 0,
        "ambiguous": 0,
        "manual_review": 0
    }

    for record in records:

        suggestion, reason = suggest_relevance(record)

        # Keep the human-reviewed status separate.
        record["suggested_status"] = suggestion
        record["suggestion_reason"] = reason

        counts[suggestion] += 1

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=output_columns
        )

        writer.writeheader()
        writer.writerows(records)

    print("=" * 60)
    print("AUTOMATED RELEVANCE SUGGESTIONS")
    print("=" * 60)

    print("Total records:", len(records))

    for status, count in counts.items():
        print(f"{status}: {count}")

    print("\nOutput saved to:")
    print(OUTPUT_FILE)

    print("\nIMPORTANT:")
    print("These are suggestions, not final classifications.")
    print("Original review CSV has not been modified.")


if __name__ == "__main__":
    main()
