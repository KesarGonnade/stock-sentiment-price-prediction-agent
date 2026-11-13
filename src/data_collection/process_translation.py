
import json
from pathlib import Path

from src.data_collection.translator import translate_article


BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def process_file(input_filename, output_filename):
    input_path = PROCESSED_DIR / input_filename
    output_path = PROCESSED_DIR / output_filename

    with open(input_path, "r", encoding="utf-8") as file:
        articles = json.load(file)

    translated_articles = []

    for article in articles:
        try:
            article = translate_article(article)
            translated_articles.append(article)

            print(
                article.get("original_title", "Untitled"),
                "->",
                article.get("translation_status")
            )

        except Exception as error:
            article["translation_status"] = "failed"
            article["translation_error"] = str(error)
            translated_articles.append(article)

            print("Translation failed:", error)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            translated_articles,
            file,
            ensure_ascii=False,
            indent=4
        )

    print(f"\nSaved {len(translated_articles)} articles to {output_path}")


if __name__ == "__main__":
    process_file(
        "tencent_news_language_detected.json",
        "tencent_news_translated.json"
    )

    process_file(
        "alibaba_news_language_detected.json",
        "alibaba_news_translated.json"
    )
