
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

FOLDERS = [
    PROJECT_ROOT / "data" / "raw",
    PROJECT_ROOT / "data" / "processed"
]


def inspect_json_file(file_path):

    print("\n" + "=" * 70)
    print("FILE:", file_path.name)
    print("=" * 70)

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            records = data

        elif isinstance(data, dict):
            records = None

            for key in [
                "data", "items", "results",
                "posts", "messages", "articles"
            ]:
                if isinstance(data.get(key), list):
                    records = data[key]
                    break

            if records is None:
                records = [data]

        else:
            print("Unsupported JSON structure.")
            return

        print("Total records:", len(records))

        if not records:
            print("No records found.")
            return

        first_record = records[0]

        if not isinstance(first_record, dict):
            print("First record is not a dictionary.")
            return

        print("\nAvailable fields:")

        for key in first_record.keys():
            print("-", key)

        print("\nFirst record sample:")

        for key, value in first_record.items():

            sample = str(value).replace("\n", " ")

            if len(sample) > 180:
                sample = sample[:180] + "..."

            print(f"{key}: {sample}")

    except Exception as error:
        print("Inspection error:", error)


def main():

    print("=" * 70)
    print("SENTIMENT DATA INSPECTION")
    print("=" * 70)

    for folder in FOLDERS:

        print(f"\n\nFOLDER: {folder}")

        if not folder.exists():
            print("Folder does not exist.")
            continue

        json_files = sorted(folder.glob("*.json"))

        if not json_files:
            print("No JSON files found.")
            continue

        for file_path in json_files:
            inspect_json_file(file_path)


if __name__ == "__main__":
    main()

