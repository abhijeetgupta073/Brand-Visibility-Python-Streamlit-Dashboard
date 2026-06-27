"""
Step 1 & 2: Data Cleaning + Feature Engineering
Brand Visibility Intelligence Dashboard - HCL GUVI Project
"""

import pandas as pd
import numpy as np
import re
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# 1. LOAD CSV
# ─────────────────────────────────────────────
def load_csv(path="brand_dirty_dataset.csv"):
    df = pd.read_csv(path)
    print(f"[CSV] Loaded: {df.shape[0]} rows × {df.shape[1]} cols")
    return df


# ─────────────────────────────────────────────
# 2. CLEAN PRICE
# ─────────────────────────────────────────────
def clean_price(val):
    if pd.isna(val):
        return np.nan
    val = str(val).strip()
    if val.lower() in ["not available", "na", "n/a", "", "none", "nan"]:
        return np.nan
    # Remove ₹, $, commas, spaces
    val = re.sub(r"[₹$,\s]", "", val)
    try:
        return float(val)
    except ValueError:
        return np.nan


# ─────────────────────────────────────────────
# 3. CLEAN REVIEWS
# ─────────────────────────────────────────────
def clean_reviews(val):
    if pd.isna(val):
        return np.nan
    val = str(val).strip()
    if val.lower() in ["many", "not available", "na", "", "none", "nan"]:
        return np.nan
    val = re.sub(r"[,\s]", "", val)
    try:
        return int(float(val))
    except ValueError:
        return np.nan


# ─────────────────────────────────────────────
# 4. EXTRACT BRAND FROM TITLE
# ─────────────────────────────────────────────
KNOWN_BRANDS = [
    "Samsung", "Apple", "Sony", "LG", "Boat", "OnePlus", "Xiaomi", "Redmi",
    "Realme", "Vivo", "Oppo", "HP", "Dell", "Lenovo", "Asus", "Acer",
    "Philips", "Bosch", "Havells", "Bajaj", "Prestige", "Morphy", "Panasonic",
    "Whirlpool", "IFB", "Godrej", "Hitachi", "Haier", "TCL", "Hisense",
    "Noise", "Fire-Boltt", "Zebronics", "Logitech", "JBL", "Skullcandy",
    "MI", "POCO", "iQOO", "Nothing", "Dyson", "Eureka"
]

def extract_brand(title):
    if pd.isna(title):
        return "Unknown"
    title_lower = str(title).lower()
    for brand in KNOWN_BRANDS:
        if brand.lower() in title_lower:
            return brand
    # Fallback: first word
    words = str(title).strip().split()
    return words[0] if words else "Unknown"


# ─────────────────────────────────────────────
# 5. PRICE RANGE CATEGORIZATION
# ─────────────────────────────────────────────
def categorize_price(price):
    if pd.isna(price):
        return "Unknown"
    if price < 500:
        return "Budget (<500)"
    elif price < 2000:
        return "Economy (500-2K)"
    elif price < 5000:
        return "Mid-Range (2K-5K)"
    elif price < 15000:
        return "Premium (5K-15K)"
    elif price < 50000:
        return "High-End (15K-50K)"
    else:
        return "Luxury (50K+)"


# ─────────────────────────────────────────────
# 6. VISIBILITY SCORE (based on position)
# ─────────────────────────────────────────────
def compute_visibility_score(position, max_pos=40):
    if pd.isna(position):
        return 0.0
    return round(max(0, (max_pos - position) / max_pos), 4)


# ─────────────────────────────────────────────
# 7. DISCOUNT PERCENTAGE
# ─────────────────────────────────────────────
def compute_discount(price, raw_price):
    if pd.isna(price) or pd.isna(raw_price) or raw_price == 0:
        return 0.0
    if raw_price <= price:
        return 0.0
    return round(((raw_price - price) / raw_price) * 100, 2)


# ─────────────────────────────────────────────
# 8. FULL CLEANING PIPELINE
# ─────────────────────────────────────────────
def clean_dataset(df: pd.DataFrame, source_label: str = "csv") -> pd.DataFrame:
    df = df.copy()

    # ── Standardize column names ──
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # ── Rename 'reviews' column if it exists as 'Reviews' ──
    df.rename(columns={"reviews": "reviews", "Reviews": "reviews"}, inplace=True)

    # ── Clean title ──
    df["title"] = df["title"].astype(str).str.strip()
    df["title"] = df["title"].str.replace(r"[!@#$%^&*]{2,}", "", regex=True)
    df["title"] = df["title"].str.strip()

    # ── Clean price ──
    df["price"] = df["price"].apply(clean_price)

    # ── raw_price: if not present, same as price (CSV may not have it) ──
    if "raw_price" not in df.columns:
        df["raw_price"] = np.nan
    else:
        df["raw_price"] = df["raw_price"].apply(clean_price)

    # ── Clean rating ──
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    # Ratings must be 0–5
    df.loc[df["rating"] > 5, "rating"] = np.nan
    df.loc[df["rating"] < 0, "rating"] = np.nan

    # ── Clean reviews ──
    df["reviews"] = df["reviews"].apply(clean_reviews)

    # ── Standardize platform ──
    df["platform"] = df["platform"].astype(str).str.strip().str.title()
    platform_map = {
        "Amazon": "Amazon", "Flipkart": "Flipkart", "Croma": "Croma",
        "Reliance Digital": "Reliance Digital", "Myntra": "Myntra",
        "Meesho": "Meesho", "Snapdeal": "Snapdeal", "Jiomart": "JioMart"
    }
    df["platform"] = df["platform"].replace(platform_map)

    # ── Standardize delivery ──
    if "delivery" in df.columns:
        df["delivery"] = df["delivery"].astype(str).str.strip()
        df["delivery"] = df["delivery"].replace(
            {"nan": "Unknown", "None": "Unknown", "": "Unknown"}
        )
    else:
        df["delivery"] = "Unknown"

    # ── Position ──
    if "position" not in df.columns:
        # Assign sequential position within keyword groups
        df["position"] = df.groupby("keyword").cumcount() + 1
    else:
        df["position"] = pd.to_numeric(df["position"], errors="coerce")
        df["position"] = df["position"].fillna(df.groupby("keyword")["position"].transform("max") + 1)
        df["position"] = df["position"].astype(int)

    # ── Handle missing price: fill with median per keyword ──
    df["price"] = df.groupby("keyword")["price"].transform(
        lambda x: x.fillna(x.median())
    )
    df["price"] = df["price"].fillna(df["price"].median())

    # ── Handle missing rating: fill with median per keyword ──
    df["rating"] = df.groupby("keyword")["rating"].transform(
        lambda x: x.fillna(x.median())
    )
    df["rating"] = df["rating"].fillna(df["rating"].median())

    # ── Handle missing reviews: fill 0 ──
    df["reviews"] = df["reviews"].fillna(0).astype(int)

    # ── Remove price <= 0 ──
    df = df[df["price"] > 0].copy()

    # ── Remove duplicates (title + price) ──
    df.drop_duplicates(subset=["title", "price"], keep="first", inplace=True)

    # ── Cap price outliers at 99th percentile ──
    p99 = df["price"].quantile(0.99)
    df["price"] = df["price"].clip(upper=p99)

    # ─── FEATURE ENGINEERING ───
    df["brand"] = df["title"].apply(extract_brand)
    df["price_range"] = df["price"].apply(categorize_price)
    df["visibility_score"] = df["position"].apply(compute_visibility_score)
    df["discount_pct"] = df.apply(
        lambda r: compute_discount(r["price"], r["raw_price"]), axis=1
    )

    # ── Link / thumbnail: add blanks if absent ──
    if "link" not in df.columns:
        df["link"] = ""
    if "thumbnail" not in df.columns:
        df["thumbnail"] = ""

    # ── Add source label ──
    df["data_source"] = source_label

    # ── Final column order ──
    cols = [
        "keyword", "title", "brand", "price", "raw_price", "rating",
        "reviews", "platform", "position", "delivery", "discount_pct",
        "price_range", "visibility_score", "link", "thumbnail", "data_source"
    ]
    df = df[[c for c in cols if c in df.columns]]
    df.reset_index(drop=True, inplace=True)

    print(f"[{source_label}] After cleaning: {df.shape[0]} rows × {df.shape[1]} cols")
    return df


if __name__ == "__main__":
    raw = load_csv("brand_dirty_dataset.csv")
    clean = clean_dataset(raw, source_label="csv")
    clean.to_csv("brand_clean_dataset.csv", index=False)
    print("[✓] Saved → brand_clean_dataset.csv")
    print(clean.head(3).to_string())
