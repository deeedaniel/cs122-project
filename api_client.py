import os
from datetime import datetime, timezone
import pandas as pd
import requests
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()

CSV_PATH = "data/amazon_products.csv"

# 3 core categories for daily gathering
# Note: Using Amazon bestsellers URLs because Rainforest API's category_id for
# Home & Kitchen doesn't match standard slugs, while direct URLs work consistently.
CATEGORIES = {
    "appliances": {
        "name": "Appliances",
        "url": "https://www.amazon.com/Best-Sellers-Appliances/zgbs/appliances",
    },
    "electronics": {
        "name": "Electronics",
        "url": "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics",
    },
    "home-garden": {
        "name": "Home & Kitchen",
        "url": "https://www.amazon.com/Best-Sellers-Home-Kitchen/zgbs/home-garden",
    },
}

CSV_COLUMNS = [
    "captured_at",
    "category_id",
    "category",
    "rank",
    "asin",
    "title",
    "price",
    "price_raw",
    "rating",
    "ratings_total",
    "image_url",
]


def parse_bestsellers_json(data, category_id, category_name):
    """Extract product records from Rainforest API JSON response into a DataFrame."""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    items = data.get("bestsellers", [])
    rows = []

    for item in items:
        # Rank fallback to position if rank is missing
        rank = item.get("rank")
        if rank is None:
            rank = item.get("position")
        if rank is not None:
            try:
                rank = int(rank)
            except:
                pass

        # Price fallback: check price.value, then price_lower.value
        price = None
        price_raw = ""
        p_obj = item.get("price") or {}
        p_low = item.get("price_lower") or {}

        if p_obj.get("value") is not None:
            try:
                price = float(p_obj["value"])
            except:
                price = None
        elif p_low.get("value") is not None:
            try:
                price = float(p_low["value"])
            except:
                price = None

        if p_obj.get("raw"):
            price_raw = str(p_obj["raw"])
        elif p_low.get("raw"):
            price_raw = str(p_low["raw"])

        # Ratings
        rating = item.get("rating")
        if rating is not None:
            try:
                rating = float(rating)
            except:
                rating = None

        ratings_total = item.get("ratings_total")
        if ratings_total is not None:
            try:
                ratings_total = int(ratings_total)
            except:
                ratings_total = None

        rows.append({
            "captured_at": now_utc,
            "category_id": category_id,
            "category": category_name,
            "rank": rank,
            "asin": str(item.get("asin", "")).strip(),
            "title": str(item.get("title", "")).strip(),
            "price": price,
            "price_raw": price_raw,
            "rating": rating,
            "ratings_total": ratings_total,
            "image_url": str(item.get("image", "")).strip(),
        })

    return pd.DataFrame(rows, columns=CSV_COLUMNS)


def fetch_category_bestsellers(category_id):
    """Fetch bestsellers for one category from Rainforest API."""
    api_key = os.getenv("RAINFOREST_API_KEY")
    if not api_key:
        raise ValueError("Missing RAINFOREST_API_KEY in .env file!")

    # Normalize category input (e.g. appliances, bestsellers_appliances, Appliances)
    cat_key = category_id.lower().replace("bestsellers_", "")
    if cat_key not in CATEGORIES:
        for k, v in CATEGORIES.items():
            if category_id.lower() in (k, v["name"].lower()):
                cat_key = k
                break

    if cat_key not in CATEGORIES:
        raise ValueError(f"Unknown category '{category_id}'. Valid options: {list(CATEGORIES.keys())}")

    category_info = CATEGORIES[cat_key]

    params = {
        "api_key": api_key,
        "type": "bestsellers",
        "url": category_info["url"],
    }

    res = requests.get("https://api.rainforestapi.com/request", params=params, timeout=30)
    res.raise_for_status()
    data = res.json()

    return parse_bestsellers_json(data, cat_key, category_info["name"])


def load_products_csv(path=CSV_PATH):
    """Load existing products CSV into a DataFrame."""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return pd.DataFrame(columns=CSV_COLUMNS)

    try:
        # Ignore comments if file still has template header comments
        df = pd.read_csv(path, comment="#")
        if df.empty:
            return pd.DataFrame(columns=CSV_COLUMNS)
        # Ensure all columns exist
        for col in CSV_COLUMNS:
            if col not in df.columns:
                df[col] = None
        return df[CSV_COLUMNS]
    except:
        return pd.DataFrame(columns=CSV_COLUMNS)


def save_products_csv(new_df, path=CSV_PATH):
    """Append new products to CSV and deduplicate on (capture_date, category_id, asin)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)

    if new_df.empty:
        return load_products_csv(path)

    existing_df = load_products_csv(path)
    if existing_df.empty:
        combined = new_df.copy()
    else:
        combined = pd.concat([existing_df, new_df], ignore_index=True)

    # Extract YYYY-MM-DD from captured_at for same-day deduplication
    combined["_date"] = combined["captured_at"].astype(str).str.slice(0, 10)
    # Keep the latest fetch on the same day for each product in that category
    combined = combined.drop_duplicates(subset=["_date", "category_id", "asin"], keep="last")
    combined = combined.drop(columns=["_date"])
    combined = combined.reset_index(drop=True)

    combined.to_csv(path, index=False)
    return combined


def fetch_all_daily_categories():
    """Fetch all 3 core categories and append them to CSV (uses 3 credits)."""
    dfs = []
    for cat_key, info in CATEGORIES.items():
        print(f"Fetching {info['name']}...")
        df = fetch_category_bestsellers(cat_key)
        print(f"  Got {len(df)} items for {info['name']}")
        dfs.append(df)

    if dfs:
        all_df = pd.concat(dfs, ignore_index=True)
        saved_df = save_products_csv(all_df)
        print(f"Saved total of {len(saved_df)} records to {CSV_PATH}")
        return saved_df

    return pd.DataFrame(columns=CSV_COLUMNS)


# Terminal runner for daily collection: python api_client.py
if __name__ == "__main__":
    print("Running daily Rainforest API bestsellers collection...")
    try:
        df = fetch_all_daily_categories()
        print("Done! Products per category in CSV:")
        print(df["category"].value_counts())
    except Exception as e:
        print(f"Error: {e}")
