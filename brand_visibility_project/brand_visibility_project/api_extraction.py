"""
Step 2: API Data Extraction using SerpAPI (Google Shopping)
Brand Visibility Intelligence Dashboard - HCL GUVI Project

HOW TO USE:
  1. Open this file
  2. Replace YOUR_SERPAPI_KEY_HERE with your actual SerpAPI key
  3. Run:  python api_extraction.py
"""

import requests
import pandas as pd
import numpy as np
import time
import json
import os

# ══════════════════════════════════════════════════
# 🔑  PUT YOUR SERPAPI KEY HERE
SERPAPI_KEY = "c46948c6eb74a4afa1abd346c9a15869703d4b4b208ff21f7ed1611a0ea042b2"
# ══════════════════════════════════════════════════

# Keywords to search (Indian e-commerce context)
KEYWORDS = [
    "Air Fryer India",
    "Camera",
    "Gaming Laptop",
    "Men Running Shoes",
    "Microwave Oven Convection",
    "Bluetooth Speaker",
    "Headphones",
    "Laptop",
    "Office Chair Ergonomic",
    "Power Bank Fast Charging",
]

# Max products per keyword
RESULTS_PER_KEYWORD = 40

# Google Shopping API endpoint
SERPAPI_URL = "https://serpapi.com/search"


def fetch_keyword(keyword: str, api_key: str) -> list[dict]:
    """Fetch Google Shopping results for one keyword."""
    params = {
        "engine": "google_shopping",
        "q": keyword,
        "api_key": api_key,
        "hl": "en",
        "gl": "in",          # India
        "num": RESULTS_PER_KEYWORD,
        "tbs": "mr:1",       # show more results
    }
    try:
        resp = requests.get(SERPAPI_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            print(f"  [API ERROR] {keyword}: {data['error']}")
            return []

        items = data.get("shopping_results", [])
        print(f"  [{keyword}] → {len(items)} products fetched")
        return items

    except requests.exceptions.RequestException as e:
        print(f"  [REQUEST ERROR] {keyword}: {e}")
        return []


def parse_product(item: dict, keyword: str, position: int) -> dict:
    """Parse a single shopping result dict into a flat row."""
    # Price parsing
    raw_price_str = item.get("price", "")
    extracted_price = item.get("extracted_price", None)

    # Try to get numeric price
    if extracted_price is None:
        price_clean = str(raw_price_str).replace("₹", "").replace(",", "").strip()
        try:
            extracted_price = float(price_clean.split("/")[0])
        except (ValueError, AttributeError):
            extracted_price = None

    # Original / raw price (before discount)
    raw_price = item.get("old_price", None)
    if raw_price is None:
        raw_price_extracted = item.get("original_price_extracted", None)
    else:
        try:
            raw_price = float(str(raw_price).replace("₹", "").replace(",", "").strip().split("/")[0])
        except (ValueError, AttributeError):
            raw_price = None

    # Rating & reviews
    rating = item.get("rating", None)
    reviews = item.get("reviews", None)
    if reviews is not None:
        try:
            reviews = int(str(reviews).replace(",", ""))
        except ValueError:
            reviews = None

    # Platform / source
    platform = item.get("source", item.get("seller", "Unknown"))

    # Delivery
    extensions = item.get("extensions", [])
    delivery = "Unknown"
    for ext in extensions:
        if any(kw in str(ext).lower() for kw in ["free delivery", "delivery", "shipping"]):
            delivery = ext
            break

    return {
        "keyword": keyword,
        "title": item.get("title", ""),
        "price": extracted_price,
        "raw_price": raw_price,
        "rating": rating,
        "reviews": reviews,
        "platform": platform,
        "position": item.get("position", position),
        "delivery": delivery,
        "link": item.get("product_link", item.get("link", "")),
        "thumbnail": item.get("thumbnail", ""),
    }


def fetch_all_keywords(api_key: str) -> pd.DataFrame:
    """Loop over all keywords and return combined raw DataFrame."""
    all_rows = []

    for keyword in KEYWORDS:
        print(f"\n→ Searching: '{keyword}'")
        items = fetch_keyword(keyword, api_key)

        for pos, item in enumerate(items, start=1):
            row = parse_product(item, keyword, pos)
            all_rows.append(row)

        time.sleep(1.5)   # polite delay between API calls

    if not all_rows:
        print("[WARNING] No data fetched. Check your API key and network.")
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    print(f"\n[API] Total raw rows fetched: {len(df)}")
    return df


def main():
    if SERPAPI_KEY == "YOUR_SERPAPI_KEY_HERE":
        print("=" * 60)
        print("  ❌  ERROR: Please set your SerpAPI key in this file.")
        print("  Open api_extraction.py and replace:")
        print("      SERPAPI_KEY = 'YOUR_SERPAPI_KEY_HERE'")
        print("  with your actual key from https://serpapi.com")
        print("=" * 60)
        return

    print("=" * 60)
    print("  Brand Visibility Intelligence – API Extraction")
    print("=" * 60)

    raw_df = fetch_all_keywords(SERPAPI_KEY)

    if raw_df.empty:
        return

    # Save raw API data
    raw_df.to_csv("api_raw_data.csv", index=False)
    print("\n[✓] Saved raw API data → api_raw_data.csv")

    # Apply cleaning pipeline
    from data_cleaning import clean_dataset
    clean_df = clean_dataset(raw_df, source_label="api")
    clean_df.to_csv("api_clean_data.csv", index=False)
    print("[✓] Saved cleaned API data → api_clean_data.csv")


if __name__ == "__main__":
    main()
