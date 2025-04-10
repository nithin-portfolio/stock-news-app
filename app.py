import streamlit as st
import requests
import plotly.express as px

# Title
st.title("📈 Senticker – Curated Stock News with Sentiment")

# Sidebar inputs
st.sidebar.header("🔎 Search")
ticker = st.sidebar.text_input("Enter a stock ticker (e.g. TSLA, AAPL):", "TSLA")
sentiment_filter = st.sidebar.selectbox("🧠 Filter by Sentiment", ["All", "Positive", "Neutral", "Negative"])

# API token from secrets
API_TOKEN = st.secrets["API_TOKEN"]
BASE_URL = st.secrets["BASE_URL"]

# Function to fetch news from API
def get_news(ticker):
    url = BASE_URL
    params = {
        "api_token": API_TOKEN,
        "symbols": ticker,
        "language": "en",
        "limit": 10
    }
    response = requests.get(url, params=params)
    return response.json().get("data", [])

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
    st.markdown(f"### 📡 News for **{ticker.upper()}**")

    with st.spinner("Fetching news..."):
        articles = get_news(ticker)

        if articles:
            
            # After fetching articles
            sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
            sentiment_scores_map = {}

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

            # Show pie chart only if there's data
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
            
            for article in articles:
                matched_entity = next((e for e in article.get("entities", []) if e["symbol"].upper() == ticker.upper()), None)
                if matched_entity:
                    sentiment_score = matched_entity.get("sentiment_score", 0)
                    sentiment_label, emoji = interpret_sentiment(sentiment_score)

                    # Apply sentiment filter
                    if sentiment_filter != "All" and sentiment_label.split()[1] != sentiment_filter:
                        continue

                    # Display article
                    st.markdown(f"#### [{article['title']}]({article['url']})")
                    st.markdown(f"📰 *{article['source']}*  |  🕒 *{article['published_at'][:10]}*")
                    st.markdown(f"**Sentiment:** {emoji} {sentiment_label} ({sentiment_score:.2f})")
                    st.markdown("---")
        else:
            st.warning("No news articles found.")