
import os
import time
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
BASE_URL = "https://api.apify.com/v2"

# LIHKG Scraper Actor ID
ACTOR_ID = "claude_code_reviewer~lihkg-scraper-en"


def get_headers():
    """Create headers for Apify API requests."""

    return {
        "Authorization": f"Bearer {APIFY_API_TOKEN}"
    }


def test_apify_connection():
    """Check whether the Apify API token works."""

    if not APIFY_API_TOKEN:
        print("ERROR: Apify API token not found.")
        return False

    try:
        response = requests.get(
            f"{BASE_URL}/users/me",
            headers=get_headers(),
            timeout=30
        )

        response.raise_for_status()

        user = response.json()["data"]

        print("Apify connection successful!")
        print("Username:", user.get("username"))

        return True

    except requests.exceptions.RequestException as error:
        print("Apify connection failed:", error)
        return False


def prepare_lihkg_input(keyword, max_items=5):
    """Prepare input for LIHKG search."""

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


def run_lihkg_actor(keyword, max_items=5):
    """
    Start LIHKG Actor, wait for completion,
    retrieve results and save them as JSON.
    """

    if not APIFY_API_TOKEN:
        raise ValueError("Apify API token not found.")

    if not 1 <= max_items <= 5:
        raise ValueError("For the initial test, max_items must be between 1 and 5.")

    actor_input = prepare_lihkg_input(keyword, max_items)

    # Step 1: Start Actor
    run_url = f"{BASE_URL}/acts/{ACTOR_ID}/runs"

    print(f"Starting LIHKG search for: {keyword}")

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

    # Step 2: Monitor Actor
    status_url = f"{BASE_URL}/actor-runs/{run_id}"

    max_wait_time = 600  # 10 minutes
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

        if status in [
            "SUCCEEDED",
            "FAILED",
            "ABORTED",
            "TIMED-OUT"
        ]:
            break

        time.sleep(5)

    else:
        raise TimeoutError(
            "Python stopped waiting after 10 minutes. "
            "The Actor may still be running. "
            f"Check Apify Console using Run ID: {run_id}"
        )

    if status != "SUCCEEDED":
        raise RuntimeError(
            f"LIHKG Actor did not succeed. Final status: {status}. "
            f"Run ID: {run_id}"
        )

    # Step 3: Retrieve dataset ID
    dataset_id = status_data.get("defaultDatasetId")

    if not dataset_id:
        raise RuntimeError("No dataset ID returned by the Actor.")

    # Step 4: Download collected data
    dataset_url = f"{BASE_URL}/datasets/{dataset_id}/items"

    dataset_response = requests.get(
        dataset_url,
        headers=get_headers(),
        params={"format": "json"},
        timeout=60
    )

    dataset_response.raise_for_status()

    results = dataset_response.json()

    # Step 5: Save raw data
    output_directory = os.path.join("data", "raw")
    os.makedirs(output_directory, exist_ok=True)

    safe_keyword = "".join(
        character for character in keyword.lower()
        if character.isalnum() or character in ("-", "_")
    )

    filename = os.path.join(
        output_directory,
        f"lihkg_{safe_keyword}_raw.json"
    )

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(
            results,
            file,
            ensure_ascii=False,
            indent=4
        )

    print("\nLIHKG collection completed!")
    print("Results collected:", len(results))
    print("Saved to:", filename)

    return results


if __name__ == "__main__":

    if test_apify_connection():

        print("\nApify connection verified.")

        # SAFETY:
        # This line starts a PAID Actor run.
        # Keep it commented until you approve the test.

        # run_lihkg_actor("Tencent", max_items=5)
