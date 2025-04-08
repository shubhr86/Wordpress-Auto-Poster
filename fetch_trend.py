import requests
import time
import logging
import pandas as pd
import pytz
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define countries and their Google Trends RSS feeds
tier_1_countries = {
    "United States": "https://trends.google.com/trending/rss?geo=US",
}

def get_trending_topics(url):
    """Fetch trending topics from Google Trends RSS feed."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "xml")

        topics = []
        current_time = datetime.now(pytz.UTC)  # Timezone-aware UTC datetime
        time_threshold = current_time - timedelta(hours=12)  # Extend time range to 12 hours

        for item in soup.find_all("item"):
            title = item.title.text.strip()
            traffic = item.find("ht:approx_traffic")
            traffic = traffic.text.strip().replace("+", "").replace("K", "000").replace("M", "000000") if traffic else "0"
            traffic = int(traffic) if traffic.isdigit() else 0
            link = item.link.text.strip() if item.link else "N/A"
            image = item.find("ht:picture")
            image = image.text.strip() if image else "N/A"

            # Extract and convert pubDate to timezone-aware datetime
            pub_date_str = item.pubDate.text.strip()
            pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")

            # Only include topics within the last 12 hours
            if pub_date >= time_threshold:
                topics.append({
                    "title": title,
                    "traffic": traffic,
                    "link": link,
                    "image": image
                })

        # Sort topics by traffic in descending order and return top 12
        return sorted(topics, key=lambda x: x["traffic"], reverse=True)[:2]
    except Exception as e:
        logging.error(f"❌ Error fetching trends from {url}: {str(e)}")
        return []

def fetch_trending_topics():
    """Fetch trending topics and save them to a CSV file."""
    all_trending_topics = {}

    for country, url in tier_1_countries.items():
        logging.info(f"🚀 Fetching trends for {country}...")
        topics = get_trending_topics(url)
        if topics:
            all_trending_topics[country] = topics
        time.sleep(2)  # Prevents rate-limiting issues

    csv_data = []
    for country, topics in all_trending_topics.items():
        for topic in topics:
            csv_data.append([country, topic["title"], topic["traffic"], topic["link"], topic["image"]])

    # Save to CSV if topics are found
    if csv_data:
        df = pd.DataFrame(csv_data, columns=["Country", "Topic", "Traffic", "Link", "Image"])
        filename = "top4_trending_topics.csv"
        df.to_csv(filename, index=False)
        logging.info(f"✅ Data saved to {filename} with {len(csv_data)} topics.")
        return filename
    else:
        logging.warning("⚠️ No trending topics found, CSV file not created.")
        return None

if __name__ == "__main__":
    fetch_trending_topics()
