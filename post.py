import os
import pandas as pd
import requests
import datetime
import time
import json
import base64
import logging
import ssl
import xmlrpc.client
import subprocess
from PIL import Image
import nltk
from nltk.corpus import stopwords
from io import BytesIO
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost
from wordpress_xmlrpc.methods.media import UploadFile
from wordpress_xmlrpc.methods.taxonomies import GetTerms
from wordpress_xmlrpc.methods.posts import EditPost


# ✅ Force TLS 1.2+ and relax strict SSL verification
ssl_context = ssl.create_default_context()
ssl_context.options |= ssl.OP_NO_SSLv2
ssl_context.options |= ssl.OP_NO_SSLv3
ssl_context.options |= ssl.OP_NO_TLSv1
ssl_context.options |= ssl.OP_NO_TLSv1_1
ssl_context.check_hostname = False  # Helps avoid hostname mismatches
ssl_context.verify_mode = ssl.CERT_OPTIONAL  # Loosen strict SSL verification

# ✅ Corrected SSLTransport class
class SSLTransport(xmlrpc.client.SafeTransport):
    def __init__(self, context=None):
        super().__init__()
        self.context = context or ssl.create_default_context()

def make_connection(self, host):
    conn = super().make_connection(host)
    if conn.sock and not isinstance(conn.sock, ssl.SSLSocket):
        conn.sock = self.context.wrap_socket(conn.sock, server_hostname=host)
    return conn


nltk.download('stopwords')

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# WordPress Credentials
WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")

# Paths and Files
CSV_PATH = "generated_articles.csv"
LOG_FILE = "upload_log.json"
SCHEDULE_FILE = "schedule.json"  # Track last scheduled date
IMAGE_SAVE_PATH = "images"

#APIs For Image Search
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

# Load schedule tracking file
if os.path.exists(SCHEDULE_FILE):
    with open(SCHEDULE_FILE, "r") as f:
        try:
            schedule_data = json.load(f)
        except json.JSONDecodeError:
            schedule_data = {}
else:
    schedule_data = {}  # Initialize if file doesn't exist

# Ensure last_scheduled_day exists in schedule.json
if "last_scheduled_day" not in schedule_data:
    schedule_data["last_scheduled_day"] = datetime.datetime.today().strftime("%Y-%m-%d")

# Load log file to track scheduled posts
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "r") as f:
        log_data = json.load(f)
else:
    log_data = {"scheduled_titles": []}  # Track previously posted titles

# 🔹 Manually encode credentials (Base64)
credentials = f"{WP_USERNAME}:{WP_PASSWORD}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()

# 🔹 Set headers for authentication
headers = {
    "Authorization": f"Basic {encoded_credentials}"
}

# ✅ Initialize WordPress client with SSL transport
client = Client(WP_URL, WP_USERNAME, WP_PASSWORD, transport=SSLTransport(ssl_context))

# ✅ Apply SSL context to ensure secure connection
#client.transport.ssl_context = ssl_context
client.transport.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
client.headers = headers 


def get_next_schedule_date():
    """Get today's date for scheduling posts and update the schedule log."""
    today = datetime.date.today()

    # Update schedule.json with today's date
    schedule_data["last_scheduled_day"] = today.strftime("%Y-%m-%d")
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedule_data, f, indent=4)

    return today



def get_category(title):
    """Determine category based on the title."""
    if any(word in title.lower() for word in ["football", "cricket", "basketball","Baseball ","nba", "match", "game"]):
        return "Sports"
    return "Entertainment"
def fetch_or_generate_images(topic):
    """Search relevant images using Google Custom Search API and save them."""

    def fetch_images(size):
        """Fetch images of a given size."""
        params = {
            "q": topic,
            "cx": SEARCH_ENGINE_ID,
            "key": GOOGLE_API_KEY,
            "searchType": "image",
            "num": 5,  # Fetch more images to filter better
            "safe": "active",
            "imgSize": size
        }
        response = requests.get(GOOGLE_SEARCH_URL, params=params, verify=True)  # Ensure SSL verification
        response.raise_for_status()
        return response.json()

    def download_image(img_url, index):
        """Download and save image if it meets size requirements."""
        try:
            img_response = requests.get(img_url, stream=True)
            img_response.raise_for_status()

            # Detect format
            img_format = img_response.headers["Content-Type"].split("/")[-1].lower()
            if img_format not in ["jpeg", "jpg", "png", "webp"]:
                print(f"❌ Unsupported format: {img_format} ({img_url})")
                return None

            # Open image
            img = Image.open(BytesIO(img_response.content))
            width, height = img.size

            # ✅ Filter images strictly: Minimum 496x496 resolution
            if width >= 496 and height >= 350:
                sanitized_topic = "".join(c for c in topic if c.isalnum() or c in " _-")
                img_name = f"{sanitized_topic[:90].replace(' ', '_')}_{index+1}.{img_format}"
                img_path = os.path.join("images", img_name)
                # Ensure "images" folder exists
                os.makedirs("images", exist_ok=True)
                img.save(img_path, img_format.upper())

                print(f"✅ Image saved: {img_path} ({width}x{height})")
                return img_path
            else:
                print(f"⚠ Skipping small/blurry image: {width}x{height}")
                return None

        except Exception as img_err:
            print(f"❌ Error downloading image: {img_url} | {img_err}")
            return None

    # ✅ Try large images first
    try:
        search_results = fetch_images("large")
        if "items" not in search_results:
            print(f"⚠ No large images found for {topic}. Trying medium size...")
            search_results = fetch_images("medium")
            if "items" not in search_results:
                print(f"❌ No images found for {topic}. Skipping article.")
                return None  # No images found

        image_filenames = []
        for i, item in enumerate(search_results["items"][:10]):  # Check more images
            img_path = download_image(item["link"], i)
            if img_path:
                image_filenames.append(img_path)
            if len(image_filenames) >= 2:
                break  # Stop after saving 2 good images

        if not image_filenames:
            print(f"⚠ No suitable images found for {topic}. Skipping article.")
            return None

        return image_filenames

    except Exception as e:
        print(f"❌ Error fetching images for {topic}: {e}")
        return None

def upload_image(image_path, retries=3):
    """Upload an image to WordPress and return its URL."""
    for attempt in range(retries):
        try:
            with open(image_path, "rb") as img_file:
                data = {
                    'name': os.path.basename(image_path),
                    'type': 'image/jpeg',
                    'bits': xmlrpc.client.Binary(img_file.read()),  # Convert to binary format
                }
            
            response = client.call(UploadFile(data))

            if response:
                print(f"✅ Image uploaded successfully: {response['url']} (ID: {response['id']})")
                return response["id"], response["url"]
        
        except xmlrpc.client.ProtocolError as e:
            print(f"⚠️ Attempt {attempt+1} failed: Protocol Error - {e.errmsg}")
        except xmlrpc.client.Fault as e:
            print(f"⚠️ Attempt {attempt+1} failed: XML-RPC Fault - {e.faultString}")
        except ssl.SSLError as e:
            print(f"⚠️ Attempt {attempt+1} failed: SSL Error - {str(e)}")
        except Exception as e:
            print(f"⚠️ Attempt {attempt+1} failed: Unexpected Error - {str(e)}")
        
        time.sleep(5)  # Wait before retrying
    
    print(f"❌ Image upload failed after {retries} attempts: {image_path}")
    return None

def generate_tags(title, topic):
    """Generate meaningful tags from title and topic"""
    words = title.lower().split() + topic.lower().split()  # Combine title and topic
    filtered_words = [word for word in words if word not in stopwords.words('english') and len(word) > 3]  
    return list(set(filtered_words))  # Remove duplicates


# ✅ Schedule Post Function
def schedule_post(title, content, category, tags, uploaded_image_ids, uploaded_image_urls, schedule_date, time_slot):
    """Schedule a post on WordPress."""

    post = WordPressPost()
    post.title = title
    post.content = content
    post.post_status = "future"
    post.terms_names = {"category": [category], "post_tag": tags}
    post.date = datetime.datetime.combine(schedule_date, time_slot)

    # ✅ Set Featured Image (Use Already Uploaded Image)
    if uploaded_image_ids:
        post.thumbnail = uploaded_image_ids[0]
        print(f"✅ Featured Image ID: {uploaded_image_ids[0]}")

    post_id = client.call(NewPost(post))

    # ✅ Ensure Featured Image is Set
    if uploaded_image_ids:
        client.call(EditPost(post_id, {'post_thumbnail': uploaded_image_ids[0]}))

    return post_id


# ✅ Main Function
def main():
    
    df = pd.read_csv(CSV_PATH)
   # next_schedule_date = datetime.date.today() + datetime.timedelta(days=1)  # Start scheduling from tomorrow

    # I want to start schedluing today
    next_schedule_date = datetime.date.today()
    scheduled_count = 0
    time_slots = [datetime.time(h, 0) for h in range(8, 24, 2)]  # Every 2 hours

    for index, row in df.iterrows():
        title, article, topic = row["Title"], row["Article"], row["Topic"]

        # ✅ Check for Duplicate Titles
        if title in log_data["scheduled_titles"]:
            print(f"⚠ Skipping duplicate article: {title}")
            continue

        category = get_category(title)
        tags = generate_tags(title, topic)
        images = fetch_or_generate_images(topic)

        # ✅ Skip if No Images Found
        if not images:
            print(f"⚠ Skipping article due to no images: {title}")
            continue  

        # ✅ Upload Images and Store URLs
        # ✅ Upload Images and Store ID & URL
        print(f"📸 Images to upload: {images}")
        uploaded_images = [upload_image(img) for img in images if img]
        uploaded_images = [(img_id, img_url) for img_id, img_url in uploaded_images if img_id]
        print(f"🔼 Uploaded Images: {uploaded_images}")

        # Extract only image IDs for featured image
        uploaded_image_ids = [img[0] for img in uploaded_images]
        uploaded_image_urls = [img[1] for img in uploaded_images]
                # ✅ Skip if No Image Upload Was Successful
        if not uploaded_image_urls:
            print(f"❌ No valid images uploaded for: {title}. Skipping this article.")
            continue

        # ✅ Insert Images in Article (Ensuring Correct URLs)
        h2_headings = article.split("<h2>")

        if len(uploaded_image_urls) > 0 and len(h2_headings) > 1:
        # Use second image if available, otherwise use the first image
            img_to_use = uploaded_image_urls[1] if len(uploaded_image_urls) > 1 else uploaded_image_urls[0]
            h2_headings[1] = f'<h2>{h2_headings[1]}<br><img src="{img_to_use}" alt="{topic}"></h2>'

        if len(uploaded_image_urls) > 0 and len(h2_headings) > 3:
            # Use first image as a fallback if the second one is not available
            h2_headings[3] = f'<h2>{h2_headings[3]}<br><img src="{uploaded_image_urls[0]}" alt="{topic}"></h2>'

        article = "<h2>".join(h2_headings)


        # ✅ Schedule Post
        post_id = schedule_post(title, article, category, tags, uploaded_image_ids, uploaded_image_urls, next_schedule_date, time_slots[scheduled_count])
        print(f"✅ Scheduled: {title} on {next_schedule_date} at {time_slots[scheduled_count]} (Post ID: {post_id})")

        # ✅ Log Scheduled Post
        log_data["scheduled_titles"].append(title)
        with open(LOG_FILE, "w") as log_file:
            json.dump(log_data, log_file)

        scheduled_count += 1

