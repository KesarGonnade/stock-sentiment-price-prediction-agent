
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
    / "relevance_v2_test.csv"
)

OUTPUT_FILE = (
    ROOT / "data" / "processed"
    / "sentiment_analysis_results.csv"
)

MODEL = "qwen2.5:3b"
OLLAMA_URL = "http://localhost:11434/api/chat"

# This Samsung YouTube comment explicitly expresses
# an opinion about buying Samsung shares.
MANUAL_RELEVANT_IDS = {
    "12e9da9861b628feb62f062efde67b773718e610373050f2420b7ebfd6da237d"
}


# --------------------------------------------------
# SENTIMENT PROMPT
# --------------------------------------------------

SYSTEM_PROMPT = """
You are a financial sentiment analysis expert.

Analyze the content for the specified target stock.

Return exactly one sentiment:

positive
negative
neutral

POSITIVE:
- Expectation of stock price increase.
- Bullish investor opinions.
- Positive earnings or business developments.
- Buying interest and optimistic price targets.
- Positive analyst recommendations.

NEGATIVE:
- Expectation of stock price decline.
- Bearish investor opinions.
- Falling earnings, losses or weak business outlook.
- Selling pressure and negative analyst recommendations.
- Short-selling sentiment when expressed negatively.

NEUTRAL:
- Factual information without a clear positive or negative direction.
- Balanced news containing both positive and negative signals.
- General company announcements with no clear sentiment.
- Information whose overall direction is unclear.

IMPORTANT:
1. Analyze the target company, not unrelated companies.
2. Understand English, Korean and Chinese.
3. Informal investor opinions are valid sentiment.
4. Do not confuse relevance with sentiment.
5. A negative article is not irrelevant.
6. Do not invent information.
7. For mixed news, use neutral unless one direction
   clearly dominates.

Return ONLY valid JSON:

{
    "sentiment": "positive",
    "confidence": 90,
    "reason": "Brief explanation"
}
"""


# --------------------------------------------------
# OLLAMA REQUEST
# --------------------------------------------------

def analyze_sentiment(record):

    prompt = f"""
Target company: {record.get('stock_name')}
Target ticker: {record.get('ticker')}
Exchange: {record.get('exchange')}
Source: {record.get('source')}
Language: {record.get('language')}

CONTENT:

{record.get('text', '')[:4000]}

Determine the sentiment toward the target stock.
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

    sentiment = str(
        output.get("sentiment", "")
    ).lower().strip()

    confidence = float(
        output.get("confidence", 0)
    )

    reason = str(
        output.get("reason", "")
    ).strip()

    if sentiment not in {
        "positive", "negative", "neutral"
    }:
        raise ValueError(
            f"Invalid sentiment: {sentiment}"
        )

    if not 0 <= confidence <= 100:
        raise ValueError("Invalid confidence")

    if not reason:
        raise ValueError("Missing reason")

    score = {
        "positive": 1,
        "neutral": 0,
        "negative": -1
    }[sentiment]

    return sentiment, score, confidence, reason


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    print("\nHENGSENG SENTIMENT ANALYZER")
    print("--------------------------------")

    if not INPUT_FILE.exists():
        print("Input file not found:", INPUT_FILE)
        return

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)
        records = list(reader)
        columns = reader.fieldnames

    if not records:
        print("No records found.")
        return

    # Correct the one manually reviewed false negative.
    for record in records:
        if record["record_id"] in MANUAL_RELEVANT_IDS:
            record["v2_classification"] = "relevant"
            record["v2_reason"] = (
                "Manual correction: explicit Samsung "
                "share-buying opinion."
            )

    # Load previous results so interrupted runs can resume.
    completed = {}

    if OUTPUT_FILE.exists():

        with open(
            OUTPUT_FILE,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            for row in csv.DictReader(file):

                if row.get("sentiment_status") == "completed":
                    completed[row["record_id"]] = row

    output_columns = columns + [
        "sentiment",
        "sentiment_score",
        "sentiment_confidence",
        "sentiment_reason",
        "sentiment_status"
    ]

    counts = {
        "positive": 0,
        "negative": 0,
        "neutral": 0,
        "not_applicable": 0,
        "manual_review": 0,
        "error": 0
    }

    relevant_records = [
        r for r in records
        if r.get("v2_classification") == "relevant"
    ]

    print("Total records:", len(records))
    print("Relevant records:", len(relevant_records))
    print("Already completed:", len(completed))
    print("Remaining:", len(relevant_records) - len(completed))
    print()

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

        for index, record in enumerate(records, 1):

            record_id = record["record_id"]

            # Keep previous completed results.
            if record_id in completed:

                result = completed[record_id]

            elif record.get("v2_classification") == "irrelevant":

                result = dict(record)
                result.update({
                    "sentiment": "",
                    "sentiment_score": "",
                    "sentiment_confidence": "",
                    "sentiment_reason": "",
                    "sentiment_status": "not_applicable"
                })

            elif record.get("v2_classification") == "ambiguous":

                result = dict(record)
                result.update({
                    "sentiment": "",
                    "sentiment_score": "",
                    "sentiment_confidence": "",
                    "sentiment_reason": "",
                    "sentiment_status": "manual_review"
                })

            else:

                print(
                    f"[{index}/{len(records)}] "
                    f"{record.get('stock_name')} | "
                    f"{record.get('source')} ... ",
                    end="",
                    flush=True
                )

                result = dict(record)

                try:

                    sentiment, score, confidence, reason = (
                        analyze_sentiment(record)
                    )

                    result.update({
                        "sentiment": sentiment,
                        "sentiment_score": score,
                        "sentiment_confidence": confidence,
                        "sentiment_reason": reason,
                        "sentiment_status": "completed"
                    })

                    print(
                        f"{sentiment} ({confidence:.0f}%)"
                    )

                except Exception as error:

                    result.update({
                        "sentiment": "",
                        "sentiment_score": "",
                        "sentiment_confidence": "",
                        "sentiment_reason": str(error),
                        "sentiment_status": "error"
                    })

                    print("ERROR:", error)

            status = result["sentiment_status"]

            if status == "completed":
                counts[result["sentiment"]] += 1
            elif status == "not_applicable":
                counts["not_applicable"] += 1
            elif status == "manual_review":
                counts["manual_review"] += 1
            elif status == "error":
                counts["error"] += 1

            writer.writerow(result)
            file.flush()

    print("\n--------------------------------")
    print("SENTIMENT ANALYSIS SUMMARY")
    print("--------------------------------")

    for label, count in counts.items():
        print(f"{label}: {count}")

    print("\nOutput saved:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()
