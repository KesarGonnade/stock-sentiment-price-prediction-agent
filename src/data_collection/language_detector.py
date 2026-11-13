
import re

from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Make language detection reproducible
DetectorFactory.seed = 0


def detect_article_language(text):
    """Detect English, Chinese, and Korean article languages."""

    if not text or not text.strip():
        return "unknown"

    # Remove URLs and numbers before language detection
    cleaned_text = re.sub(r"https?://\S+", " ", text)
    cleaned_text = re.sub(r"\d+", " ", cleaned_text)

    # Count Chinese characters and Korean Hangul characters
    chinese_count = len(
        re.findall(r"[\u4e00-\u9fff]", cleaned_text)
    )

    korean_count = len(
        re.findall(r"[\uac00-\ud7af]", cleaned_text)
    )

    # Chinese and Korean script detection
    if chinese_count > 0 and chinese_count >= korean_count:
        return "zh"

    if korean_count > 0:
        return "ko"

    # Use langdetect for remaining languages
    try:
        return detect(cleaned_text)

    except LangDetectException:
        return "unknown"


if __name__ == "__main__":

    test_articles = [
        "Tencent reported strong revenue growth.",
        "高盛點名中國互聯網龍頭股，佈局第三季度財報行情",
        "腾讯发布了新的人工智能模型。",
        "삼성전자가 새로운 반도체 기술을 발표했습니다."
    ]

    for article in test_articles:

        language = detect_article_language(article)

        print("Article:", article)
        print("Detected language:", language)
        print("--------------------------------")
