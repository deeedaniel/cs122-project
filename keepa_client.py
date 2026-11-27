import json
import os
from datetime import datetime, timezone

import pandas as pd
from apify_client import ApifyClient
from dotenv import load_dotenv

from api_client import load_products_csv

# Load APIFY_TOKEN from .env file
load_dotenv()

ACTOR_ID = "silentflow/keepa-scraper"
HISTORY_CSV_PATH = "data/keepa_history.csv"
RAW_JSON_PATH = "data/keepa_raw.json"

HISTORY_COLUMNS = [
    "fetched_at",
    "asin",
    "title",
    "series",  # which history field the point came from, e.g. buyBoxPriceHistory
    "date",
    "price",
]


def run_keepa_actor(asins, history_days=0, include_offers=True):
    """
    Run the Keepa scraper on Apify and return the list of product items.
    history_days=0 returns the full history Keepa has. Costs ~$0.005 per product.
    """
    token = os.getenv("APIFY_TOKEN")
    if not token:
        raise ValueError("Missing APIFY_TOKEN in .env file!")

    asins = [str(a).strip() for a in asins if str(a).strip()]
    if not asins:
        raise ValueError("No ASINs given.")

    client = ApifyClient(token)
    run_input = {
        "asins": asins,
        "marketplace": "us",
        "historyDays": history_days,
        "maxItems": len(asins),  # cap results so we never pay for more than we asked
        "includeOffers": include_offers,
    }

    # .call() starts the actor and waits until the run finishes
    run = client.actor(ACTOR_ID).call(run_input=run_input)
    if run is None or run.status != "SUCCEEDED":
        status = run.status if run else "unknown"
        raise RuntimeError(f"Keepa actor run did not succeed (status: {status})")

    return list(client.dataset(run.default_dataset_id).iterate_items())


def parse_history_items(items):
    """
    Flatten every '...History' field of each product into rows of
    (asin, series, date, price). One row per price change point.
    """
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []

    for item in items:
        asin = str(item.get("asin", "")).strip()
        title = str(item.get("title", "")).strip()

        for field, value in item.items():
            if not field.endswith("History") or not isinstance(value, list):
                continue
            for point in value:
                if not isinstance(point, dict):
                    continue
                price = point.get("price")
                try:
                    price = float(price) if price is not None else None
                except (TypeError, ValueError):
                    price = None
                rows.append({
                    "fetched_at": now_utc,
                    "asin": asin,
                    "title": title,
                    "series": field,
                    "date": point.get("date"),
                    "price": price,
                })

    return pd.DataFrame(rows, columns=HISTORY_COLUMNS)


def load_keepa_history(path=HISTORY_CSV_PATH):
    """Load the saved Keepa history CSV into a DataFrame."""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return pd.DataFrame(columns=HISTORY_COLUMNS)
    try:
        df = pd.read_csv(path)
        for col in HISTORY_COLUMNS:
            if col not in df.columns:
                df[col] = None
        return df[HISTORY_COLUMNS]
    except Exception:
        return pd.DataFrame(columns=HISTORY_COLUMNS)


def save_keepa_history(new_df, path=HISTORY_CSV_PATH):
    """
    Merge new history into the CSV. Each fetch returns a product's full history,
    so the same (asin, series, date) point is kept only once (newest fetch wins).
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existing_df = load_keepa_history(path)

    if existing_df.empty:
        combined = new_df.copy()
    elif new_df.empty:
        combined = existing_df
    else:
        combined = pd.concat([existing_df, new_df], ignore_index=True)

    combined = combined.drop_duplicates(subset=["asin", "series", "date"], keep="last")
    combined = combined.sort_values(by=["asin", "series", "date"]).reset_index(drop=True)
    combined.to_csv(path, index=False)
    return combined


def fetch_keepa_history(asins=None, history_days=90, include_offers=True):
    """
    Fetch Keepa price history for the given ASINs (default: every ASIN in the
    Rainforest CSV), save the raw response and the flattened history CSV.
    """
    if asins is None:
        asins = load_products_csv()["asin"].dropna().unique().tolist()

    print(f"Fetching Keepa history for {len(asins)} ASINs (~${len(asins) * 0.0051:.2f})...")
    items = run_keepa_actor(asins, history_days=history_days, include_offers=include_offers)
    print(f"  Got {len(items)} products back")

    # Keep the raw response so offers and other fields are available without paying again
    os.makedirs(os.path.dirname(RAW_JSON_PATH), exist_ok=True)
    with open(RAW_JSON_PATH, "w") as f:
        json.dump(items, f, indent=2, default=str)

    history_df = parse_history_items(items)
    saved_df = save_keepa_history(history_df)
    print(f"Saved {len(history_df)} history points. Total in database: {len(saved_df)}")
    return saved_df


# --- Analysis Helper Functions ---

def get_keepa_price_history(asin, series=None, path=HISTORY_CSV_PATH):
    """
    Get the price history for one ASIN, sorted by date.
    Pass series (e.g. "buyBoxPriceHistory") to get just one line.
    """
    df = load_keepa_history(path)
    if df.empty:
        return df
    df = df[df["asin"] == asin]
    if series:
        df = df[df["series"] == series]
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
    return df.sort_values(by="date")[["date", "series", "price", "title"]]


def get_available_series(path=HISTORY_CSV_PATH):
    """List which history series were returned (e.g. buyBoxPriceHistory)."""
    df = load_keepa_history(path)
    return sorted(df["series"].dropna().unique().tolist()) if not df.empty else []


# Terminal runner: python keepa_client.py           -> all ASINs from the CSV
#                  python keepa_client.py ASIN1 ... -> just those ASINs (cheap test)
if __name__ == "__main__":
    import sys

    try:
        test_asins = sys.argv[1:] or None
        fetch_keepa_history(asins=test_asins)
        print("Series available:", get_available_series())
    except Exception as e:
        print(f"Error: {e}")
