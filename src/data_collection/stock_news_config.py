
# Hong Kong and South Korean stock news configuration

STOCK_NEWS_CONFIG = {

    # -------------------------
    # HONG KONG STOCK EXCHANGE
    # -------------------------

    "Tencent Holdings": {
        "ticker": "0700.HK",
        "exchange": "HKEX",
        "search_queries": {
            "english": (
                "Tencent Holdings 0700 HK stock financial news "
                "earnings business performance"
            ),
            "chinese": (
                "騰訊控股 0700 股價 財經新聞 業績"
            )
        }
    },

    "Alibaba Group": {
        "ticker": "9988.HK",
        "exchange": "HKEX",
        "search_queries": {
            "english": (
                "Alibaba Group 9988 HK stock financial news "
                "earnings business performance"
            ),
            "chinese": (
                "阿里巴巴 9988 港股 股價 財經新聞 業績"
            )
        }
    },

    "HSBC Holdings": {
        "ticker": "0005.HK",
        "exchange": "HKEX",
        "search_queries": {
            "english": (
                "HSBC Holdings 0005 HK stock financial news "
                "earnings banking performance"
            ),
            "chinese": (
                "滙豐控股 0005 港股 股價 財經新聞 業績"
            )
        }
    },

    "Xiaomi Corporation": {
        "ticker": "1810.HK",
        "exchange": "HKEX",
        "search_queries": {
            "english": (
                "Xiaomi Corporation 1810 HK stock financial news "
                "earnings business performance"
            ),
            "chinese": (
                "小米集團 1810 港股 股價 財經新聞 業績"
            )
        }
    },

    "BYD Company": {
        "ticker": "1211.HK",
        "exchange": "HKEX",
        "search_queries": {
            "english": (
                "BYD Company 1211 HK stock financial news "
                "electric vehicles earnings"
            ),
            "chinese": (
                "比亞迪 1211 港股 股價 財經新聞 業績"
            )
        }
    },

    # -------------------------
    # KOREA EXCHANGE
    # -------------------------

    "Samsung Electronics": {
        "ticker": "005930.KS",
        "exchange": "KRX",
        "search_queries": {
            "english": (
                "Samsung Electronics 005930 stock financial news "
                "earnings semiconductor business"
            ),
            "korean": (
                "삼성전자 005930 주가 금융 뉴스 실적"
            )
        }
    },

    "SK Hynix": {
        "ticker": "000660.KS",
        "exchange": "KRX",
        "search_queries": {
            "english": (
                "SK Hynix 000660 stock financial news "
                "earnings semiconductor business"
            ),
            "korean": (
                "SK하이닉스 000660 주가 금융 뉴스 실적"
            )
        }
    },

    "Hyundai Motor": {
        "ticker": "005380.KS",
        "exchange": "KRX",
        "search_queries": {
            "english": (
                "Hyundai Motor 005380 stock financial news "
                "earnings automobile business"
            ),
            "korean": (
                "현대자동차 005380 주가 금융 뉴스 실적"
            )
        }
    },

    "LG Energy Solution": {
        "ticker": "373220.KS",
        "exchange": "KRX",
        "search_queries": {
            "english": (
                "LG Energy Solution 373220 stock financial news "
                "earnings battery business"
            ),
            "korean": (
                "LG에너지솔루션 373220 주가 금융 뉴스 실적"
            )
        }
    },

    "Kakao": {
        "ticker": "035720.KS",
        "exchange": "KRX",
        "search_queries": {
            "english": (
                "Kakao Corporation 035720 stock financial news "
                "earnings business performance"
            ),
            "korean": (
                "카카오 035720 주가 금융 뉴스 실적"
            )
        }
    }
}
if __name__ == "__main__":

    print("Total companies:", len(STOCK_NEWS_CONFIG))

    for stock_name, details in STOCK_NEWS_CONFIG.items():

        print(
            stock_name,
            "|",
            details["ticker"],
            "|",
            list(details["search_queries"].keys())
        )