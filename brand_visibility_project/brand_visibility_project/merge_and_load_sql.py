"""
Step 3: Merge CSV + API Data → Load into PostgreSQL
Brand Visibility Intelligence Dashboard - HCL GUVI Project

HOW TO USE:
  1. Make sure you have run:
       python data_cleaning.py        (creates brand_clean_dataset.csv)
       python api_extraction.py       (creates api_clean_data.csv)
  2. Set your PostgreSQL credentials below (DB_CONFIG section)
  3. Run:  python merge_and_load_sql.py
"""

import pandas as pd
import numpy as np
import os
from sqlalchemy import create_engine, text
from data_cleaning import clean_dataset, load_csv

# ══════════════════════════════════════════════════
# 🗄️  POSTGRESQL CONNECTION CONFIG – EDIT THESE
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "brand_visibility",   # create this DB in pgAdmin first
    "user": "postgres",               # your PostgreSQL username
    "password": "12345",   # your PostgreSQL password
}
# ══════════════════════════════════════════════════

TABLE_NAME = "products"


def get_engine():
    url = (
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    return create_engine(url)


# ─────────────────────────────────────────────
# MERGE
# ─────────────────────────────────────────────
def merge_datasets() -> pd.DataFrame:
    # --- Load & clean CSV dataset ---
    print("[1] Loading CSV dataset...")
    csv_raw = load_csv("brand_dirty_dataset.csv")
    csv_clean = clean_dataset(csv_raw, source_label="csv")

    # --- Load API dataset if it exists ---
    api_path = "api_clean_data.csv"
    if os.path.exists(api_path):
        print("[2] Loading API dataset...")
        api_clean = pd.read_csv(api_path)
        print(f"    API rows: {len(api_clean)}")
    else:
        print("[2] No API data found (api_clean_data.csv missing).")
        print("    Run api_extraction.py first to fetch live data.")
        print("    Proceeding with CSV data only.\n")
        api_clean = pd.DataFrame()

    # --- Combine ---
    if not api_clean.empty:
        # Align columns
        all_cols = list(
            dict.fromkeys(csv_clean.columns.tolist() + api_clean.columns.tolist())
        )
        for col in all_cols:
            if col not in csv_clean.columns:
                csv_clean[col] = np.nan
            if col not in api_clean.columns:
                api_clean[col] = np.nan

        merged = pd.concat([csv_clean, api_clean[all_cols]], ignore_index=True)
    else:
        merged = csv_clean

    # --- Drop duplicates across sources ---
    merged.drop_duplicates(subset=["title", "price"], keep="first", inplace=True)
    merged.reset_index(drop=True, inplace=True)

    print(f"\n[Merge] Final dataset: {merged.shape[0]} rows × {merged.shape[1]} cols")
    merged.to_csv("brand_final_dataset.csv", index=False)
    print("[✓] Saved → brand_final_dataset.csv")
    return merged


# ─────────────────────────────────────────────
# LOAD INTO POSTGRESQL
# ─────────────────────────────────────────────
def load_to_postgres(df: pd.DataFrame):
    if DB_CONFIG["password"] == "YOUR_DB_PASSWORD":
        print("\n[WARNING] PostgreSQL password not set. Skipping DB load.")
        print("  Open merge_and_load_sql.py and fill in DB_CONFIG.")
        return

    print("\n[3] Connecting to PostgreSQL...")
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("    Connected ✓")
    except Exception as e:
        print(f"    Connection FAILED: {e}")
        print("    Make sure PostgreSQL is running and the database exists.")
        return

    print(f"[4] Loading {len(df)} rows into table '{TABLE_NAME}'...")
    try:
        df.to_sql(
            TABLE_NAME,
            engine,
            if_exists="replace",   # replace on each run
            index=False,
            chunksize=500,
        )
        print(f"[✓] Data loaded into PostgreSQL table '{TABLE_NAME}'")
    except Exception as e:
        print(f"[ERROR] Failed to load data: {e}")
        return

    # Create useful indexes
    with engine.connect() as conn:
        try:
            conn.execute(text(f'CREATE INDEX IF NOT EXISTS idx_keyword ON "{TABLE_NAME}" (keyword);'))
            conn.execute(text(f'CREATE INDEX IF NOT EXISTS idx_brand   ON "{TABLE_NAME}" (brand);'))
            conn.execute(text(f'CREATE INDEX IF NOT EXISTS idx_platform ON "{TABLE_NAME}" (platform);'))
            conn.commit()
            print("[✓] Indexes created")
        except Exception as e:
            print(f"[Warning] Index creation: {e}")

    print("\n[Done] You can now run:  streamlit run dashboard.py")


if __name__ == "__main__":
    df = merge_datasets()
    load_to_postgres(df)
