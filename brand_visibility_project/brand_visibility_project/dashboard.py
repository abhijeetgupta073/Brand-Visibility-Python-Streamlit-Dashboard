"""
Brand Visibility Intelligence Dashboard
Streamlit App with SQL-powered live filters
HCL GUVI Project - Author: Shivani
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from sqlalchemy import create_engine, text

# ══════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════
st.set_page_config(
    page_title="Brand Visibility Intelligence",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════
# CUSTOM CSS
# ══════════════════════════════════════════════════
st.markdown("""
<style>
    /* Header banner */
    .main-header {
        background: linear-gradient(135deg, #1a2a6c, #b21f1f, #1a2a6c);
        padding: 20px 30px;
        border-radius: 12px;
        margin-bottom: 20px;
        color: white;
    }
    .main-header h1 { font-size: 2rem; margin: 0; font-weight: 700; }
    .main-header p  { margin: 5px 0 0; opacity: 0.85; font-size: 0.9rem; }

    /* KPI cards */
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-top: 4px solid #1a2a6c;
        text-align: center;
    }
    .kpi-value { font-size: 1.8rem; font-weight: 700; color: #1a2a6c; }
    .kpi-label { font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 1px; }

    /* Tab styling */
    .stTabs [data-baseweb="tab"] { font-size: 0.85rem; font-weight: 600; }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 12px; }

    /* Sidebar */
    section[data-testid="stSidebar"] { background: #0f2044; }
    section[data-testid="stSidebar"] * { color: white !important; }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stMultiSelect label { color: #ffd700 !important; font-weight: 600; }

    /* Charts */
    .chart-title { font-size: 1rem; font-weight: 600; color: #333; margin-bottom: 8px; }

    /* Scrollable table */
    .dataframe { font-size: 0.82rem !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# DATA LOADING  (PostgreSQL first, CSV fallback)
# ══════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def get_engine():
    """Create SQLAlchemy engine from Streamlit secrets."""
    try:
        cfg = st.secrets["postgres"]
        url = (
            f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}"
            f"@{cfg['host']}:{cfg['port']}/{cfg['database']}"
        )
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception:
        return None


@st.cache_data(show_spinner=False, ttl=300)
def load_data(filters: dict) -> pd.DataFrame:
    """
    Load data from PostgreSQL with filters pushed down as SQL WHERE clauses.
    Falls back to CSV if DB unavailable.
    """
    engine = get_engine()

    if engine:
        where_clauses = []
        params = {}

        if filters.get("keywords"):
            kw_list = ", ".join([f":kw{i}" for i in range(len(filters["keywords"]))])
            where_clauses.append(f"keyword IN ({kw_list})")
            for i, k in enumerate(filters["keywords"]):
                params[f"kw{i}"] = k

        if filters.get("brands"):
            b_list = ", ".join([f":br{i}" for i in range(len(filters["brands"]))])
            where_clauses.append(f"brand IN ({b_list})")
            for i, b in enumerate(filters["brands"]):
                params[f"br{i}"] = b

        if filters.get("platforms"):
            p_list = ", ".join([f":pl{i}" for i in range(len(filters["platforms"]))])
            where_clauses.append(f"platform IN ({p_list})")
            for i, p in enumerate(filters["platforms"]):
                params[f"pl{i}"] = p

        if filters.get("price_min") is not None:
            where_clauses.append("price >= :price_min")
            params["price_min"] = filters["price_min"]

        if filters.get("price_max") is not None:
            where_clauses.append("price <= :price_max")
            params["price_max"] = filters["price_max"]

        if filters.get("rating_min") is not None:
            where_clauses.append("rating >= :rating_min")
            params["rating_min"] = filters["rating_min"]

        if filters.get("rating_max") is not None:
            where_clauses.append("rating <= :rating_max")
            params["rating_max"] = filters["rating_max"]

        if filters.get("max_position") is not None:
            where_clauses.append("position <= :max_position")
            params["max_position"] = filters["max_position"]

        where_str = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        query = text(f'SELECT * FROM products {where_str} ORDER BY position LIMIT 5000')

        try:
            with engine.connect() as conn:
                df = pd.read_sql(query, conn, params=params)
            return df
        except Exception as e:
            st.warning(f"DB query failed: {e}. Using CSV fallback.")

    # ── CSV Fallback ──
    csv_path = "brand_final_dataset.csv"
    if not os.path.exists(csv_path):
        csv_path = "brand_dirty_dataset.csv"
        from data_cleaning import load_csv, clean_dataset
        df = clean_dataset(load_csv(csv_path), "csv")
    else:
        df = pd.read_csv(csv_path)

    # Apply filters in-memory
    if filters.get("keywords"):
        df = df[df["keyword"].isin(filters["keywords"])]
    if filters.get("brands"):
        df = df[df["brand"].isin(filters["brands"])]
    if filters.get("platforms"):
        df = df[df["platform"].isin(filters["platforms"])]
    if filters.get("price_min") is not None:
        df = df[df["price"] >= filters["price_min"]]
    if filters.get("price_max") is not None:
        df = df[df["price"] <= filters["price_max"]]
    if filters.get("rating_min") is not None:
        df = df[df["rating"] >= filters["rating_min"]]
    if filters.get("rating_max") is not None:
        df = df[df["rating"] <= filters["rating_max"]]
    if filters.get("max_position") is not None:
        df = df[df["position"] <= filters["max_position"]]

    return df


@st.cache_data(show_spinner=False)
def load_all_options() -> dict:
    """Load dropdown options (no filters applied)."""
    engine = get_engine()
    if engine:
        try:
            with engine.connect() as conn:
                keywords  = pd.read_sql("SELECT DISTINCT keyword  FROM products ORDER BY keyword",  conn)["keyword"].tolist()
                brands    = pd.read_sql("SELECT DISTINCT brand    FROM products ORDER BY brand",    conn)["brand"].tolist()
                platforms = pd.read_sql("SELECT DISTINCT platform FROM products ORDER BY platform", conn)["platform"].tolist()
                prices    = pd.read_sql("SELECT MIN(price) AS mn, MAX(price) AS mx FROM products",  conn).iloc[0]
                return {
                    "keywords": keywords, "brands": brands, "platforms": platforms,
                    "price_min": float(prices["mn"]), "price_max": float(prices["mx"])
                }
        except Exception:
            pass

    csv_path = "brand_final_dataset.csv"
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        from data_cleaning import load_csv, clean_dataset
        df = clean_dataset(load_csv("brand_dirty_dataset.csv"), "csv")

    return {
        "keywords":  sorted(df["keyword"].dropna().unique().tolist()),
        "brands":    sorted(df["brand"].dropna().unique().tolist()),
        "platforms": sorted(df["platform"].dropna().unique().tolist()),
        "price_min": float(df["price"].min()),
        "price_max": float(df["price"].max()),
    }


# ══════════════════════════════════════════════════
# COLOUR PALETTE
# ══════════════════════════════════════════════════
COLORS = px.colors.qualitative.Bold
TEMPLATE = "plotly_white"


# ══════════════════════════════════════════════════
# SIDEBAR FILTERS
# ══════════════════════════════════════════════════
def render_sidebar(opts: dict) -> dict:
    with st.sidebar:
        st.markdown("## 🔧 Filters")
        st.markdown("---")

        keywords = st.multiselect(
            "🔑 KEYWORD",
            options=opts["keywords"],
            default=[],
            placeholder="All keywords",
        )
        brands = st.multiselect(
            "🏷️ BRAND",
            options=opts["brands"],
            default=[],
            placeholder="All brands",
        )
        platforms = st.multiselect(
            "🛒 PLATFORM",
            options=opts["platforms"],
            default=[],
            placeholder="All platforms",
        )

        st.markdown("💰 PRICE RANGE (₹)")
        price_range = st.slider(
            "",
            min_value=int(opts["price_min"]),
            max_value=int(opts["price_max"]),
            value=(int(opts["price_min"]), int(opts["price_max"])),
            step=500,
        )

        st.markdown("⭐ RATING RANGE")
        rating_range = st.slider("", min_value=0.0, max_value=5.0,
                                  value=(0.0, 5.0), step=0.1)

        st.markdown("📍 MAX POSITION (RANKING)")
        max_pos = st.slider("", min_value=1, max_value=40, value=40, step=1)

        st.markdown("---")
        st.markdown("**Data source:** SQL-Powered · Live Filters")

    return {
        "keywords":    keywords  or None,
        "brands":      brands    or None,
        "platforms":   platforms or None,
        "price_min":   price_range[0],
        "price_max":   price_range[1],
        "rating_min":  rating_range[0],
        "rating_max":  rating_range[1],
        "max_position": max_pos,
    }


# ══════════════════════════════════════════════════
# KPI HELPER
# ══════════════════════════════════════════════════
def kpi(label: str, value, icon: str = ""):
    st.markdown(f"""
    <div class="kpi-card">
        <div style="font-size:1.6rem">{icon}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# TAB 1 – OVERVIEW
# ══════════════════════════════════════════════════
def tab_overview(df: pd.DataFrame):
    # KPIs
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: kpi("Total Products", f"{len(df):,}", "📦")
    with c2: kpi("Avg Price",      f"₹{df['price'].mean():,.0f}", "💰")
    with c3: kpi("Avg Rating",     f"{df['rating'].mean():.2f}", "⭐")
    with c4: kpi("Total Reviews",  f"{df['reviews'].sum():,}", "💬")
    with c5: kpi("Platforms",      df["platform"].nunique(), "🏪")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 Price Distribution")
        fig = px.histogram(
            df, x="price", nbins=40,
            color_discrete_sequence=["#1a2a6c"],
            template=TEMPLATE,
            labels={"price": "Price (₹)", "count": "# Products"},
        )
        fig.update_layout(bargap=0.05, margin=dict(t=10, b=40, l=40, r=10))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 🔑 Products per Keyword")
        kw_cnt = df["keyword"].value_counts().reset_index()
        kw_cnt.columns = ["keyword", "count"]
        fig = px.bar(
            kw_cnt, x="count", y="keyword", orientation="h",
            color="count", color_continuous_scale="Blues",
            template=TEMPLATE,
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"},
                          margin=dict(t=10, b=40, l=150, r=10),
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("#### 🍕 Platform Share")
        plat_cnt = df["platform"].value_counts().reset_index()
        plat_cnt.columns = ["platform", "count"]
        fig = px.pie(
            plat_cnt, names="platform", values="count",
            color_discrete_sequence=COLORS, template=TEMPLATE,
            hole=0.45,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.markdown("#### 📦 Price Range Distribution")
        pr_cnt = df["price_range"].value_counts().reset_index()
        pr_cnt.columns = ["price_range", "count"]
        order = ["Budget (<500)", "Economy (500-2K)", "Mid-Range (2K-5K)",
                 "Premium (5K-15K)", "High-End (15K-50K)", "Luxury (50K+)", "Unknown"]
        pr_cnt["price_range"] = pd.Categorical(pr_cnt["price_range"], categories=order, ordered=True)
        pr_cnt.sort_values("price_range", inplace=True)
        fig = px.bar(
            pr_cnt, x="price_range", y="count",
            color="price_range",
            color_discrete_sequence=COLORS,
            template=TEMPLATE,
        )
        fig.update_layout(showlegend=False, margin=dict(t=10, b=80, l=40, r=10),
                          xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════
# TAB 2 – BRAND INSIGHTS
# ══════════════════════════════════════════════════
def tab_brand_insights(df: pd.DataFrame):
    top_brand     = df["brand"].value_counts().idxmax()
    avg_vis        = df["visibility_score"].mean()
    top_vis_brand  = df.groupby("brand")["visibility_score"].mean().idxmax()
    top_rated_brand = df.groupby("brand")["rating"].mean().idxmax()

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Total Brands",      df["brand"].nunique(), "🏷️")
    with c2: kpi("Top Brand",          top_brand, "🥇")
    with c3: kpi("Best Visibility",    top_vis_brand, "👁️")
    with c4: kpi("Highest Rated Brand", top_rated_brand, "⭐")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📦 Brand vs Product Count")
        bc = df["brand"].value_counts().head(15).reset_index()
        bc.columns = ["brand", "count"]
        fig = px.bar(bc, x="count", y="brand", orientation="h",
                     color="count", color_continuous_scale="Blues",
                     template=TEMPLATE)
        fig.update_layout(yaxis={"categoryorder": "total ascending"},
                          coloraxis_showscale=False,
                          margin=dict(t=10, b=40, l=120, r=10))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### ⭐ Brand vs Avg Rating")
        br = df.groupby("brand")["rating"].mean().sort_values(ascending=False).head(15).reset_index()
        br.columns = ["brand", "avg_rating"]
        fig = px.bar(br, x="avg_rating", y="brand", orientation="h",
                     color="avg_rating", color_continuous_scale="Oranges",
                     template=TEMPLATE)
        fig.update_layout(yaxis={"categoryorder": "total ascending"},
                          coloraxis_showscale=False,
                          margin=dict(t=10, b=40, l=120, r=10))
        fig.update_xaxes(range=[0, 5])
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("#### 👁️ Visibility Score by Brand")
        bv = df.groupby("brand")["visibility_score"].mean().sort_values(ascending=False).head(15).reset_index()
        bv.columns = ["brand", "vis_score"]
        fig = px.bar(bv, x="vis_score", y="brand", orientation="h",
                     color="vis_score", color_continuous_scale="Greens",
                     template=TEMPLATE)
        fig.update_layout(yaxis={"categoryorder": "total ascending"},
                          coloraxis_showscale=False,
                          margin=dict(t=10, b=40, l=120, r=10))
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.markdown("#### 🏆 Top Brands in Top-10 Positions")
        top10 = df[df["position"] <= 10]
        if not top10.empty:
            t10c = top10["brand"].value_counts().head(12).reset_index()
            t10c.columns = ["brand", "top10_count"]
            fig = px.bar(t10c, x="brand", y="top10_count",
                         color="top10_count", color_continuous_scale="Purples",
                         template=TEMPLATE)
            fig.update_layout(xaxis_tickangle=-30, coloraxis_showscale=False,
                              margin=dict(t=10, b=80, l=40, r=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No products in top-10 positions with current filters.")

    st.markdown("#### 📍 Avg Position (Ranking) per Brand")
    bp = df.groupby("brand")["position"].mean().sort_values().head(15).reset_index()
    bp.columns = ["brand", "avg_position"]
    fig = px.bar(bp, x="brand", y="avg_position",
                 color="avg_position", color_continuous_scale="RdYlGn_r",
                 template=TEMPLATE)
    fig.update_layout(xaxis_tickangle=-30, coloraxis_showscale=False,
                      margin=dict(t=10, b=80, l=40, r=10))
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════
# TAB 3 – PRICING ANALYSIS
# ══════════════════════════════════════════════════
def tab_pricing(df: pd.DataFrame):
    avg_price  = df["price"].mean()
    max_price  = df["price"].max()
    min_price  = df["price"].min()
    disc_pct   = (df["discount_pct"] > 0).mean() * 100

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Avg Price",           f"₹{avg_price:,.0f}", "💰")
    with c2: kpi("Max Price",           f"₹{max_price:,.0f}", "📈")
    with c3: kpi("Min Price",           f"₹{min_price:,.0f}", "📉")
    with c4: kpi("Below-Median Products", f"{disc_pct:.1f}%", "🏷️")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 💹 Price vs Ranking (Scatter)")
        fig = px.scatter(
            df, x="position", y="price", color="brand",
            size="reviews", hover_data=["title", "platform"],
            template=TEMPLATE, opacity=0.7,
            labels={"position": "Position (Rank)", "price": "Price (₹)"},
        )
        fig.update_layout(margin=dict(t=10, b=40, l=40, r=10), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### ⭐ Price vs Rating (Scatter)")
        fig = px.scatter(
            df, x="rating", y="price", color="platform",
            size="reviews", hover_data=["title", "brand"],
            template=TEMPLATE, opacity=0.7,
            labels={"rating": "Rating", "price": "Price (₹)"},
        )
        fig.update_layout(margin=dict(t=10, b=40, l=40, r=10), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("#### 🏷️ Discount % by Brand")
        db = df[df["discount_pct"] > 0].groupby("brand")["discount_pct"].mean().sort_values(ascending=False).head(15).reset_index()
        db.columns = ["brand", "avg_discount"]
        if not db.empty:
            fig = px.bar(db, x="brand", y="avg_discount",
                         color="avg_discount", color_continuous_scale="Reds",
                         template=TEMPLATE)
            fig.update_layout(xaxis_tickangle=-30, coloraxis_showscale=False,
                              margin=dict(t=10, b=80, l=40, r=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No discounted products with current filters.")

    with col4:
        st.markdown("#### 🏪 Discount % by Platform")
        dp = df[df["discount_pct"] > 0].groupby("platform")["discount_pct"].mean().sort_values(ascending=False).reset_index()
        dp.columns = ["platform", "avg_discount"]
        if not dp.empty:
            fig = px.bar(dp, x="platform", y="avg_discount",
                         color="avg_discount", color_continuous_scale="Oranges",
                         template=TEMPLATE)
            fig.update_layout(xaxis_tickangle=-30, coloraxis_showscale=False,
                              margin=dict(t=10, b=80, l=40, r=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No discounted products with current filters.")

    st.markdown("#### 💰 Avg Price per Platform")
    pp = df.groupby("platform")["price"].mean().sort_values(ascending=False).reset_index()
    pp.columns = ["platform", "avg_price"]
    fig = px.bar(pp, x="platform", y="avg_price",
                 color="avg_price", color_continuous_scale="Blues",
                 template=TEMPLATE,
                 text=pp["avg_price"].apply(lambda x: f"₹{x:,.0f}"))
    fig.update_traces(textposition="outside")
    fig.update_layout(xaxis_tickangle=-20, coloraxis_showscale=False,
                      margin=dict(t=10, b=80, l=40, r=10))
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════
# TAB 4 – PLATFORM ANALYSIS
# ══════════════════════════════════════════════════
def tab_platform(df: pd.DataFrame):
    best_plat   = df.groupby("platform")["rating"].mean().idxmax()
    cheap_plat  = df.groupby("platform")["price"].mean().idxmin()
    most_prods  = df["platform"].value_counts().idxmax()

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Total Platforms",         df["platform"].nunique(), "🏪")
    with c2: kpi("Best Platform (Rating)",  best_plat,  "🌟")
    with c3: kpi("Cheapest Platform",        cheap_plat, "💸")
    with c4: kpi("Most Products",            most_prods, "📦")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 Platform vs Product Count")
        pc = df["platform"].value_counts().reset_index()
        pc.columns = ["platform", "count"]
        fig = px.bar(pc, x="platform", y="count",
                     color="count", color_continuous_scale="Blues",
                     template=TEMPLATE,
                     text="count")
        fig.update_traces(textposition="outside")
        fig.update_layout(xaxis_tickangle=-20, coloraxis_showscale=False,
                          margin=dict(t=10, b=80, l=40, r=10))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### ⭐ Platform vs Avg Rating")
        pr = df.groupby("platform")["rating"].mean().reset_index()
        pr.columns = ["platform", "avg_rating"]
        fig = px.bar(pr, x="platform", y="avg_rating",
                     color="avg_rating", color_continuous_scale="Oranges",
                     template=TEMPLATE,
                     text=pr["avg_rating"].apply(lambda x: f"{x:.2f}"))
        fig.update_traces(textposition="outside")
        fig.update_xaxes(range=[0, 5.5])
        fig.update_layout(xaxis_tickangle=-20, coloraxis_showscale=False,
                          margin=dict(t=10, b=80, l=40, r=10))
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("#### 💰 Platform vs Avg Price")
        pp = df.groupby("platform")["price"].mean().reset_index()
        pp.columns = ["platform", "avg_price"]
        fig = px.bar(pp, x="platform", y="avg_price",
                     color="avg_price", color_continuous_scale="Greens",
                     template=TEMPLATE,
                     text=pp["avg_price"].apply(lambda x: f"₹{x:,.0f}"))
        fig.update_traces(textposition="outside")
        fig.update_layout(xaxis_tickangle=-20, coloraxis_showscale=False,
                          margin=dict(t=10, b=80, l=40, r=10))
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.markdown("#### 📍 Platform vs Avg Position (Ranking)")
        pos_p = df.groupby("platform")["position"].mean().reset_index()
        pos_p.columns = ["platform", "avg_position"]
        fig = px.bar(pos_p, x="platform", y="avg_position",
                     color="avg_position", color_continuous_scale="Reds",
                     template=TEMPLATE,
                     text=pos_p["avg_position"].apply(lambda x: f"{x:.1f}"))
        fig.update_traces(textposition="outside")
        fig.update_layout(xaxis_tickangle=-20, coloraxis_showscale=False,
                          margin=dict(t=10, b=80, l=40, r=10))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 🏷️ Brand Distribution per Platform (Stacked Bar)")
    bpp = df.groupby(["platform", "brand"]).size().reset_index(name="count")
    top_brands_list = df["brand"].value_counts().head(8).index.tolist()
    bpp = bpp[bpp["brand"].isin(top_brands_list)]
    fig = px.bar(bpp, x="platform", y="count", color="brand",
                 template=TEMPLATE, barmode="stack",
                 color_discrete_sequence=COLORS)
    fig.update_layout(xaxis_tickangle=-20, margin=dict(t=10, b=80, l=40, r=10))
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════
# TAB 5 – VISIBILITY & RANKING
# ══════════════════════════════════════════════════
def tab_visibility(df: pd.DataFrame):
    avg_pos       = df["position"].mean()
    avg_vis       = df["visibility_score"].mean()
    best_ranked   = df.loc[df["position"].idxmin(), "title"] if not df.empty else "N/A"
    top10_pct     = (df["position"] <= 10).mean() * 100

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Avg Position",        f"{avg_pos:.1f}", "📍")
    with c2: kpi("Avg Visibility Score", f"{avg_vis:.3f}", "👁️")
    with c3: kpi("Products in Top-10",  f"{top10_pct:.1f}%", "🏆")
    with c4: kpi("Best Ranked Product",  best_ranked[:25] + "…" if len(str(best_ranked)) > 25 else best_ranked, "🥇")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 Ranking Distribution (Histogram)")
        fig = px.histogram(df, x="position", nbins=40,
                           color_discrete_sequence=["#b21f1f"],
                           template=TEMPLATE,
                           labels={"position": "Position (Rank)"})
        fig.update_layout(bargap=0.05, margin=dict(t=10, b=40, l=40, r=10))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### ⭐ Rating vs Ranking")
        fig = px.scatter(df, x="position", y="rating", color="brand",
                         hover_data=["title", "platform", "price"],
                         template=TEMPLATE, opacity=0.7,
                         labels={"position": "Position (Rank)", "rating": "Rating"})
        fig.update_layout(margin=dict(t=10, b=40, l=40, r=10), showlegend=False)
        fig.add_hline(y=df["rating"].mean(), line_dash="dash",
                      line_color="gray", annotation_text="Avg Rating")
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("#### 💬 Reviews vs Ranking (Bubble)")
        sample = df.sample(min(300, len(df)), random_state=42)
        fig = px.scatter(sample, x="position", y="reviews",
                         size="visibility_score", color="platform",
                         hover_data=["title", "brand"],
                         template=TEMPLATE, opacity=0.75,
                         labels={"position": "Position", "reviews": "Reviews"})
        fig.update_layout(margin=dict(t=10, b=40, l=40, r=10))
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.markdown("#### 👁️ Visibility Score by Brand (Top 15)")
        bv = df.groupby("brand")["visibility_score"].mean().sort_values(ascending=False).head(15).reset_index()
        bv.columns = ["brand", "vis_score"]
        fig = px.bar(bv, x="vis_score", y="brand", orientation="h",
                     color="vis_score", color_continuous_scale="Purples",
                     template=TEMPLATE)
        fig.update_layout(yaxis={"categoryorder": "total ascending"},
                          coloraxis_showscale=False,
                          margin=dict(t=10, b=40, l=120, r=10))
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════
# TAB 6 – PRODUCT EXPLORER
# ══════════════════════════════════════════════════
def tab_product_explorer(df: pd.DataFrame):
    st.markdown("### 🔍 Product Explorer")

    search_query = st.text_input("🔎 Search by product title:", "")
    show_cols = ["title", "brand", "price", "rating", "reviews",
                 "platform", "position", "discount_pct", "price_range", "keyword"]

    display = df[[c for c in show_cols if c in df.columns]].copy()
    if search_query:
        display = display[
            display["title"].str.lower().str.contains(search_query.lower(), na=False)
        ]

    st.markdown(f"**{len(display):,} products shown**")

    sort_col = st.selectbox("Sort by:", options=show_cols, index=show_cols.index("position"))
    sort_asc  = st.radio("Order:", ["Ascending", "Descending"], horizontal=True) == "Ascending"
    display   = display.sort_values(sort_col, ascending=sort_asc)

    # Format money columns
    display["price"] = display["price"].apply(lambda x: f"₹{x:,.0f}" if pd.notna(x) else "N/A")
    display["discount_pct"] = display["discount_pct"].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%")

    st.dataframe(display.reset_index(drop=True), use_container_width=True, height=500)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 💰 Rating vs Price")
        fig = px.scatter(df, x="rating", y="price", color="brand",
                         hover_data=["title"], template=TEMPLATE, opacity=0.7)
        fig.update_layout(margin=dict(t=10, b=40, l=40, r=10), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("#### 💬 Reviews vs Ranking")
        fig = px.scatter(df, x="position", y="reviews", color="platform",
                         size="price", hover_data=["title", "brand"],
                         template=TEMPLATE, opacity=0.7)
        fig.update_layout(margin=dict(t=10, b=40, l=40, r=10))
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════
def main():
    opts    = load_all_options()
    filters = render_sidebar(opts)
    df      = load_data(filters)

    # ── Header ──
    record_count = len(df)
    st.markdown(f"""
    <div class="main-header">
        <h1>🛒 E-Commerce Analytics Dashboard</h1>
        <p>HCL-GUVI Learning Module · Brand Visibility Intelligence ·
           <b>{record_count:,} records shown</b>
           &nbsp;&nbsp;<span style="background:rgba(255,255,255,0.2);padding:4px 10px;border-radius:20px;font-size:0.8rem;">SQL-Powered · Live Filters</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    if df.empty:
        st.warning("No data matches the current filters. Try broadening your selection.")
        return

    # ── Tabs ──
    tabs = st.tabs([
        "📋 Overview",
        "🏷️ Brand Insights",
        "💰 Pricing Analysis",
        "🏪 Platform Analysis",
        "👁️ Visibility & Ranking",
        "🔍 Product Explorer",
    ])

    with tabs[0]: tab_overview(df)
    with tabs[1]: tab_brand_insights(df)
    with tabs[2]: tab_pricing(df)
    with tabs[3]: tab_platform(df)
    with tabs[4]: tab_visibility(df)
    with tabs[5]: tab_product_explorer(df)


if __name__ == "__main__":
    main()
