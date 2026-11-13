
import json
from pathlib import Path

DATA_DIR = Path("data/raw")

FILES = [
    "samsung_youtube_raw.json",
    "sk_hynix_youtube_raw.json",
    "hyundai_youtube_raw.json",
    "lg_energy_solution_youtube_raw.json",
    "kakao_youtube_raw.json",
]

for filename in FILES:
    path = DATA_DIR / filename

    with open(path, "r", encoding="utf-8") as file:
        comments = json.load(file)

    print("\n" + "=" * 70)
    print(filename)
    print("=" * 70)

    for index, comment in enumerate(comments, start=1):
        print(f"\nComment {index}")
        print("Video:", comment.get("video_title"))
        print("Author:", comment.get("author"))
        print("Text:", comment.get("text"))
        print("Likes:", comment.get("likes"))
        print("Date:", comment.get("published_at"))
