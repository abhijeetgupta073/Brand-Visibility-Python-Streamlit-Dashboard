# Brand-Visibility-Python-Streamlit-Dashboard
Built an E-Commerce Brand Visibility Intelligence Dashboard using Python, SerpAPI, PostgreSQL &amp; Streamlit. Includes ETL pipeline, data cleaning, feature engineering (visibility score, discount %), EDA, and 6-tab interactive dashboard with SQL-powered live filters. HCL-GUVI Capstone Project.
🛒 Brand Visibility Intelligence Dashboard

HCL-GUVI Capstone Project | E-Commerce Analytics & Business Intelligence

<img width="1905" height="930" alt="image" src="https://github.com/user-attachments/assets/23ecf29b-c032-4a29-85bf-f0b67688e05f" />


📌 Project Overview

A full-stack Brand Visibility Intelligence Dashboard that extracts real-time product data from Google Shopping via SerpAPI, merges it with a pre-provided dirty dataset, runs a complete ETL pipeline, stores cleaned data in PostgreSQL, and visualizes insights through an interactive Streamlit web application with SQL-powered live filters.


Domain: E-Commerce Analytics / Digital Marketing Intelligence / Business Intelligence




🎯 Business Use Cases


Competitive analysis for e-commerce brands
Pricing strategy optimization across platforms
Market positioning insights for new product launches
Platform performance comparison (Amazon, Flipkart, Croma, etc.)
Identifying high-visibility brands and products
Monitoring discount strategies across competitors



🗂️ Project Structure

brand_visibility_project/
│
├── 📄 data_cleaning.py           # Step 1 — Clean & preprocess dirty CSV
├── 📄 api_extraction.py          # Step 2 — Fetch live data via SerpAPI
├── 📄 merge_and_load_sql.py      # Step 3 — Merge datasets + load to PostgreSQL
├── 📄 dashboard.py               # Step 4 — 6-tab Streamlit dashboard
│
├── 📊 brand_dirty_dataset.csv    # Raw dataset (Dataset 1)
├── 📊 brand_clean_dataset.csv    # Auto-generated after cleaning
├── 📊 brand_final_dataset.csv    # Auto-generated after merging
│
├── 📁 .streamlit/
│   └── secrets.toml              # PostgreSQL credentials (gitignored)
│
├── 📄 requirements.txt
└── 📄 README.md


🔧 Tech Stack

LayerTechnologyLanguagePython 3.11Data ExtractionSerpAPI (Google Shopping API)Data ProcessingPandas, NumPyDatabasePostgreSQL + SQLAlchemyDashboardStreamlitVisualizationPlotly ExpressVersion ControlGit & GitHub


⚙️ Setup & Installation

Prerequisites


Python 3.11 (recommended)
PostgreSQL installed and running
SerpAPI account (free tier at serpapi.com)


1. Clone the Repository

bashgit clone https://github.com/YOUR_USERNAME/brand-visibility-dashboard.git
cd brand-visibility-dashboard

2. Install Dependencies

bashpip install -r requirements.txt

3. Configure API Key

Open api_extraction.py and replace line 16:

pythonSERPAPI_KEY = "YOUR_SERPAPI_KEY_HERE"   # ← paste your SerpAPI key here

4. Configure PostgreSQL

.streamlit/secrets.toml (for dashboard):

toml[postgres]
host     = "localhost"
port     = 5432
database = "brand_visibility"
user     = "postgres"
password = "YOUR_PASSWORD"

merge_and_load_sql.py (for data loading):

pythonDB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "database": "brand_visibility",
    "user":     "postgres",
    "password": "YOUR_PASSWORD",
}


💡 Create the database in pgAdmin first: CREATE DATABASE brand_visibility;




🚀 How to Run

bash# Step 1 — Clean the dirty CSV dataset
python data_cleaning.py

# Step 2 — Fetch live data from SerpAPI (needs API key)
python api_extraction.py

# Step 3 — Merge both datasets and load into PostgreSQL
python merge_and_load_sql.py

# Step 4 — Launch the dashboard
streamlit run dashboard.py


Note: The dashboard works without PostgreSQL too — it auto-falls back to CSV mode.




📊 Dashboard Tabs

TabKPIsCharts📋 OverviewTotal Products, Avg Price, Avg Rating, Total Reviews, PlatformsPrice Distribution, Products per Keyword, Platform Share, Price Range🏷️ Brand InsightsTop Brand, Best Visibility, Highest RatedBrand Count, Avg Rating, Top-10 Positions, Visibility Score, Avg Position💰 Pricing AnalysisAvg/Max/Min Price, % DiscountedPrice vs Ranking, Price vs Rating, Discount by Brand/Platform, Avg Price per Platform🏪 Platform AnalysisTotal Platforms, Best/Cheapest PlatformProduct Count, Avg Rating, Avg Price, Avg Position, Brand Distribution👁️ Visibility & RankingAvg Position, Avg Visibility, Top-10%Ranking Distribution, Rating vs Ranking, Reviews Bubble Chart, Visibility by Brand🔍 Product ExplorerFiltered Count, Avg Price, Avg RatingSearchable table, Rating vs Price, Reviews vs Ranking


🔍 Sidebar Filters (SQL-Powered Live Filters)

All filters dynamically modify the SQL query sent to PostgreSQL:


🔑 Keyword — multi-select
🏷️ Brand — multi-select
🏪 Platform — multi-select
💰 Price Range — slider
⭐ Rating Range — slider
📍 Max Position / Ranking — slider



🛠️ Data Pipeline

SerpAPI (Google Shopping)       brand_dirty_dataset.csv
         ↓                               ↓
   api_extraction.py          data_cleaning.py
         ↓                               ↓
  api_clean_data.csv      brand_clean_dataset.csv
            ↘                 ↙
         merge_and_load_sql.py
                  ↓
          PostgreSQL (products table)
                  ↓
           dashboard.py → Streamlit App


🧹 Data Cleaning Steps


Removed noise from product titles (special characters)
Converted price and reviews to numeric (handled "Not Available", "many", etc.)
Standardized platform names (Amazon, Flipkart, Croma...)
Filled missing ratings/prices with keyword-level median
Removed duplicates based on title + price
Capped price outliers at 99th percentile
Standardized delivery and categorical values



⚙️ Feature Engineering

FeatureDescriptionbrandExtracted from product title using known brand listvisibility_score(40 - position) / 40 — higher rank = higher scoreprice_rangeCategorized: Budget / Economy / Mid-Range / Premium / High-End / Luxurydiscount_pct((raw_price - price) / raw_price) × 100


📁 Dataset Details

ColumnTypeDescriptionkeywordStringSearch term usedtitleStringProduct namepriceFloatFinal selling price (₹)raw_priceFloatOriginal price before discountratingFloatAvg user rating (0–5)reviewsIntegerTotal customer reviewsplatformStringE-commerce platformpositionIntegerSearch result rankdeliveryStringDelivery typebrandStringExtracted brand namevisibility_scoreFloatDerived ranking metricprice_rangeStringPrice categorydiscount_pctFloatDiscount percentage


📸 Screenshots
<img width="1905" height="930" alt="image" src="https://github.com/user-attachments/assets/2d11a86b-189b-4e49-8d18-1f44c5d86519" />

👩‍💻 Author

Abhijeet Gupta

AIML Student

HCL-GUVI Learning Module


📄 License

This project is licensed under the MIT License.
