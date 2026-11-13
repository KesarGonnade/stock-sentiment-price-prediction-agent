
from src.data_collection.exa_collector import (
    search_stock_news,
    save_news
)

from src.data_collection.stock_news_config import (
    STOCK_NEWS_CONFIG
)


def collect_one_stock(stock_name, max_results=3):

    if stock_name not in STOCK_NEWS_CONFIG:
        raise ValueError(
            f"Stock not found: {stock_name}"
        )

    details = STOCK_NEWS_CONFIG[stock_name]

    print("\nSelected company:", stock_name)
    print("Ticker:", details["ticker"])
    print("Exchange:", details["exchange"])

    articles = search_stock_news(
        stock_name=stock_name,
        ticker=details["ticker"],
        search_queries=details["search_queries"],
        exchange=details["exchange"],
        max_results=max_results
    )

    filename = (
        "exa_"
        + details["ticker"].replace(".", "_")
        + "_news.json"
    )

    save_news(articles, filename)

    return articles


if __name__ == "__main__":

    print("Available companies:\n")

    for index, stock_name in enumerate(
        STOCK_NEWS_CONFIG.keys(),
        start=1
    ):
        print(f"{index}. {stock_name}")

    print("\nCollection script ready.")
    print("No search request has been made.")
