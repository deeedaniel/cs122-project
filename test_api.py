import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("RAINFOREST_API_KEY")
if not API_KEY:
    raise ValueError("RAINFOREST_API_KEY not found. Check your .env file.")

params = {
    "api_key": API_KEY,
    "type": "bestsellers",
    "url": "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics",
}

response = requests.get("https://api.rainforestapi.com/request", params=params, timeout=30)
response.raise_for_status()
data = response.json()

# Cache the raw JSON locally so you can test CSV parsing without spending extra credits
with open("sample_response.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print("Request Info:", json.dumps(data.get("request_info", {}), indent=2))

bestsellers = data.get("bestsellers", [])
print(f"\nTotal items returned: {len(bestsellers)}")

if bestsellers:
    print("\nFirst item structure:")
    print(json.dumps(bestsellers[0], indent=2))