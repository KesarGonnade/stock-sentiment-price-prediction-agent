
# South Korea Telegram data collection

# Five selected South Korean companies
KOREAN_STOCKS = {
    "Samsung Electronics": {
        "ticker": "005930",
        "keywords": ["삼성전자", "Samsung Electronics", "005930"]
    },
    "SK Hynix": {
        "ticker": "000660",
        "keywords": ["SK하이닉스", "SK Hynix", "000660"]
    },
    "Hyundai Motor": {
        "ticker": "005380",
        "keywords": ["현대차", "Hyundai Motor", "005380"]
    },
    "LG Energy Solution": {
        "ticker": "373220",
        "keywords": ["LG에너지솔루션", "LG Energy Solution", "373220"]
    },
    "Kakao": {
        "ticker": "035720",
        "keywords": ["카카오", "Kakao", "035720"]
    }
}

# Combine all keywords for the Telegram Actor
TELEGRAM_KEYWORDS = [
    keyword
    for stock in KOREAN_STOCKS.values()
    for keyword in stock["keywords"]
]

# Initial collection settings
TELEGRAM_INPUT = {
    "keywords": TELEGRAM_KEYWORDS,
    "country": "kr",
    "language": "ko",
    "resultType": "messages",
    "maxResults": 10,
    "maxMessagesPerChannel": 10,
    "maxChannelsPerKeyword": 2,
    "since": "10 days",
    "discoverChannels": True
}

# Display configuration only — this does NOT start the Actor
if __name__ == "__main__":
    print("South Korea Telegram configuration")
    print("Companies:", len(KOREAN_STOCKS))
    print("Keywords:", len(TELEGRAM_KEYWORDS))
    print("\nKeywords to search:")

    for keyword in TELEGRAM_KEYWORDS:
        print("-", keyword)

    print("\nActor input prepared.")
    print("No scraping has been started.")
