
import os
import time
import json
import requests
from dotenv import load_dotenv

load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
BASE_URL = "https://api.apify.com/v2"
ACTOR_ID = "k-data-lab~telegram-channel-scraper"


def run_telegram_test():
    if not APIFY_API_TOKEN:
        raise ValueError("APIFY_API_TOKEN not found.")

    actor_input = {
    "keywords": ["小米", "小米集团", "1810"],
    "country": "hk",
    "language": "zh",
    "resultType": "messages",
    "maxResults": 10,
    "maxMessagesPerChannel": 10,
    "maxChannelsPerKeyword": 1,
    "since": "10 days",
    "discoverChannels": True
}

    headers = {
        "Authorization": f"Bearer {APIFY_API_TOKEN}"
    }

    print("Starting Xiaomi Hong Kong Telegram collection...")

    response = requests.post(
        f"{BASE_URL}/acts/{ACTOR_ID}/runs",
        headers=headers,
        json=actor_input,
        timeout=60
    )
    response.raise_for_status()

    run_data = response.json()["data"]
    run_id = run_data["id"]

    print("Actor started. Run ID:", run_id)

    status_url = f"{BASE_URL}/actor-runs/{run_id}"
    start_time = time.monotonic()

    while time.monotonic() - start_time < 600:
        status_response = requests.get(
            status_url,
            headers=headers,
            timeout=30
        )
        status_response.raise_for_status()

        status_data = status_response.json()["data"]
        status = status_data["status"]

        print("Status:", status)

        if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
            break

        time.sleep(5)
    else:
        raise TimeoutError(f"Check Apify Console. Run ID: {run_id}")

    if status != "SUCCEEDED":
        raise RuntimeError(f"Actor failed: {status}")

    dataset_id = status_data.get("defaultDatasetId")

    dataset_response = requests.get(
        f"{BASE_URL}/datasets/{dataset_id}/items",
        headers=headers,
        params={"format": "json"},
        timeout=60
    )
    dataset_response.raise_for_status()

    results = dataset_response.json()

    os.makedirs("data/raw", exist_ok=True)

    output_file = "data/raw/xiaomi_telegram_raw.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=4)

    print("\nCollection completed!")
    print("Messages collected:", len(results))
    print("Saved to:", output_file)


if __name__ == "__main__":
    run_telegram_test()
