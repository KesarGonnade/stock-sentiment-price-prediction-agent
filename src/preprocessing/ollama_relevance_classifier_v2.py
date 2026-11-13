
import csv
import json
import urllib.request
import random

from pathlib import Path


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    ROOT / "data" / "processed"
    / "ollama_relevance_results.csv"
)

OUTPUT_FILE = (
    ROOT / "data" / "processed"
    / "relevance_v2_test.csv"
)

MODEL = "qwen2.5:3b"

OLLAMA_URL = "http://localhost:11434/api/chat"

TEST_SIZE = 199


# --------------------------------------------------
# CLASSIFICATION PROMPT
# --------------------------------------------------

SYSTEM_PROMPT = """
You are an expert financial-market relevance classifier.

Your task is to determine whether a record is useful
for analyzing sentiment or market information about
the SPECIFIC target stock.

Understand English, Korean and Chinese.
Read the original language directly.

Return exactly one classification:

1. relevant
2. irrelevant
3. ambiguous

RELEVANT:

- Opinions about buying, selling or holding the stock.
- Predictions about future stock prices.
- Bullish or bearish investor discussions.
- Actual stock price increases or decreases.
- Short selling and short covering discussions.
- Trader positions and market expectations.
- Company earnings and financial results.
- Company announcements with investment significance.
- Industry developments directly affecting the company.

IMPORTANT SOURCE-SPECIFIC RULES:

NAVER:
Posts collected from a specific stock's Naver Finance
discussion board are presumed to concern that stock.

Short, informal Korean investor comments about:
- Short sellers
- Buying and selling
- Holding positions
- Price expectations
- Bullish or bearish opinions
- Traders exiting positions

must be considered relevant when they express
a meaningful investment opinion.

Do not reject investor discussions just because
they do not repeat the company name or ticker.

TELEGRAM:
Messages may discuss multiple companies.

Classify as relevant if the message contains
meaningful information about the target company.

Do not classify the entire message as relevant
just because another company is discussed.

EXA:
Financial news about the target company is relevant.

Competitor or industry news is relevant only when
there is a meaningful connection to the target company.

YOUTUBE:
General market discussions without a meaningful
connection to the target stock are irrelevant.

IRRELEVANT:

- Spam and personal attacks.
- Unrelated conversations.
- Promotions unrelated to the target stock.
- News about unrelated companies.
- General market discussions with no target-stock connection.

AMBIGUOUS:

- Insufficient information.
- Unclear connection to the target company.
- Announcements with uncertain investment significance.
- Records containing only a URL without article content.

IMPORTANT:

1. Negative sentiment is still relevant sentiment.
2. Informal investor language can be relevant.
3. Do not confuse relevance with positive sentiment.
4. Do not invent missing information.
5. Consider the source context.
6. A stock-specific Naver discussion board provides
   useful context even if the ticker is not repeated.

Return ONLY valid JSON in this format:

{
    "classification": "relevant",
    "confidence": 95,
    "reason": "Brief explanation"
}
"""


# --------------------------------------------------
# OLLAMA CLASSIFICATION FUNCTION
# --------------------------------------------------

def classify(record):

    prompt = f"""
Target company: {record.get('stock_name')}
Target ticker: {record.get('ticker')}
Exchange: {record.get('exchange')}
Source: {record.get('source')}
Language: {record.get('language')}

Original content:

{record.get('text', '')[:3000]}

Determine whether this content is relevant
to the target stock.

Remember to apply the source-specific rules.
"""

    payload = {
        "model": MODEL,

        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        "format": "json",
        "stream": False,

        "options": {
            "temperature": 0
        }
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(
        request,
        timeout=180
    ) as response:

        result = json.loads(
            response.read().decode("utf-8")
        )

    output = json.loads(
        result["message"]["content"]
    )

    label = str(
        output.get("classification", "")
    ).lower().strip()

    confidence = float(
        output.get("confidence", 0)
    )

    reason = str(
        output.get("reason", "")
    ).strip()

    if label not in {
        "relevant",
        "irrelevant",
        "ambiguous"
    }:
        raise ValueError(
            f"Invalid classification: {label}"
        )

    if not 0 <= confidence <= 100:
        raise ValueError(
            "Invalid confidence score"
        )

    if not reason:
        raise ValueError(
            "Missing classification reason"
        )

    return label, confidence, reason


# --------------------------------------------------
# SELECT TEST RECORDS
# --------------------------------------------------

def select_test_records(records):

    random.seed(42)

    groups = {
        "relevant": [],
        "irrelevant": [],
        "ambiguous": []
    }

    for record in records:

        label = str(
            record.get("llm_suggested_status", "")
        ).lower().strip()

        if label in groups:
            groups[label].append(record)

    selected = []

    # First select up to 3 from each V1 category.
    for label in [
        "relevant",
        "irrelevant",
        "ambiguous"
    ]:

        available = groups[label]

        count = min(3, len(available))

        if count:
            selected.extend(
                random.sample(available, count)
            )

    # Fill the remaining slots to reach 10.
    remaining = [
        record
        for record in records
        if record not in selected
    ]

    needed = TEST_SIZE - len(selected)

    if needed > 0 and remaining:

        selected.extend(
            random.sample(
                remaining,
                min(needed, len(remaining))
            )
        )

    return selected


# --------------------------------------------------
# MAIN FUNCTION
# --------------------------------------------------

def main():

    print("\nQWEN RELEVANCE CLASSIFIER V2")
    print("--------------------------------")

    if not INPUT_FILE.exists():

        print("Input file not found:")
        print(INPUT_FILE)

        return

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        records = list(reader)

        if not records:

            print("Input file contains no records.")
            return

        columns = reader.fieldnames

    selected = select_test_records(records)

    output_columns = columns + [
        "v2_classification",
        "v2_confidence",
        "v2_reason"
    ]

    counts = {
        "relevant": 0,
        "irrelevant": 0,
        "ambiguous": 0,
        "error": 0
    }

    print(f"\nTotal records: {len(records)}")
    print(f"Test records: {len(selected)}\n")

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

        for index, record in enumerate(
            selected,
            start=1
        ):

            print(
                f"[{index}/{len(selected)}] "
                f"{record.get('stock_name')} | "
                f"{record.get('source')}",
                end=" ... ",
                flush=True
            )

            try:

                label, confidence, reason = classify(
                    record
                )

                record["v2_classification"] = label

                record["v2_confidence"] = confidence

                record["v2_reason"] = reason

                counts[label] += 1

                print(
                    f"{label} ({confidence:.0f}%)"
                )

            except Exception as error:

                record["v2_classification"] = "error"

                record["v2_confidence"] = ""

                record["v2_reason"] = str(error)

                counts["error"] += 1

                print("ERROR:", error)

            writer.writerow(record)

            file.flush()

    print("\n--------------------------------")
    print("V2 TEST SUMMARY")
    print("--------------------------------")

    for label, count in counts.items():

        print(f"{label}: {count}")

    print("\nSaved output:")
    print(OUTPUT_FILE)

    print("\nOriginal input data was not modified.")


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    main()
