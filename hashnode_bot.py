import os
import sys
import requests
from datetime import datetime

# --- Récupération et vérification des clés d'API ---
OPENROUTER_API_KEY = os.getenv("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")
HASHNODE_API_KEY   = os.getenv("cccd8350-e12e-419f-b437-2d5b8f286e9f")

if not OPENROUTER_API_KEY:
    print("❌ ERREUR : OPENROUTER_API_KEY n'est pas défini.")
    sys.exit(1)

if not HASHNODE_API_KEY:
    print("❌ ERREUR : HASHNODE_API_KEY n'est pas défini.")
    sys.exit(1)

# --- Test d'authentification OpenRouter ---
def test_openrouter_auth():
    resp = requests.get(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    )
    print("🔎 Auth test status:", resp.status_code)
    print("🔎 Auth test response:", resp.text)
    if resp.status_code != 200:
        print("❌ Échec de l’authentification OpenRouter, vérifie ta clé.")
        sys.exit(1)

test_openrouter_auth()

# --- Génération de l'article via OpenRouter.ai ---
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
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        json=payload,
        headers=headers
    )

    print("Status code:", response.status_code)
    print("Response text:", response.text)

    data = response.json()
    if "choices" not in data:
        raise ValueError("La réponse de l'API OpenRouter ne contient pas 'choices'.")
    return data["choices"][0]["message"]["content"]

# --- Récupération de l'ID de la publication Hashnode ---
HASHNODE_API_URL = "https://gql.hashnode.com/"

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
    resp = requests.post(HASHNODE_API_URL, json={"query": query}, headers=headers)
    resp.raise_for_status()
    return resp.json()['data']['me']['publication']['_id']

# --- Publication de l'article sur Hashnode ---
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
            "tags": [{"_id": "64d3ac20b4110f0001e6aa5b", "name": "Artificial Intelligence"}],
            "coverImageOptions": {"enabled": False},
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": HASHNODE_API_KEY
    }

    resp = requests.post(HASHNODE_API_URL, json={"query": mutation, "variables": variables}, headers=headers)
    print("Publish status:", resp.status_code)
    print("Publish response:", resp.text)
    resp.raise_for_status()
    print("✅ Article publié avec succès :", title)

# --- Exécution principale ---
if __name__ == "__main__":
    article = generate_article()
    publish_article(article)
