import logging
import os
import json
from fetch_trend import fetch_trending_topics
from content import run_content_generation
from post import main as schedule_posts


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

PROGRESS_FILE = "progress.json"

def load_progress():
    """Load progress from file."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as file:
            return json.load(file)
    return {}

def save_progress(step, topic):
    """Save progress state."""
    progress = {"step": step, "topic": topic}
    with open(PROGRESS_FILE, "w") as file:
        json.dump(progress, file)

def main():
    """Main function to run the workflow."""
    progress = load_progress()

    # Fetch trending topics
    if progress.get("step") is None:
        logging.info("🚀 Fetching trending topics...")
        csv_file = fetch_trending_topics()
        if not csv_file:
            logging.warning("⚠ No trending topics found. Exiting...")
            return
        save_progress("content_generation", None)

    # Generate articles
    if progress.get("step") in [None, "content_generation"]:
        logging.info("📝 Generating articles...")
        run_content_generation()
        save_progress("image_download", None)

    # Download images & post to WordPress
    if progress.get("step") in [None, "content_generation", "image_download"]:
        logging.info("📸 Downloading images & posting articles...")
        schedule_posts()  # Ensure it resumes from last post
        save_progress("completed", None)

    logging.info("✅ Workflow completed successfully!")
    os.remove(PROGRESS_FILE)  # Cleanup after success
    
logging.info(f"📂 Current working directory: {os.getcwd()}")
logging.info(f"📄 Files in current directory: {os.listdir('.')}")
logging.info(f"📁 Subdirectories and contents in 'images': {os.listdir('images') if os.path.exists('images') else 'Not Found'}")


if __name__ == "__main__":
    main()
