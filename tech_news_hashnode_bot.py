import os
import sys
import requests
from datetime import datetime, timedelta
import json
import random

# --- Retrieve and verify API keys ---
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
HASHNODE_API_KEY = os.getenv("HASHNODE_API_KEY")
NEWSAPI_API_KEY = os.getenv("NEWSAPI_API_KEY")

if not MISTRAL_API_KEY:
    print("❌ ERROR : MISTRAL_API_KEY is not defined. Ensure the environment variable is correctly set and you have created a Mistral AI API key.")
    sys.exit(1)

if not HASHNODE_API_KEY:
    print("❌ ERROR : HASHNODE_API_KEY is not defined. Ensure the environment variable is correctly set.")
    sys.exit(1)

if not NEWSAPI_API_KEY:
    print("❌ ERROR : NEWSAPI_API_KEY is not defined. Ensure the environment variable is correctly set and you have created a NewsAPI.org API key.")
    sys.exit(1)

# --- Define the Mistral AI model to use and the API URL ---
MISTRAL_MODEL_NAME = "mistral-tiny" # Consider "mistral-large" or "mistral-medium" for longer/more complex articles
MISTRAL_API_BASE_URL = "https://api.mistral.ai/v1/chat/completions"

# --- Hashnode Configuration ---
HASHNODE_API_URL = "https://gql.hashnode.com/"

# IMPORTANT: REPLACE THIS WITH YOUR TECH NEWS PUBLICATION ID!
# You can find it in the dashboard URL of your Hashnode blog (e.g., https://hashnode.com/YOUR_ID/dashboard).
TECH_NEWS_HASHNODE_PUBLICATION_ID = "6859b71fd0e33fbfaf1676f5" # <-- **PASTE YOUR ID HERE**

# --- NewsAPI Configuration ---
NEWSAPI_BASE_URL = "https://newsapi.org/v2/everything"
NEWSAPI_QUERY = "technology OR AI OR cybersecurity OR software development" # Keywords for tech news
NEWSAPI_LANGUAGE = "en" # CHANGED: Language of news articles to English
NEWSAPI_SORT_BY = "relevancy" # "relevancy", "popularity", "publishedAt"

# --- GitHub Repository URL Variables ---
GITHUB_REPOSITORY = os.getenv('GITHUB_REPOSITORY')
GITHUB_REF = os.getenv('GITHUB_REF')

if GITHUB_REPOSITORY:
    GITHUB_USERNAME = GITHUB_REPOSITORY.split('/')[0]
    GITHUB_REPO_NAME = GITHUB_REPOSITORY.split('/')[1]
else:
    GITHUB_USERNAME = "your_username"
    GITHUB_REPO_NAME = "your_repo"      
    print("⚠️ GITHUB_REPOSITORY variables not found. Using default values. Ensure the script runs in a GitHub Actions environment.")

if GITHUB_REF and GITHUB_REF.startswith('refs/heads/'):
    GITHUB_BRANCH = GITHUB_REF.split('/')[-1]
else:
    GITHUB_BRANCH = "main"

COVER_IMAGES_DIR = "covers"

# --- Utility Functions ---

def is_image_url_valid(url):
    """
    Checks if a URL points to a valid image by making a HEAD request.
    """
    if not url:
        return False
    try:
        response = requests.head(url, timeout=5)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '')
        return content_type.startswith('image/')
    except requests.exceptions.RequestException as e:
        print(f"DEBUG: Image URL validation failed for {url}: {e}")
        return False

def get_github_raw_base_url():
    """Constructs the base URL for raw files in your GitHub repository."""
    return f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO_NAME}/{GITHUB_BRANCH}"

def get_random_cover_image_url():
    """
    Lists images in the specified directory and returns the raw URL of a random image.
    This is a fallback if no relevant image from the news article is found.
    """
    image_files = []
    covers_path = os.path.join(os.getenv('GITHUB_WORKSPACE', '.'), COVER_IMAGES_DIR)

    if not os.path.exists(covers_path):
        print(f"❌ ERROR : The cover images folder '{covers_path}' does not exist. Please create it or check the path.")
        return None

    try:
        for filename in os.listdir(covers_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                image_files.append(filename)
        
        if not image_files:
            print(f"⚠️ No image files found in the folder '{covers_path}'.")
            return None
        
        selected_file = random.choice(image_files)
        
        base_url = get_github_raw_base_url()
        full_image_url = f"{base_url}/{COVER_IMAGES_DIR}/{selected_file}"
        print(f"✅ Selected fallback cover image from covers folder: {selected_file}")
        return full_image_url

    except Exception as e:
        print(f"❌ ERROR reading cover image files : {e}")
        return None

# --- Mistral AI Authentication Test ---
def test_mistral_auth():
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MISTRAL_MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": "Test connection."
            }
        ]
    }

    print(f"🔎 Testing Mistral AI authentication with model '{MISTRAL_MODEL_NAME}' at URL: {MISTRAL_API_BASE_URL}")
    try:
        resp = requests.post(MISTRAL_API_BASE_URL, headers=headers, json=payload, timeout=30)
        print(f"Auth test Mistral status: {resp.status_code}")
        if resp.status_code == 200:
            print("✅ Mistral AI authentication successful and model accessible.")
            try:
                response_data = resp.json()
                if "choices" in response_data and response_data["choices"]:
                    print("✅ Model response in expected format (contains 'choices').")
                else:
                    print("⚠️ Valid model response but does not contain 'choices' in the expected format.")
            except json.JSONDecodeError:
                print("⚠️ Model response not valid JSON. This might be a Mistral AI server issue.")
        elif resp.status_code == 401:
            print("❌ Mistral AI authentication failed: 401 Unauthorized. Incorrect API key or insufficient permissions.")
            sys.exit(1)
        else:
            print(f"❌ Mistral AI authentication failed. Unexpected status: {resp.status_code}, Response: {resp.text}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR or connection issue during Mistral AI authentication test : {e}")
        sys.exit(1)

test_mistral_auth()

# --- Retrieve tech news via NewsAPI ---
def get_tech_news():
    today = datetime.now()
    from_date = (today - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S')

    params = {
        "q": NEWSAPI_QUERY,
        "language": NEWSAPI_LANGUAGE,
        "sortBy": NEWSAPI_SORT_BY,
        "apiKey": NEWSAPI_API_KEY,
        "from": from_date,
        "pageSize": 10 # Number of articles to retrieve
    }
    
    print(f"\n🔎 Retrieving tech news from NewsAPI.org for keywords : '{NEWSAPI_QUERY}'...")
    try:
        response = requests.get(NEWSAPI_BASE_URL, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        
        if data['status'] == 'ok' and data['articles']:
            print(f"✅ {len(data['articles'])} tech news articles retrieved.")
            recent_articles = [
                a for a in data['articles'] 
                if a['title'] and a['description'] and a['content'] and 
                   datetime.strptime(a['publishedAt'][:19], '%Y-%m-%dT%H:%M:%S').date() == today.date()
            ]
            
            if not recent_articles:
                print("⚠️ No relevant tech news articles found for today after filtering. Using a random article from the latest ones.")
                return random.choice(data['articles']) if data['articles'] else None
            
            # Return a random article from the recent ones
            return random.choice(recent_articles)
        elif data['status'] == 'ok' and not data['articles']:
            print("⚠️ NewsAPI.org returned no articles for the current query.")
            return None
        else:
            print(f"❌ ERROR from NewsAPI.org : {data.get('message', 'Message not available')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP ERROR retrieving tech news from NewsAPI.org : {e}")
        return None
    except Exception as e:
        print(f"❌ An unexpected error occurred while retrieving tech news : {e}")
        return None

# --- Article Generation via Mistral AI API ---
def generate_article():
    news_article = get_tech_news()
    
    if news_article:
        news_title = news_article.get('title', 'Unknown Tech News')
        news_description = news_article.get('description', '')
        news_content = news_article.get('content', '')
        news_url = news_article.get('url', '')

        # CHANGED: Updated prompt for more engaging title and refined instructions
        article_prompt = (
            f"Write a professional, detailed, and engaging blog post of at least 1500 words in English. "
            f"The article must be based on the following tech news: \n\n"
            f"News Title: {news_title}\n"
            f"Description: {news_description}\n"
            f"Initial Content: {news_content}\n"
            f"Source Link: {news_url}\n\n"
            f"Develop this topic in depth, adding context, analysis, future implications, and examples if possible. "
            f"**The very first line of the output MUST be a compelling, SEO-friendly, and catchy title (H1 markdown format, e.g., # Your Awesome Title).** "
            f"This title must immediately grab the reader’s attention, include strong and relevant SEO keywords, clearly reflect the core topic of the article, and be concise yet compelling. It should be written in a human, emotional, or curiosity-driven way that encourages clicks—even if it uses light, tasteful clickbait—while still staying true to the article’s content."
            f"Do not include 'Title: ', 'Author: ', or 'Publication Date: ' at the beginning. "
            f"The article must end with the signature 'By Nathan Remacle.'. "
            f"Optimize the content for SEO by naturally including relevant keywords. "
            f"Avoid formulations that sound 'AI' and adopt a human and engaging tone."
        )
        print(f"PROMPT FOR ARTICLE BASED ON NEWS: {news_title}")
    else:
        print("⚠️ No tech news retrieved. Generating an article on a generic tech topic.")
        # Fallback if no news is found
        keywords = [
            "cybersecurity", "cloud computing", "blockchain", "artificial intelligence", "machine learning",
            "deep learning", "quantum computing", "edge computing", "devops", "gitops", "kubernetes", "docker",
            "serverless", "microservices", "API management", "zero trust", "network security", "data privacy",
            "GDPR compliance", "penetration testing", "ethical hacking", "firewall configuration", "VPN technology",
            "multi-factor authentication", "natural language processing", "computer vision", "generative AI",
            "neural networks", "digital twins", "augmented reality", "virtual reality", "mixed reality", "data science",
            "big data analytics", "data lakes", "data warehouses", "ETL pipelines", "real-time analytics", "BI tools",
            "fintech", "regtech", "healthtech", "edtech", "agritech", "legaltech", "low-code", "no-code platforms",
            "mobile development", "responsive design", "progressive web apps", "cross-platform apps",
            "web development", "frontend frameworks", "react.js", "vue.js", "angular", "backend systems", "REST APIs",
            "GraphQL", "WebSockets", "event-driven architecture", "CI/CD pipelines", "infrastructure as code",
            "cloud-native apps", "cloud security", "multi-cloud strategy", "hybrid cloud", "platform engineering",
            "digital transformation", "IT strategy", "tech stack optimization", "legacy system modernization",
            "distributed systems", "peer-to-peer networks", "open-source software", "SaaS", "PaaS", "IaaS",
            "edge AI", "AI governance", "digital ethics", "algorithmic bias", "privacy by design",
            "digital forensics", "incident response", "threat detection", "security operations center (SOC)",
            "log management", "SIEM tools", "compliance automation", "container security", "code quality",
            "static code analysis", "unit testing", "test-driven development", "agile methodology", "scrum",
            "product management", "user experience (UX)", "human-computer interaction", "accessibility",
            "tech leadership", "innovation management", "IT consulting", "technology trends", "smart cities",
            "connected devices", "IoT platforms", "wearable tech", "5G networks", "digital identity", "biometrics",
            "passwordless authentication", "data monetization", "tech regulation", "AI legislation", "sustainable IT",
            "green computing", "digital sovereignty", "robotics", "autonomous systems", "intelligent automation",
            "chatbots", "virtual assistants", "real-time collaboration tools"
        ]
        chosen_keyword = random.choice(keywords)
        article_prompt = (
            "Write a professional, detailed, and engaging blog post of at least 1500 words in English on a current "
            f"topic related to '{chosen_keyword}'. "
            f"**The very first line of the output MUST be a compelling, SEO-friendly, and catchy title (H1 markdown format, e.g., # Your Awesome Title).** "
            f"Do not include 'Title: ', 'Author: ', or 'Publication Date: ' at the beginning. "
            f"The article must end with the signature 'By Nathan Remacle.'. "
            f"Optimize the content for SEO by naturally including relevant keywords. "
            f"Avoid formulations that sound 'AI' and adopt a human and engaging tone."
        )
        print(f"PROMPT FOR ARTICLE BASED ON GENERIC KEYWORD: {chosen_keyword}")

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MISTRAL_MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": article_prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 2500
    }

    print(f"\n🚀 Attempting to generate article with model '{MISTRAL_MODEL_NAME}'...")
    try:
        response = requests.post(
            MISTRAL_API_BASE_URL,
            headers=headers,
            json=payload,
            timeout=180
        )
        response.raise_for_status()

        print("Status code Mistral:", response.status_code)

        data = response.json()
        
        if 'choices' in data and data['choices'] and 'message' in data['choices'][0] and 'content' in data['choices'][0]['message']:
            article_content = data['choices'][0]['message']['content'].strip()
            # Pass the news_article along with content so we can extract its image URL later
            return article_content, news_article
        else:
            raise ValueError(f"Mistral AI response does not contain the expected chat completions format. Full response: {data}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP ERROR generating article with Mistral AI : {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ DATA ERROR in Mistral AI response : {e}")
        sys.exit(1)

# --- Hashnode Publication ---
def publish_article(content, news_article_data=None): # news_article_data is the full news article object
    publication_id = TECH_NEWS_HASHNODE_PUBLICATION_ID
    
    first_line_match = content.split('\n')[0].strip()
    extracted_title = ""
    if first_line_match.startswith('# '):
        extracted_title = first_line_match[2:].strip()
        content = content[len(first_line_match):].strip() 
    else:
        extracted_title = "Tech News Article from " + datetime.now().strftime("%d %B %Y - %H:%M")

    if "By Nathan Remacle." not in content:
        content += "\n\nBy Nathan Remacle."

    selected_cover_url = None
    # NEW LOGIC: Try to use image from news_article_data first
    if news_article_data and news_article_data.get('urlToImage'):
        news_image_url = news_article_data['urlToImage']
        print(f"DEBUG: Checking news article image URL: {news_image_url}")
        if is_image_url_valid(news_image_url):
            selected_cover_url = news_image_url
            print(f"✅ Using news article image as cover: {selected_cover_url}")
        else:
            print("⚠️ News article image URL is invalid or not an image. Falling back to covers folder.")
            selected_cover_url = get_random_cover_image_url()
    else:
        print("⚠️ No image URL found in news article data. Falling back to covers folder.")
        selected_cover_url = get_random_cover_image_url() # Fallback to covers folder

    mutation = """
    mutation PublishPost($input: PublishPostInput!) {
      publishPost(input: $input) {
        post {
          id
          title
          slug
          url
        }
      }
    }
    """
    
    variables = {
        "input": {
            "title": extracted_title,
            "contentMarkdown": content,
            "publicationId": publication_id,
            "tags": [], # Consider adding relevant tags based on news content
        }
    }
    
    if selected_cover_url:
        variables["input"]["coverImageOptions"] = {
            "coverImageURL": selected_cover_url,
            "isCoverAttributionHidden": True 
        }
        print(f"DEBUG: Hashnode cover image added to variables: {selected_cover_url}")
    else:
        print("DEBUG: No cover image added (no URL configured or valid image found).")


    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HASHNODE_API_KEY}"
    }

    print(f"\n✍️ Attempting to publish article '{extracted_title}' to Hashnode...")
    print(f"DEBUG: JSON Payload sent to Hashnode (without full content): {json.dumps(variables, indent=2)}")
    print(f"DEBUG: Start of Markdown content sent: {content[:200]}...")

    try:
        resp = requests.post(HASHNODE_API_URL, json={"query": mutation, "variables": variables}, headers=headers)
        
        print("Publish status:", resp.status_code)
        print("Publish response:", resp.text)
        
        response_data = resp.json()

        if 'errors' in response_data and response_data['errors']:
            print(f"❌ GraphQL ERROR from Hashnode when publishing article : {response_data['errors']}")
            sys.exit(1)

        post_url = None
        if 'data' in response_data and \
           'publishPost' in response_data['data'] and \
           'post' in response_data['data']['publishPost'] and \
           'url' in response_data['data']['publishPost']['post']:
            post_url = response_data['data']['publishPost']['post']['url']
            print(f"✅ Article published successfully : {extracted_title} at URL : {post_url}")
        else:
            print(f"✅ Article published successfully (URL not retrieved) : {extracted_title}")

    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP ERROR publishing article to Hashnode : {e}")
        print(f"Hashnode response on error : {resp.text if 'resp' in locals() else 'No response.'}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during publication : {e}")
        sys.exit(1)

# --- Main Execution ---
if __name__ == "__main__":
    print("Starting Hashnode bot.")
    try:
        # receive both article content and news_article_data from generate_article
        article_content, news_article_data = generate_article() 
        publish_article(article_content, news_article_data) # Pass news_article_data to publish_article
        print("\n🎉 Hashnode bot successfully completed!")
    except Exception as e:
        print(f"\nFATAL ERROR: A critical error occurred : {e}")
        sys.exit(1)