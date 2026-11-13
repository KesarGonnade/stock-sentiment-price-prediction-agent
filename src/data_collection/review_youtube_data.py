
import json
from pathlib import Path

DATA_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed/youtube_reviewed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Manual review based on the comments we inspected.
# Comment numbers start from 1.
REVIEW_DECISIONS = {
    "samsung_youtube_raw.json": {
        "relevant": [2],
        "ambiguous": [3],
        "irrelevant": [1]
    },
    "sk_hynix_youtube_raw.json": {
        "relevant": [1],
        "ambiguous": [2],
        "irrelevant": []
    },
    "hyundai_youtube_raw.json": {
        "relevant": [1],
        "ambiguous": [],
        "irrelevant": [2]
    },
    "lg_energy_solution_youtube_raw.json": {
        "relevant": [],
        "ambiguous": [],
        "irrelevant": list(range(1, 40))
    },
    "kakao_youtube_raw.json": {
        "relevant": [1, 2, 3, 4],
        "ambiguous": [],
        "irrelevant": []
    }
}


def review_file(filename, decisions):
    input_path = DATA_DIR / filename

    with open(input_path, "r", encoding="utf-8") as file:
        comments = json.load(file)

    reviewed = {
        "relevant": [],
        "ambiguous": [],
        "irrelevant": []
    }

    assigned_numbers = set()

    for category, numbers in decisions.items():
        for number in numbers:
            if number < 1 or number > len(comments):
                raise ValueError(
                    f"Invalid comment number {number} in {filename}"
                )

            if number in assigned_numbers:
                raise ValueError(
                    f"Comment {number} classified more than once"
                )

            assigned_numbers.add(number)

            record = comments[number - 1].copy()
            record["review_status"] = category
            reviewed[category].append(record)

    if len(assigned_numbers) != len(comments):
        raise ValueError(
            f"Not all comments were classified in {filename}"
        )

    stock_name = filename.replace("_youtube_raw.json", "")

    for category, records in reviewed.items():
        output_path = OUTPUT_DIR / f"{stock_name}_{category}.json"

        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(
                records,
                file,
                ensure_ascii=False,
                indent=4
            )

    print(f"\n{filename}")
    print(f"Relevant: {len(reviewed['relevant'])}")
    print(f"Ambiguous: {len(reviewed['ambiguous'])}")
    print(f"Irrelevant: {len(reviewed['irrelevant'])}")


def main():
    total_relevant = 0
    total_ambiguous = 0
    total_irrelevant = 0

    for filename, decisions in REVIEW_DECISIONS.items():
        review_file(filename, decisions)

        total_relevant += len(decisions["relevant"])
        total_ambiguous += len(decisions["ambiguous"])
        total_irrelevant += len(decisions["irrelevant"])

    print("\n" + "=" * 45)
    print("YOUTUBE REVIEW SUMMARY")
    print(f"Relevant: {total_relevant}")
    print(f"Ambiguous: {total_ambiguous}")
    print(f"Irrelevant: {total_irrelevant}")
    print(f"Total: {total_relevant + total_ambiguous + total_irrelevant}")
    print(f"\nReviewed files saved in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
