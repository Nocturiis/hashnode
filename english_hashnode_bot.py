import os
import sys
import requests
from datetime import datetime
import json
import random

# --- Retrieve and verify API keys ---
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
HASHNODE_API_KEY = os.getenv("HASHNODE_API_KEY") # Same Hashnode API key can be used for multiple publications

if not MISTRAL_API_KEY:
    print("❌ ERROR : MISTRAL_API_KEY is not defined. Ensure the environment variable is correctly set and you have created a Mistral AI API key.")
    sys.exit(1)

if not HASHNODE_API_KEY:
    print("❌ ERROR : HASHNODE_API_KEY is not defined. Ensure the environment variable is correctly set.")
    sys.exit(1)

# --- Define the Mistral AI model to use and the API URL ---
MISTRAL_MODEL_NAME = "mistral-tiny"
MISTRAL_API_BASE_URL = "https://api.mistral.ai/v1/chat/completions"

# --- Hashnode Configuration ---
HASHNODE_API_URL = "https://gql.hashnode.com/"

# --- MODIFIED: Specific Hashnode Publication ID for the ENGLISH blog ---
# YOU MUST REPLACE "YOUR_ENGLISH_HASHNODE_PUBLICATION_ID_HERE" with the actual ID from Hashnode
ENGLISH_HASHNODE_PUBLICATION_ID = "68488b76218d748963ca9c0f" 

# --- GitHub Repository URL Variables ---
GITHUB_REPOSITORY = os.getenv('GITHUB_REPOSITORY') # Format: 'user/repo'
GITHUB_REF = os.getenv('GITHUB_REF') # Format: 'refs/heads/main' or 'refs/heads/master'

# Extract username and repo name
if GITHUB_REPOSITORY:
    GITHUB_USERNAME = GITHUB_REPOSITORY.split('/')[0]
    GITHUB_REPO_NAME = GITHUB_REPOSITORY.split('/')[1]
else:
    GITHUB_USERNAME = "your_username" # Fallback if not in GH Actions environment
    GITHUB_REPO_NAME = "your_repo"      # Fallback
    print("⚠️ GITHUB_REPOSITORY variables not found. Using default values. Ensure the script runs in a GitHub Actions environment.")

# Extract branch name
if GITHUB_REF and GITHUB_REF.startswith('refs/heads/'):
    GITHUB_BRANCH = GITHUB_REF.split('/')[-1]
else:
    GITHUB_BRANCH = "main" # Fallback, usually 'main' or 'master'

# The folder where your cover images are located in the repository
COVER_IMAGES_DIR = "covers" # This can be the same folder as for the French blog

# --- Utility Functions ---

def get_github_raw_base_url():
    """Constructs the base URL for raw files in your GitHub repository."""
    return f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO_NAME}/{GITHUB_BRANCH}"

def get_random_cover_image_url():
    """
    Lists images in the specified directory and returns the raw URL of a random image.
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
        print(f"✅ Selected cover image : {selected_file}")
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

# --- Article Generation via Mistral AI API ---
def generate_article():
    # MODIFIED HERE: English article prompt
    article_prompt = (
        "Write a professional and detailed blog post of at least 1500 words in English on a topic "
        "(ideally current) related to information technology in its entirety. "
        "The title should be included at the beginning of the article content (first level heading, e.g., # Article Title). "
        "Do not start the article with 'Title: ', 'Author: ', or 'Publication Date: '. "
        "The article must end with the signature 'By Nathan Remacle.'. "
        "Optimize the content for SEO by naturally including relevant keywords. "
        "Avoid formulations that sound 'AI' and adopt a human and engaging tone."
    )
    
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
            print("DEBUG: Response processed as Mistral AI Chat Completions API.")
        else:
            raise ValueError(f"Mistral AI response does not contain the expected chat completions format. Full response: {data}")
        
        return article_content
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP ERROR generating article with Mistral AI : {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ DATA ERROR in Mistral AI response : {e}")
        sys.exit(1)

# --- Hashnode Publication ---
def publish_article(content):
    # MODIFIED HERE: Use the specific English publication ID
    publication_id = ENGLISH_HASHNODE_PUBLICATION_ID 
    
    first_line_match = content.split('\n')[0].strip()
    extracted_title = ""
    if first_line_match.startswith('# '):
        extracted_title = first_line_match[2:].strip()
        content = content[len(first_line_match):].strip() # Remove title from content
    else:
        extracted_title = "Article from " + datetime.now().strftime("%d %B %Y - %H:%M")

    # Ensure signature is present (MODIFIED HERE: English signature)
    if "By Nathan Remacle." not in content:
        content += "\n\nBy Nathan Remacle."

    selected_cover_url = get_random_cover_image_url()

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
            "tags": [],
        }
    }
    
    if selected_cover_url:
        variables["input"]["coverImageOptions"] = {
            "coverImageURL": selected_cover_url,
            "isCoverAttributionHidden": True # Set to True to hide default attribution
        }
        print(f"DEBUG: Hashnode cover image added to variables: {selected_cover_url}")
    else:
        print("DEBUG: No cover image added (no URL configured or empty list).")


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
        article = generate_article()
        publish_article(article)
        print("\n🎉 Hashnode bot successfully completed!")
    except Exception as e:
        print(f"\nFATAL ERROR: A critical error occurred : {e}")
        sys.exit(1)