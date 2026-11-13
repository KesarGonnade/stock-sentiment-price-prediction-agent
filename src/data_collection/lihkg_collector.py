
import os
import time
import json
import requests

from src.data_collection.apify_collector import (
    APIFY_API_TOKEN,
    BASE_URL,
    get_headers,
    test_apify_connection
)

ACTOR_ID = "claude_code_reviewer~lihkg-scraper-en"


def prepare_search_input(keyword, max_items=5):
    """Prepare input for searching LIHKG threads."""

    return {
        "mode": "search",
        "keywords": [keyword],
        "maxItems": max_items,
        "dateFrom": "10d",
        "order": "desc_reply_time",
        "aiLabels": False,
        "onlyNew": False,
        "proxyConfiguration": {
            "useApifyProxy": True
        }
    }


def prepare_thread_input(thread_ids):
    """Prepare input for retrieving full threads and replies."""

    return {
        "mode": "thread",
        "threadIds": [str(thread_id) for thread_id in thread_ids],
        "maxItems": len(thread_ids),
        "proxyConfiguration": {
            "useApifyProxy": True
        }
    }


def run_actor(actor_input, output_filename):
    """Run LIHKG Actor, wait for completion and save results."""

    if not APIFY_API_TOKEN:
        raise ValueError("Apify API token not found.")

    run_url = f"{BASE_URL}/acts/{ACTOR_ID}/runs"

    print("\nStarting LIHKG Actor...")

    response = requests.post(
        run_url,
        headers=get_headers(),
        json=actor_input,
        timeout=60
    )

    response.raise_for_status()

    run_data = response.json()["data"]
    run_id = run_data["id"]

    print("Actor started.")
    print("Run ID:", run_id)

    status_url = f"{BASE_URL}/actor-runs/{run_id}"

    max_wait_time = 600
    start_time = time.monotonic()

    while time.monotonic() - start_time < max_wait_time:

        status_response = requests.get(
            status_url,
            headers=get_headers(),
            timeout=30
        )

        status_response.raise_for_status()

        status_data = status_response.json()["data"]
        status = status_data["status"]

        print("Current status:", status)

        if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
            break

        time.sleep(5)

    else:
        raise TimeoutError(
            f"Actor timed out. Run ID: {run_id}"
        )

    if status != "SUCCEEDED":
        raise RuntimeError(
            f"LIHKG Actor failed. Status: {status}"
        )

    dataset_id = status_data.get("defaultDatasetId")

    if not dataset_id:
        raise RuntimeError("No dataset ID returned.")

    dataset_url = f"{BASE_URL}/datasets/{dataset_id}/items"

    dataset_response = requests.get(
        dataset_url,
        headers=get_headers(),
        params={"format": "json"},
        timeout=60
    )

    dataset_response.raise_for_status()

    results = dataset_response.json()

    output_directory = os.path.join("data", "raw")
    os.makedirs(output_directory, exist_ok=True)

    filepath = os.path.join(output_directory, output_filename)

    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(
            results,
            file,
            ensure_ascii=False,
            indent=4
        )

    print("\nCollection completed!")
    print("Records collected:", len(results))
    print("Saved to:", filepath)

    return results


def run_lihkg_actor(keyword, max_items=5):
    """Stage 1: Search for relevant LIHKG threads."""

    if not 1 <= max_items <= 5:
        raise ValueError("max_items must be between 1 and 5.")

    actor_input = prepare_search_input(keyword, max_items)

    safe_keyword = "".join(
        character for character in keyword.lower()
        if character.isalnum() or character in ("-", "_")
    )

    filename = f"lihkg_search_{safe_keyword}.json"

    print(f"Searching LIHKG for: {keyword}")

    return run_actor(actor_input, filename)


def run_lihkg_thread(thread_ids):
    """Stage 2: Retrieve full content and replies."""

    if not thread_ids:
        raise ValueError("At least one thread ID is required.")

    if len(thread_ids) > 5:
        raise ValueError("For initial testing, use at most 5 threads.")

    actor_input = prepare_thread_input(thread_ids)

    filename = f"lihkg_threads_{'_'.join(map(str, thread_ids))}.json"

    print("Retrieving full thread content...")

    return run_actor(actor_input, filename)


if __name__ == "__main__":

    if test_apify_connection():

        print("\nApify connection verified.")

        run_lihkg_actor("騰訊控股", max_items=1)
