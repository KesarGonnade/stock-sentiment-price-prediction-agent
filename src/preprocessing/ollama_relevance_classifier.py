
import csv
import json
import time
import urllib.request
import urllib.error

from pathlib import Path


# ==========================================
# CONFIGURATION
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT / "data" / "processed"
    / "sentiment_relevance_review.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT / "data" / "processed"
    / "ollama_relevance_results.csv"
)

OLLAMA_URL = "http://localhost:11434/api/chat"

MODEL_NAME = "qwen2.5:3b"

MAX_TEXT_LENGTH = 3000


# ==========================================
# CLASSIFICATION PROMPT
# ==========================================

SYSTEM_PROMPT = """
You are a financial data relevance classifier.

Your task is to classify social media posts and financial news
about publicly traded companies.

The text may be written in English, Korean or Chinese.
Understand the original language. Do not require translation.

Classify each record using exactly one label:

1. relevant:
   The content provides useful information about the stock,
   share price, investment, trading, investor opinion,
   market expectations, financial performance, earnings,
   valuation, price movement, or other information that could
   reasonably influence investor sentiment.

2. irrelevant:
   The content is unrelated to the stock or provides no useful
   information for stock-market sentiment analysis.
   Examples include spam, unrelated conversations, generic
   promotions, and unrelated content.

3. ambiguous:
   The content discusses the company but its relevance to
   investment or stock sentiment is unclear.
   Examples include ordinary product updates, general company
   announcements, and technology news without a clear market
   connection.

Important rules:

- Do not assume every company announcement is relevant.
- Do not assume every negative statement is bearish sentiment.
- Do not invent facts that are not in the text.
- Do not classify based only on the stock name.
- Consider the actual meaning and context of the text.
- Treat short posts carefully.
- If context is insufficient, choose ambiguous.
- Do not confuse likes or views with positive sentiment.

Return ONLY valid JSON with this structure:

{
    "classification": "relevant",
    "reason": "Short explanation of the decision"
}
"""


# ==========================================
# CALL LOCAL OLLAMA MODEL
# ==========================================

def classify_with_ollama(record):

    text = record.get("text", "").strip()

    user_prompt = f"""
Stock: {record.get('stock_name')}
Ticker: {record.get('ticker')}
Exchange: {record.get('exchange')}
Source: {record.get('source')}
Language: {record.get('language')}

Content:
{text[:MAX_TEXT_LENGTH]}

Classify the investment relevance of this content.
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.1
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

    content = result["message"]["content"]

    classification = json.loads(content)

    label = str(
        classification.get("classification", "")
    ).lower().strip()

    reason = str(
        classification.get("reason", "")
    ).strip()

    allowed_labels = {
        "relevant",
        "irrelevant",
        "ambiguous"
    }

    if label not in allowed_labels:
        raise ValueError(
            f"Invalid classification returned: {label}"
        )

    if not reason:
        raise ValueError("Classification reason is empty.")

    return label, reason


# ==========================================
# MAIN PROCESS
# ==========================================

def main():

    print("=" * 65)
    print("OLLAMA MULTILINGUAL RELEVANCE CLASSIFIER")
    print("=" * 65)

    if not INPUT_FILE.exists():
        print("ERROR: Input CSV not found.")
        return

    # Check whether Ollama is accessible
    try:

        request = urllib.request.Request(
            "http://localhost:11434/api/tags"
        )

        with urllib.request.urlopen(
            request,
            timeout=10
        ) as response:

            model_data = json.loads(
                response.read().decode("utf-8")
            )

        installed_models = [
            model["name"]
            for model in model_data.get("models", [])
        ]

        if not any(
            name == MODEL_NAME
            or name.startswith(MODEL_NAME + ":")
            for name in installed_models
        ):
            print("ERROR: Required model is not available.")
            print("Available models:", installed_models)
            return

    except Exception as error:

        print("ERROR: Cannot connect to Ollama.")
        print("Details:", error)
        print("Check that Ollama is running.")
        return

    # Read input records
    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)
        records = list(reader)
        columns = reader.fieldnames or []

    output_columns = columns + [
        "llm_suggested_status",
        "llm_reason",
        "llm_model"
    ]

    counts = {
        "relevant": 0,
        "irrelevant": 0,
        "ambiguous": 0,
        "error": 0
    }

    print("\nModel:", MODEL_NAME)
    print("Records to classify:", len(records))
    print("\nStarting classification...\n")

    # Write after every record so progress is preserved
    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as output_file:

        writer = csv.DictWriter(
            output_file,
            fieldnames=output_columns
        )

        writer.writeheader()
        output_file.flush()

        for index, record in enumerate(records, start=1):

            print(
                f"[{index}/{len(records)}] "
                f"{record.get('ticker')} | "
                f"{record.get('source')}",
                end=" ... "
            )

            try:

                label, reason = classify_with_ollama(record)

                record["llm_suggested_status"] = label
                record["llm_reason"] = reason
                record["llm_model"] = MODEL_NAME

                counts[label] += 1

                print(label)

            except Exception as error:

                record["llm_suggested_status"] = "error"
                record["llm_reason"] = str(error)
                record["llm_model"] = MODEL_NAME

                counts["error"] += 1

                print("ERROR:", error)

            writer.writerow(record)
            output_file.flush()

    print("\n" + "=" * 65)
    print("CLASSIFICATION SUMMARY")
    print("=" * 65)

    print("Total records:", len(records))
    print("Relevant:", counts["relevant"])
    print("Irrelevant:", counts["irrelevant"])
    print("Ambiguous:", counts["ambiguous"])
    print("Errors:", counts["error"])

    print("\nOutput saved to:")
    print(OUTPUT_FILE)

    print("\nOriginal datasets were not modified.")


if __name__ == "__main__":
    main()
