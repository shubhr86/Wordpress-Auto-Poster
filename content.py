import os
import pandas as pd
import time
import asyncio
import logging
import requests
import re
from openai import AsyncOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Set API Keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
HYPERBOLIC_API_KEY = os.getenv("HYPERBOLIC_API_KEY")

# Choose models (fallback if one fails)
MODELS = [
    "google/gemma-3-27b-it:free",
    "deepseek/deepseek-chat-v3-0324:free"
]

# Initialize OpenAI Async Client
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Read topics CSV
df = pd.read_csv("top4_trending_topics.csv")
print("CSV Columns:", df.columns)

# Define output file
output_path = "generated_articles.csv"

# Function to generate an article asynchronously
async def generate_article(topic, model):
    prompt = f"""
You are a professional journalist and content writer. Your goal is to write engaging, conversational, and natural-sounding articles that feel like they were written by a human. Avoid generic phrasing, robotic structures, and predictable patterns.

### **Instructions:**
- Write an **SEO-optimized** article on **"{topic}"** designed for a **WordPress** audience.
- **Title Format:** Generate a compelling and engaging title related to {topic}.
- Keep the **tone friendly, engaging, and slightly opinionated**—as if you're personally guiding the reader.
- Use **short and long sentences** to create a natural rhythm.
- **Avoid overuse of transition words like "Furthermore" or "Moreover"**—write the way people actually talk.
- Ask **rhetorical questions** to engage the reader.
- Use **real-life examples, personal experiences, or historical references** where applicable.
- **DO NOT overuse complex vocabulary**—keep it simple and readable.
- Do not use Buzzwords.

### **Formatting Guidelines:**
- **Start the article with:** `title: [Generated Title]`
- **Write the article body after the title without repeating the title.**
- Include **5-7 `<h2>` headings** and **4-7 `<h3>` subheadings**.
- Use `<ul>`, `<ol>`, and `<li>` to break down information naturally.
- **Do not include "Okay, here’s your article..." or any AI-style introductions.**
- **Do not copy from AI-generated sources or follow overly structured templates.**
- Do not use ###,*** and any symbol in the article.

Write naturally, as if you were a journalist explaining this to a friend.
"""
    
    retries = 2
    for _ in range(retries):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.7,
            )

            if not response or not hasattr(response, "choices") or not response.choices:
                logging.error(f"❌ Empty response from model {model} for topic '{topic}'")
                continue

            article = response.choices[0].message.content

            # ✅ Clean Markdown formatting
            article = article.replace("### ", "<h2>").replace("## ", "<h2>")  # Convert headings
            article = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", article)  # Convert bold
            article = re.sub(r"(?<!<h2>)[*_](.*?)[*_](?!</h2>)", r"\1", article)  # Remove stray symbols

            if "title:" in article:
                split_article = article.split("\n", 1)
                title = split_article[0].replace("title:", "").strip()
                content = split_article[1].strip() if len(split_article) > 1 else ""
            else:
                logging.warning(f"⚠️ No title found for topic '{topic}'. Using default title.")
                title = topic
                content = article.strip()

            return title, content
        except Exception as e:
            logging.error(f"Error using model {model}: {e}")

    # If OpenRouter API fails, switch to Hyperbolic API
    logging.info("🔄 Switching to Hyperbolic API")
    try:
        url = "https://api.hyperbolic.xyz/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {HYPERBOLIC_API_KEY}"
        }
        data = {
            "messages": [{
                "role": "user",
                "content": prompt
            }],
            "model": "meta-llama/Llama-3.3-70B-Instruct",
            "max_tokens": 1500,
            "temperature": 0.3,
            "top_p": 0.5
        }
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        if "choices" in result and result["choices"]:
            article = result["choices"][0]["message"]["content"]

            if "title:" in article:
                split_article = article.split("\n", 1)
                title = split_article[0].replace("title:", "").strip()
                content = split_article[1].strip() if len(split_article) > 1 else ""
            else:
                title = topic
                content = article.strip()

            return title, content
    except Exception as e:
        logging.error(f"❌ Hyperbolic API failed: {e}")
    
    return None, None

# Function to process articles one by one
async def process_articles():
    """Processes trending topics and generates articles."""
    df = pd.read_csv("top4_trending_topics.csv")
    columns = ["Title", "Article", "Topic"]
    new_articles = []

    for _, row in df.iterrows():
        topic = row["Topic"]
        logging.info(f"🔄 Generating article for: {topic}...")

        for model in MODELS:
            title, article_text = await generate_article(topic, model)
            if title and article_text:
                new_articles.append([title, article_text, topic])
                logging.info(f"✅ Article generated for {topic}")
                break

    if new_articles:
        result_df = pd.DataFrame(new_articles, columns=columns)
        result_df.to_csv("generated_articles.csv", mode="w", header=True, index=False)
        logging.info("✅ Articles saved to generated_articles.csv")

def run_content_generation():
    """Runs the async content generation process."""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(process_articles())
