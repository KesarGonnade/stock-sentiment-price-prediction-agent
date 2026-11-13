
import os
import json
from collections import Counter

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

required_fields = [
    "original_title",
    "original_text",
    "published_date",
    "collection_timestamp",
    "search_language",
    "source_domain"
]

total = 0
missing_fields = Counter()
languages = Counter()
urls = []
missing_dates = 0
empty_text = 0
future_articles = 0

print("\nNEWS DATA QUALITY AUDIT\n")

for filename in files:
    path = os.path.join("data", "processed", filename)

    with open(path, "r", encoding="utf-8") as file:
        articles = json.load(file)

    print(f"\n{filename}: {len(articles)} articles")

    for article in articles:
        total += 1

        for field in required_fields:
            if not article.get(field):
                missing_fields[field] += 1

        languages[article.get("search_language", "unknown")] += 1

        if not article.get("published_date"):
            missing_dates += 1

        if not article.get("original_text", "").strip():
            empty_text += 1

        published = article.get("published_date")
        collected = article.get("collection_timestamp")

        if published and collected and published > collected:
            future_articles += 1

        url = article.get("url")
        if url:
            urls.append(url)

print("\n========== AUDIT SUMMARY ==========")
print("Total articles:", total)
print("Language distribution:", dict(languages))
print("Missing required fields:", dict(missing_fields))
print("Missing publication dates:", missing_dates)
print("Empty original text:", empty_text)
print("Articles published after collection:", future_articles)
print("Duplicate URLs:", len(urls) - len(set(urls)))
print("Articles without URL:", total - len(urls))
