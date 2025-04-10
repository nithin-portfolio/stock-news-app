import streamlit as st
import requests

# Title
st.title("📈 Senticker – Stock News with Sentiment")

# User input
ticker = st.text_input("Enter a stock ticker (e.g. TSLA, AAPL):", "TSLA")
sentiment_filter = st.selectbox("Filter by sentiment", ["All", "Positive", "Neutral", "Negative"])

# Get API token from secrets
API_TOKEN = st.secrets["API_TOKEN"]
BASE_URL = st.secrets["BASE_URL"]

# Fetch news
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

# Sentiment helper
def interpret_sentiment(score):
    if score > 0.15:
        return "Positive"
    elif score < -0.15:
        return "Negative"
    return "Neutral"

# Show results
if ticker:
    with st.spinner("Fetching news..."):
        news_data = get_news(ticker)

        if news_data:
            for article in news_data:
                for entity in article.get("entities", []):
                    if entity["symbol"].upper() == ticker.upper():
                        sentiment_score = entity.get("sentiment_score", 0)
                        sentiment = interpret_sentiment(sentiment_score)

                        # Apply filter
                        if sentiment_filter != "All" and sentiment != sentiment_filter:
                            continue

                        st.markdown(f"### [{article['title']}]({article['url']})")
                        st.markdown(f"📰 {article['source']} • 🕒 {article['published_at'][:10]}")
                        st.markdown(f"**Sentiment:** {sentiment} ({sentiment_score:.2f})")
                        st.markdown("---")
        else:
            st.warning("No news found.")
