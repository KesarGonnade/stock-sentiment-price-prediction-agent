
import csv
import random

from pathlib import Path
from collections import defaultdict


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT / "data" / "processed"
    / "ollama_relevance_results.csv"
)

OUTPUT = (
    ROOT / "data" / "processed"
    / "relevance_audit_sample.csv"
)

SAMPLE_PER_CLASS = 7


def main():

    groups = defaultdict(list)

    with open(
        INPUT, "r", encoding="utf-8-sig", newline=""
    ) as file:

        for record in csv.DictReader(file):
            label = record.get("llm_suggested_status")
            groups[label].append(record)

    random.seed(42)

    selected = []

    for label in ["relevant", "irrelevant", "ambiguous"]:

        sample_size = min(
            SAMPLE_PER_CLASS,
            len(groups[label])
        )

        selected.extend(
            random.sample(groups[label], sample_size)
        )

    columns = [
        "ticker",
        "source",
        "language",
        "text",
        "llm_suggested_status",
        "llm_reason"
    ]

    with open(
        OUTPUT, "w", encoding="utf-8-sig", newline=""
    ) as file:

        writer = csv.DictWriter(
            file, fieldnames=columns
        )

        writer.writeheader()

        for record in selected:
            writer.writerow({
                key: record.get(key, "")
                for key in columns
            })

    print("Audit sample created.")
    print("Total selected:", len(selected))
    print("Output:", OUTPUT)

    for label in ["relevant", "irrelevant", "ambiguous"]:
        print(f"{label}: {sum(
            r['llm_suggested_status'] == label
            for r in selected
        )}")


if __name__ == "__main__":
    main()
