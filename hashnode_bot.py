import os
import requests
from datetime import datetime

OPENROUTER_API_KEY = os.getenv("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")
HASHNODE_API_KEY = os.getenv("cccd8350-e12e-419f-b437-2d5b8f286e9f")

# Hashnode GraphQL endpoint
HASHNODE_API_URL = "https://gql.hashnode.com/"

def generate_article():
    prompt = "Écris un article de blog (~500 mots) sur une tendance actuelle en intelligence artificielle."
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
    return response.json()["choices"][0]["message"]["content"]

def get_publication_id():
    query = """
    query {
      me {
        publication {
          _id
        }
      }
    }
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": HASHNODE_API_KEY
    }
    response = requests.post(HASHNODE_API_URL, json={"query": query}, headers=headers)
    return response.json()['data']['me']['publication']['_id']

def publish_article(content):
    publication_id = get_publication_id()
    title = "Article IA - " + datetime.now().strftime("%d %B %Y")
    
    mutation = """
    mutation CreateStory($input: CreateStoryInput!) {
      createStory(input: $input) {
        post {
          title
          slug
        }
      }
    }
    """
    variables = {
        "input": {
            "title": title,
            "contentMarkdown": content,
            "publicationId": publication_id,
            "isRepublished": False,
            "tags": [{"_id": "64d3ac20b4110f0001e6aa5b", "name": "Artificial Intelligence"}],  # AI tag
            "coverImageOptions": {"enabled": False},
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": HASHNODE_API_KEY
    }

    response = requests.post(HASHNODE_API_URL, json={"query": mutation, "variables": variables}, headers=headers)
    if response.status_code == 200:
        print("✅ Article publié :", response.json())
    else:
        print("❌ Échec de publication :", response.status_code, response.text)

if __name__ == "__main__":
    article = generate_article()
    publish_article(article)
