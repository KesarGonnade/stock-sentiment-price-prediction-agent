
import os
import json

from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from dotenv import load_dotenv
from exa_py import Exa

from src.data_collection.stock_news_config import STOCK_NEWS_CONFIG


# --------------------------------------------------
# 1. LOAD ENVIRONMENT VARIABLES
# --------------------------------------------------

load_dotenv()

EXA_API_KEY = os.getenv("EXA_API_KEY")


# --------------------------------------------------
# 2. CREATE EXA CLIENT
# --------------------------------------------------

def get_exa_client():
    """Create and return an Exa API client."""

    if not EXA_API_KEY:
        raise ValueError(
            "EXA_API_KEY not found in .env file."
        )

    return Exa(api_key=EXA_API_KEY)


# --------------------------------------------------
# 3. VALIDATE PUBLICATION DATE
# --------------------------------------------------

def is_valid_publication_date(published_date, current_time=None):
    """Check whether an article has a valid, non-future date."""

    if not published_date:
        return False

    try:
        parsed_date = datetime.fromisoformat(
            published_date.replace("Z", "+00:00")
        )

        if parsed_date.tzinfo is None:
            parsed_date = parsed_date.replace(
                tzinfo=timezone.utc
            )

        if current_time is None:
            current_time = datetime.now(timezone.utc)

        return parsed_date <= current_time

    except (ValueError, TypeError, AttributeError):
        return False


# --------------------------------------------------
# 4. SEARCH NEWS FOR ONE STOCK
# --------------------------------------------------

def search_stock_news(
    stock_name,
    ticker,
    search_queries,
    exchange,
    max_results=3
):
    """Search financial news in multiple languages."""

    if not 1 <= max_results <= 5:
        raise ValueError(
            "max_results must be between 1 and 5."
        )

    client = get_exa_client()

    collection_time = datetime.now(timezone.utc)

    start_date = (
        collection_time - timedelta(days=10)
    ).isoformat()

    collection_timestamp = collection_time.isoformat()

    all_articles = []
    seen_urls = set()

    # Search separately for each language
    for language, query in search_queries.items():

        print(
            f"Searching {language} news for {stock_name}..."
        )

        response = client.search(
            query,
            type="lite",
            category="news",
            num_results=max_results,
            start_published_date=start_date,
            contents={
                "text": {
                    "max_characters": 3000
                }
            }
        )

        # Process search results
        for result in response.results:

            # Skip missing, invalid, or future publication dates
            if not is_valid_publication_date(
                result.published_date,
                collection_time
            ):
                print(
                    "Skipping article with invalid or future date:",
                    result.title
                )
                continue

            url = result.url

            # Skip duplicate or missing URLs
            if not url or url in seen_urls:
                continue

            seen_urls.add(url)

            # Extract publisher domain
            source_domain = urlparse(url).netloc.lower()

            source_domain = source_domain.removeprefix(
                "www."
            )

            # Create article record
            article = {

                "stock_name": stock_name,

                "ticker": ticker,

                "exchange": exchange,

                "search_language": language,

                "original_language": None,

                "original_title": result.title,

                "original_text": result.text,

                "translated_title": None,

                "translated_text": None,

                "url": url,

                "source_domain": source_domain,

                "published_date": result.published_date,

                "author": result.author,

                "search_query": query,

                "collection_timestamp": collection_timestamp,

                "language_detection_status": "pending",

                "translation_status": "pending",

                "relevance_status": "pending_manual_review"
            }

            all_articles.append(article)

    print(
        f"Articles found for {stock_name}: "
        f"{len(all_articles)}"
    )

    return all_articles


# --------------------------------------------------
# 5. SAVE NEWS ARTICLES
# --------------------------------------------------

def save_news(
    articles,
    filename="exa_news_raw.json"
):
    """Save only articles with valid publication dates."""

    current_time = datetime.now(timezone.utc)

    valid_articles = []
    seen_urls = set()

    for article in articles:

        published_date = article.get("published_date")

        # Skip missing, invalid, or future dates
        if not is_valid_publication_date(
            published_date,
            current_time
        ):
            continue

        url = article.get("url")

        # Skip missing or duplicate URLs
        if not url or url in seen_urls:
            continue

        seen_urls.add(url)

        valid_articles.append(article)

    output_directory = os.path.join(
        "data",
        "raw"
    )

    os.makedirs(
        output_directory,
        exist_ok=True
    )

    filepath = os.path.join(
        output_directory,
        filename
    )

    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            valid_articles,
            file,
            ensure_ascii=False,
            indent=4
        )

    print("\nNews collection saved successfully.")

    print("Original articles:", len(articles))

    print("Valid articles saved:", len(valid_articles))

    print(
        "Articles excluded:",
        len(articles) - len(valid_articles)
    )

    print("File location:", filepath)


# --------------------------------------------------
# 6. COLLECT NEWS FOR ALL 10 STOCKS
# --------------------------------------------------

def collect_all_stock_news(max_results=3):
    """Collect multilingual news for all configured stocks."""

    all_articles = []

    seen_urls = set()

    print("\nStarting multilingual news collection.")

    print(
        "Total companies:",
        len(STOCK_NEWS_CONFIG)
    )

    for stock_name, details in STOCK_NEWS_CONFIG.items():

        print("\n----------------------------------")

        print("Processing:", stock_name)

        print("----------------------------------")

        articles = search_stock_news(

            stock_name=stock_name,

            ticker=details["ticker"],

            search_queries=details["search_queries"],

            exchange=details["exchange"],

            max_results=max_results
        )

        # Remove duplicate URLs across stocks
        for article in articles:

            url = article["url"]

            if url not in seen_urls:

                seen_urls.add(url)

                all_articles.append(article)

    print("\n----------------------------------")

    print("NEWS COLLECTION COMPLETED")

    print("----------------------------------")

    print(
        "Total unique articles:",
        len(all_articles)
    )

    return all_articles


# --------------------------------------------------
# 7. MAIN PROGRAM
# --------------------------------------------------

if __name__ == "__main__":

    print("\nExa Multilingual News Collector")

    print("----------------------------------")

    print(
        "Companies configured:",
        len(STOCK_NEWS_CONFIG)
    )

    print(
        "Search languages: English, Chinese, Korean"
    )

    print(
        "Maximum results per language: 3"
    )

    print(
        "Collection period: Last 10 days"
    )

    print("----------------------------------")

    print(
        "\nCollector initialized successfully."
    )

    print(
        "No search request has been made."
    )
