import streamlit as st
import requests
import plotly.express as px
import pandas as pd
import os
from datetime import datetime, timedelta

# Title
st.title("📈 Senticker – Curated Stock News with Sentiment")

# Sidebar inputs
st.sidebar.header("🔎 Search")
ticker = st.sidebar.text_input("Enter a stock ticker (e.g. TSLA, AAPL):", "TSLA").upper()
sentiment_filter = st.sidebar.selectbox("🧠 Filter by Sentiment", ["All", "Positive", "Neutral", "Negative"])

# API token from secrets
API_TOKEN = st.secrets["API_TOKEN"]
BASE_URL = st.secrets["BASE_URL"]

# Constants
CACHE_FILE = "sentiment_data.csv"
PRELOAD_TICKERS = ["NVDA", "AAPL"]

# Function to fetch paginated news (for preload)
def fetch_paginated_news(ticker, max_articles=100):
    articles = []
    page = 1
    while len(articles) < max_articles:
        params = {
            "api_token": API_TOKEN,
            "symbols": ticker,
            "language": "en",
            "published_after": (datetime.utcnow() - timedelta(hours=12)).isoformat(),
            "page": page,
            "limit": 10
        }
        response = requests.get(BASE_URL, params=params)
        data = response.json().get("data", [])
        if not data:
            break
        articles.extend(data)
        page += 1
    return articles[:max_articles]

# Cache data on app load
@st.cache_data(show_spinner="Preloading news cache...")
def preload_cache():
    all_data = []
    for t in PRELOAD_TICKERS:
        news = fetch_paginated_news(t)
        for article in news:
            matched_entity = next((e for e in article.get("entities", []) if e["symbol"].upper() == t), None)
            if matched_entity:
                all_data.append({
                    "symbol": t,
                    "title": article["title"],
                    "url": article["url"],
                    "source": article["source"],
                    "published_at": article["published_at"],
                    "sentiment_score": matched_entity.get("sentiment_score", 0)
                })
    df = pd.DataFrame(all_data)
    df.to_csv(CACHE_FILE, index=False)
    return df

# Load or create cache safely
if os.path.exists(CACHE_FILE) and os.path.getsize(CACHE_FILE) > 0:
    cached_df = pd.read_csv(CACHE_FILE)
else:
    cached_df = preload_cache()

# Function to interpret sentiment
def interpret_sentiment(score):
    if score > 0.15:
        return "😊 Positive", "🟢"
    elif score < -0.15:
        return "😟 Negative", "🔴"
    else:
        return "😐 Neutral", "🟡"

# Display News
if ticker:
    st.markdown(f"### 📡 News for **{ticker}**")

    if ticker in PRELOAD_TICKERS:
        articles_df = cached_df[cached_df["symbol"] == ticker]
    else:
        # Real-time fallback
        with st.spinner("Fetching real-time news..."):
            params = {
                "api_token": API_TOKEN,
                "symbols": ticker,
                "language": "en",
                "limit": 3
            }
            response = requests.get(BASE_URL, params=params)
            articles = response.json().get("data", [])
            articles_df = []
            for article in articles:
                matched_entity = next((e for e in article.get("entities", []) if e["symbol"].upper() == ticker), None)
                if matched_entity:
                    articles_df.append({
                        "symbol": ticker,
                        "title": article["title"],
                        "url": article["url"],
                        "source": article["source"],
                        "published_at": article["published_at"],
                        "sentiment_score": matched_entity.get("sentiment_score", 0)
                    })
            articles_df = pd.DataFrame(articles_df)

    if articles_df.empty:
        st.warning("No news articles found.")
    else:
        sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
        for _, row in articles_df.iterrows():
            score = row["sentiment_score"]
            if score > 0.15:
                sentiment_counts["Positive"] += 1
            elif score < -0.15:
                sentiment_counts["Negative"] += 1
            else:
                sentiment_counts["Neutral"] += 1

        # Pie chart
        if sum(sentiment_counts.values()) > 0:
            fig = px.pie(
                names=list(sentiment_counts.keys()),
                values=list(sentiment_counts.values()),
                color=list(sentiment_counts.keys()),
                color_discrete_map={
                    "Positive": "green",
                    "Neutral": "gold",
                    "Negative": "red"
                },
                title="📊 Sentiment Distribution"
            )
            st.plotly_chart(fig)

        # Show articles
        for _, row in articles_df.iterrows():
            sentiment_label, emoji = interpret_sentiment(row["sentiment_score"])
            if sentiment_filter != "All" and sentiment_label.split()[1] != sentiment_filter:
                continue
            st.markdown(f"#### [{row['title']}]({row['url']})")
            st.markdown(f"📰 *{row['source']}*  |  🕒 *{row['published_at'][:10]}*")
            st.markdown(f"**Sentiment:** {emoji} {sentiment_label} ({row['sentiment_score']:.2f})")
            st.markdown("---")