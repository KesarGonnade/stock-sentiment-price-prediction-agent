
import os
import json
from collections import defaultdict

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

url_map = defaultdict(list)

for filename in files:
    path = os.path.join("data", "processed", filename)

    with open(path, "r", encoding="utf-8") as file:
        articles = json.load(file)

    for article in articles:
        url = article.get("url")

        if url:
            url_map[url].append({
                "file": filename,
                "title": article.get("original_title")
            })

print("\nDUPLICATE URL REPORT\n")

duplicates = {
    url: records
    for url, records in url_map.items()
    if len(records) > 1
}

if not duplicates:
    print("No duplicate URLs found.")
else:
    for number, (url, records) in enumerate(duplicates.items(), 1):
        print(f"\nDuplicate {number}")
        print("URL:", url)

        for record in records:
            print("File:", record["file"])
            print("Title:", record["title"])
