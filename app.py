import streamlit as st
import requests
from datetime import datetime

API_TOKEN = st.secrets["API_TOKEN"]
BASE_URL = st.secrets["BASE_URL"]

st.set_page_config(page_title="Stock News Sentiment", layout="centered")

st.title("📈 Stock News with Sentiment Analysis")

ticker = st.text_input("Enter a stock ticker (e.g., TSLA, AAPL)", "TSLA")

if st.button("🔍 Get News"):
    with st.spinner("Fetching news..."):
        params = {
            "symbols": ticker.upper(),
            "filter_entities": "true",
            "language": "en",
            "limit": 5,
            "api_token": API_TOKEN
        }

        response = requests.get(BASE_URL, params=params)

        if response.status_code == 200:
            data = response.json()
            articles = data.get("data", [])

            if not articles:
                st.warning("No news articles found.")
            else:
                for article in articles:
                    st.markdown("---")
                    st.subheader(article["title"])
                    st.write(f"**Published:** {datetime.fromisoformat(article['published_at'].replace('Z', '+00:00')).strftime('%b %d, %Y %H:%M')} UTC")
                    st.write(article["description"] or article["snippet"])
                    st.image(article["image_url"], width=300)
                    st.markdown(f"[🔗 Read more]({article['url']})")

                    for entity in article.get("entities", []):
                        if entity.get("symbol") == ticker.upper():
                            sentiment = entity.get("sentiment_score", 0)
                            emoji = "😐"
                            if sentiment > 0.2:
                                emoji = "😊 Positive"
                            elif sentiment < -0.2:
                                emoji = "😠 Negative"
                            else:
                                emoji = "😐 Neutral"
                            st.info(f"**Sentiment Score**: {sentiment:.2f} ({emoji})")
        else:
            st.error(f"Failed to fetch news. Error code: {response.status_code}")