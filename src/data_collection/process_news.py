
import json
import os

from src.data_collection.language_detector import (
    detect_article_language
)


# --------------------------------------------------
# PROCESS ONE NEWS FILE
# --------------------------------------------------

def process_news_file(input_file, output_file):

    with open(input_file, "r", encoding="utf-8") as file:
        articles = json.load(file)

    processed_articles = []

    for article in articles:

        title = article.get("original_title") or ""
        text = article.get("original_text") or ""

        # Detect language using title and article text
        combined_text = title + " " + text

        detected_language = detect_article_language(
            combined_text
        )

        article["original_language"] = detected_language

        processed_articles.append(article)

        print(
            article.get("ticker"),
            "|",
            detected_language,
            "|",
            title[:70]
        )

    os.makedirs(
        os.path.dirname(output_file),
        exist_ok=True
    )

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            processed_articles,
            file,
            ensure_ascii=False,
            indent=4
        )

    print("\nProcessed articles:", len(processed_articles))
    print("Saved to:", output_file)


# --------------------------------------------------
# MAIN PROGRAM
# --------------------------------------------------

if __name__ == "__main__":

    files = [
        (
            "data/processed/tencent_news_reviewed.json",
            "data/processed/tencent_news_language_detected.json"
        ),
        (
            "data/processed/alibaba_news_reviewed.json",
            "data/processed/alibaba_news_language_detected.json"
        )
    ]

    for input_file, output_file in files:

        print("\n================================")
        print("Processing:", input_file)
        print("================================")

        process_news_file(
            input_file,
            output_file
        )

    print("\nLanguage detection completed!")

