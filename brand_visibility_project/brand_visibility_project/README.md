# 🛒 Brand Visibility Intelligence Dashboard
**HCL GUVI Project | Author: Shivani**

---

## 📁 Project Structure

```
brand_visibility_project/
│
├── brand_dirty_dataset.csv       ← Dataset 1 (provided)
├── data_cleaning.py              ← Step 1: Clean & preprocess CSV
├── api_extraction.py             ← Step 2: Fetch data from SerpAPI
├── merge_and_load_sql.py         ← Step 3: Merge datasets + load to PostgreSQL
├── dashboard.py                  ← Step 4: Streamlit dashboard
├── requirements.txt
├── .streamlit/
│   └── secrets.toml              ← PostgreSQL credentials (don't commit!)
└── README.md
```

---

## ⚙️ Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Clean the CSV dataset
```bash
python data_cleaning.py
```
→ Creates `brand_clean_dataset.csv`

---

## 🔑 Where to Put Your API Key

Open **`api_extraction.py`** and find line 16:
```python
SERPAPI_KEY = "YOUR_SERPAPI_KEY_HERE"
```
Replace with your actual key from https://serpapi.com

Then run:
```bash
python api_extraction.py
```
→ Creates `api_raw_data.csv` and `api_clean_data.csv`

---

## 🗄️ PostgreSQL Setup

1. Open **pgAdmin** and create a database named `brand_visibility`
2. Open **`merge_and_load_sql.py`** and fill in `DB_CONFIG`:
```python
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "database": "brand_visibility",
    "user":     "postgres",
    "password": "YOUR_DB_PASSWORD",   # ← your password here
}
```
3. Also fill in **`.streamlit/secrets.toml`** with the same credentials
4. Run:
```bash
python merge_and_load_sql.py
```
→ Merges both datasets and loads them into PostgreSQL table `products`

---

## 🚀 Run the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard will open at **http://localhost:8501**

> **Note:** If PostgreSQL is not connected, the dashboard automatically
> falls back to reading `brand_final_dataset.csv` (CSV mode). Everything
> still works — just without live SQL queries.

---

## 📊 Dashboard Tabs

| Tab | Content |
|-----|---------|
| Overview | KPIs, Price Distribution, Products per Keyword, Platform Share |
| Brand Insights | Brand counts, ratings, visibility scores, top-10 rankings |
| Pricing Analysis | Price scatter, discount by brand/platform, avg price per platform |
| Platform Analysis | Product counts, ratings, prices, stacked brand distribution |
| Visibility & Ranking | Ranking histogram, rating vs rank, reviews bubble chart |
| Product Explorer | Searchable & sortable product table |

---

## 🔧 Sidebar Filters (SQL-Powered)

All filters dynamically modify the SQL query sent to PostgreSQL:
- Keyword (multi-select)
- Brand (multi-select)
- Platform (multi-select)
- Price Range (slider)
- Rating Range (slider)
- Max Position / Ranking (slider)
