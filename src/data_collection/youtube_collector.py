
import os
import json
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
BASE_URL = "https://www.googleapis.com/youtube/v3"

OUTPUT_DIR = Path("data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

STOCKS = {
    "samsung": {"name": "Samsung Electronics", "keyword": "삼성전자 주식"},
    "sk_hynix": {"name": "SK Hynix", "keyword": "SK하이닉스 주식"},
    "hyundai": {"name": "Hyundai Motor", "keyword": "현대차 주식"},
    "lg_energy_solution": {
        "name": "LG Energy Solution",
        "keyword": "LG에너지솔루션 주식"
    },
    "kakao": {"name": "Kakao", "keyword": "카카오 주식"}
}

TEN_DAYS_AGO = (
    datetime.now(timezone.utc) - timedelta(days=10)
).isoformat(timespec="seconds").replace("+00:00", "Z")


def youtube_request(endpoint, params):
    params["key"] = API_KEY

    response = requests.get(
        f"{BASE_URL}/{endpoint}",
        params=params,
        timeout=30
    )

    response.raise_for_status()
    return response.json()


def search_videos(stock):
    print(f"\nSearching videos for {stock['name']}...")

    data = youtube_request("search", {
        "part": "snippet",
        "q": stock["keyword"],
        "type": "video",
        "order": "date",
        "publishedAfter": TEN_DAYS_AGO,
        "regionCode": "KR",
        "relevanceLanguage": "ko",
        "maxResults": 5
    })

    videos = []

    for item in data.get("items", []):
        videos.append({
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "channel": item["snippet"]["channelTitle"],
            "published_at": item["snippet"]["publishedAt"]
        })

    print(f"Videos found: {len(videos)}")
    return videos


def collect_comments(video):
    data = youtube_request("commentThreads", {
        "part": "snippet",
        "videoId": video["video_id"],
        "maxResults": 100,
        "order": "time",
        "textFormat": "plainText"
    })

    comments = []

    for item in data.get("items", []):
        snippet = item["snippet"]["topLevelComment"]["snippet"]

        published_at = snippet.get("publishedAt", "")

        if not published_at:
            continue

        comment_date = datetime.fromisoformat(
            published_at.replace("Z", "+00:00")
        )

        cutoff = datetime.now(timezone.utc) - timedelta(days=10)

        if comment_date < cutoff:
            continue

        comments.append({
            "video_id": video["video_id"],
            "video_title": video["title"],
            "channel": video["channel"],
            "author": snippet.get("authorDisplayName"),
            "text": snippet.get("textOriginal", snippet.get("textDisplay")),
            "likes": snippet.get("likeCount", 0),
            "published_at": published_at,
            "source": "YouTube",
            "stock": None
        })

    return comments


def main():
    if not API_KEY:
        raise ValueError("YOUTUBE_API_KEY not found in .env")

    for stock_id, stock in STOCKS.items():
        print(f"\n{'=' * 45}")
        print(f"Processing {stock['name']}")

        try:
            videos = search_videos(stock)
            all_comments = []

            for video in videos:
                try:
                    comments = collect_comments(video)

                    for comment in comments:
                        comment["stock"] = stock["name"]

                    all_comments.extend(comments)

                    print(
                        f"Comments collected from "
                        f"{video['title'][:50]}: {len(comments)}"
                    )

                except requests.exceptions.HTTPError as error:
                    print(f"Could not collect comments: {error}")

            output_file = OUTPUT_DIR / f"{stock_id}_youtube_raw.json"

            with open(output_file, "w", encoding="utf-8") as file:
                json.dump(
                    all_comments,
                    file,
                    ensure_ascii=False,
                    indent=4
                )

            print(f"Saved {len(all_comments)} comments to {output_file}")

        except requests.exceptions.HTTPError as error:
            print(f"API error for {stock['name']}: {error}")
            if error.response is not None:
                print(error.response.text[:1000])
        except requests.exceptions.RequestException as error:
            print(f"Network error: {error}")


if __name__ == "__main__":
    main()
