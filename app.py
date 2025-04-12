import streamlit as st
import requests
import plotly.express as px
import pandas as pd
import os
from datetime import datetime, timedelta
import time

# Constants
STOCKS = ["TSLA", "NVDA", "AAPL"]
ARTICLES_PER_STOCK = 100
ARTICLES_PER_REQUEST = 3
HOURS_LOOKBACK = 12
FILE_PATH = "sentiment_data.csv"

# API token from secrets
API_TOKEN = st.secrets["API_TOKEN"]
BASE_URL = st.secrets["BASE_URL"]

# Title
st.title("\ud83d\udcc8 Senticker – Curated Stock News with Sentiment")

# Sidebar inputs
st.sidebar.header("\ud83d\udd0e Search")
ticker = st.sidebar.text_input("Enter a stock ticker (e.g. TSLA, AAPL):", "TSLA")
sentiment_filter = st.sidebar.selectbox("\ud83e\udde0 Filter by Sentiment", ["All", "Positive", "Neutral", "Negative"])

# Function to fetch news from API
def get_news(ticker, page=1, limit=10, hours=12):
    url = BASE_URL
    params = {
        "api_token": API_TOKEN,
        "symbols": ticker,
        "language": "en",
        "limit": limit,
        "page": page,
        "published_after": (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    }
    response = requests.get(url, params=params)
    return response.json().get("data", [])

# Function to interpret sentiment
def interpret_sentiment(score):
    if score > 0.15:
        return "\ud83d\ude0a Positive", "\ud83d\udfe2"
    elif score < -0.15:
        return "\ud83d\ude1f Negative", "\ud83d\udd34"
    else:
        return "\ud83d\ude10 Neutral", "\ud83d\udfe1"

# Cache the default news on app load
@st.cache_data
def load_sentiment_data():
    return pd.read_csv(FILE_PATH) if os.path.exists(FILE_PATH) else pd.DataFrame()

def store_articles(articles, symbol):
    records = []
    for article in articles:
        sentiment = None
        if article.get("entities"):
            sentiment = article["entities"][0].get("sentiment_score", None)
        records.append({
            "date": article.get("published_at", ""),
            "symbol": symbol,
            "title": article.get("title", ""),
            "url": article.get("url", ""),
            "sentiment_score": sentiment
        })
    df = pd.DataFrame(records)
    if os.path.exists(FILE_PATH):
        existing = pd.read_csv(FILE_PATH)
        combined = pd.concat([existing, df], ignore_index=True)
        combined.drop_duplicates(subset=["title", "date"], inplace=True)
        combined.to_csv(FILE_PATH, index=False)
    else:
        df.to_csv(FILE_PATH, index=False)

def fetch_and_store_default_stocks():
    for stock in STOCKS:
        articles_collected = 0
        page = 1
        while articles_collected < ARTICLES_PER_STOCK:
            articles = get_news(stock, page=page, limit=ARTICLES_PER_REQUEST)
            if not articles:
                break
            store_articles(articles, stock)
            articles_collected += len(articles)
            page += 1
            time.sleep(0.3)

# On first load, cache articles for TSLA, NVDA, AAPL
if not os.path.exists(FILE_PATH):
    with st.spinner("Fetching and caching TSLA, NVDA, AAPL news..."):
        fetch_and_store_default_stocks()

# Display News
if ticker:
    st.markdown(f"### \ud83d\udcf0 News for **{ticker.upper()}**")
    if ticker.upper() in STOCKS:
        df = load_sentiment_data()
        articles = df[df["symbol"] == ticker.upper()].to_dict("records")
    else:
        articles = get_news(ticker.upper(), limit=10)

    if articles:
        sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}

        for article in articles:
            matched_entity = next((e for e in article.get("entities", []) if e["symbol"].upper() == ticker.upper()), None)
            if matched_entity:
                score = matched_entity.get("sentiment_score", 0)
                if score > 0.15:
                    sentiment_counts["Positive"] += 1
                elif score < -0.15:
                    sentiment_counts["Negative"] += 1
                else:
                    sentiment_counts["Neutral"] += 1

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
                title="\ud83d\udcca Sentiment Distribution"
            )
            st.plotly_chart(fig)

        for article in articles:
            matched_entity = next((e for e in article.get("entities", []) if e["symbol"].upper() == ticker.upper()), None)
            if matched_entity:
                sentiment_score = matched_entity.get("sentiment_score", 0)
                sentiment_label, emoji = interpret_sentiment(sentiment_score)
                if sentiment_filter != "All" and sentiment_label.split()[1] != sentiment_filter:
                    continue

                st.markdown(f"#### [{article['title']}]({article['url']})")
                st.markdown(f"\ud83d\udcf0 *{article['source']}*  |  \ud83d\udd52 *{article['published_at'][:10]}*")
                st.markdown(f"**Sentiment:** {emoji} {sentiment_label} ({sentiment_score:.2f})")
                st.markdown("---")
    else:
        st.warning("No news articles found.")
