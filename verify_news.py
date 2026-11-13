
import os
import json

files = [
    "tencent_news_reviewed.json",
    "alibaba_news_reviewed.json",
    "hsbc_news_reviewed.json",
    "xiaomi_news_reviewed.json",
    "byd_news_reviewed.json",
    "samsung_news_reviewed.json",
    "sk_hynix_news_reviewed.json",
    "hyundai_news_reviewed.json",
    "lg_energy_solution_news_reviewed.json",
    "kakao_news_reviewed.json"
]

total = 0

print("\nREVIEWED NEWS FILE VERIFICATION\n")

for filename in files:
    path = os.path.join("data", "processed", filename)

    if not os.path.exists(path):
        print(f"MISSING | {filename}")
        continue

    try:
        with open(path, "r", encoding="utf-8") as file:
            articles = json.load(file)

        if not isinstance(articles, list):
            print(f"INVALID | {filename} | Expected a list")
            continue

        print(f"OK | {filename} | {len(articles)} articles")
        total += len(articles)

    except Exception as error:
        print(f"ERROR | {filename} | {error}")

print("\nTOTAL REVIEWED ARTICLES:", total)
