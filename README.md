# WordPress Auto Poster

## Description
WordPress Auto Poster is a powerful automation tool that generates and posts AI-written articles to WordPress websites. The script leverages AI models for content creation and integrates with Google Trends to fetch trending topics. Additionally, it ensures high-quality posts with relevant images using Google Search API.

## Need for the Project
Manually creating and publishing blog posts can be time-consuming, especially for websites requiring frequent updates. This project solves the problem by:
- Automating content creation using AI.
- Fetching trending topics to ensure relevance.
- Searching for and inserting images dynamically.
- Posting articles to WordPress on a schedule.
- Reducing manual effort while maintaining consistency.

## Features
- **AI-Powered Content Generation**: Uses OpenRouter API (Free) for generating articles and automatically switches to Hyperbolic API (Paid) if OpenRouter fails.
- **Google Trends Integration**: Fetches trending topics for categories like Entertainment, Celebrity, Hollywood, and Sports.
- **Automated Image Search & Upload**: Finds relevant images using Google Custom Search API and uploads them to WordPress.
- **Smart Image Handling**:
  - First image is set as the featured image.
  - Additional images are inserted after specific `<h2>` headings in the article.
  - If only one image is found, it is used in both positions.
- **Scheduled Posting**: Automatically schedules 12 posts per day at 2-hour intervals.
- **Error Handling & Logging**: Logs errors, API failures, and posts to ensure smooth operation and debugging.
- **Fallback Mechanism**:
  - If OpenRouter API fails twice, it switches to Hyperbolic API.
  - Ensures no interruptions in content generation.

## Technologies Used
- **Python**
- **OpenRouter API** (AI Content Generation)
- **Hyperbolic API** (Fallback AI Content Generation)
- **Google Trends RSS Feed** (Trending Topics)
- **Google Custom Search API** (Image Search)
- **WordPress XML-RPC API** (Auto Posting)
- **NLTK** (Text Processing)
- **BeautifulSoup** (Web Scraping)
- **Pandas** (Data Handling)
- **PIL (Pillow)** (Image Processing)
- **Logging & Error Handling** (Ensuring smooth execution)

## API Requirements
Before running the script, you need to set up the following APIs:

1. **OpenRouter API** (Free AI Content Generation)
   - Sign up at [OpenRouter](https://openrouter.ai/)
   - Get an API key from the dashboard.

2. **Hyperbolic API** (Paid AI Content Generation - Fallback Option)
   - Sign up at [Hyperbolic API](https://app.hyperbolic.xyz/)
   - Obtain an API key (paid service).

3. **Google Custom Search API** (Image Search)
   - Go to [Google Developers Console](https://console.cloud.google.com/)
   - Enable Custom Search API and generate an API key.
   - Create a Custom Search Engine (CSE) and note the Search Engine ID.

4. **WordPress XML-RPC API** (Auto Posting)
   - Enable XML-RPC on your WordPress site.
   - Obtain the site URL, username, and application password.

## Installation & Usage

### 1. Clone the Repository
```sh
$ git clone https://github.com/shubhr86/Wordpress-Auto-Poster.git
$ cd Wordpress-Auto-Poster
```

### 2. Install Dependencies
```sh
$ pip install -r requirements.txt
```

### 3. Change these in the code
```sh
OPENROUTER_API_KEY=your_openrouter_api_key
HYPERBOLIC_API_KEY=your_hyperbolic_api_key
WP_URL=https://yourwordpresssite.com/xmlrpc.php
WP_USERNAME=your_username
WP_PASSWORD=your_password
GOOGLE_API_KEY=your_google_api_key
SEARCH_ENGINE_ID=your_search_engine_id
```

### 4. Run the Script
```sh
$ python main.py
```
This will start the automation process:
1. Fetch trending topics from Google Trends.
2. Generate AI-based articles.
3. Find and upload relevant images.
4. Post articles to WordPress on a schedule.

### 5. Automate with GitHub Actions
The script can run daily at 9 AM IST using GitHub Actions.
To enable:
- Set up **GitHub Secrets** with the required API keys.
- Push the project to GitHub.
- The action will automatically run as per the schedule.

## Repository
[GitHub Repo](https://github.com/shubhr86/Wordpress-Auto-Poster)

