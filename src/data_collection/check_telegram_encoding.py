
import json

file_path = "data/raw/samsung_telegram_raw.json"

with open(file_path, "r", encoding="utf-8") as file:
    messages = json.load(file)

for index, message in enumerate(messages, start=1):
    print(f"\n{'=' * 50}")
    print("MESSAGE:", index)
    print("CHANNEL:", message.get("channelUsername"))
    print("DATE:", message.get("date"))
    print("KEYWORD:", message.get("keyword"))
    print("TEXT:\n", message.get("text"))
