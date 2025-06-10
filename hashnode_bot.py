import os
import sys
import requests
from datetime import datetime

# --- Récupération et vérification des clés d'API ---
HUGGINGFACE_API_KEY = os.getenv("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")
HASHNODE_API_KEY     = os.getenv("cccd8350-e12e-419f-b437-2d5b8f286e9f")

if not HUGGINGFACE_API_KEY:
    print("❌ ERREUR : HUGGINGFACE_API_KEY n'est pas défini.")
    sys.exit(1)

if not HASHNODE_API_KEY:
    print("❌ ERREUR : HASHNODE_API_KEY n'est pas défini.")
    sys.exit(1)

# --- Test d'authentification Hugging Face ---
def test_hf_auth():
    resp = requests.get(
        "https://api-inference.huggingface.co/models/bigscience/bloomz",
        headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    )
    print("🔎 Auth test HF status:", resp.status_code)
    if resp.status_code not in (200, 503):
        print("❌ Échec de l’authentification HF, vérifie ta clé.")
        sys.exit(1)

test_hf_auth()

# --- Génération de l'article via HuggingFace Inference API ---
def generate_article():
    prompt = (
        "Rédige un article de blog (~500 mots) en français sur une tendance actuelle "
        "en intelligence artificielle, avec un titre accrocheur et une conclusion."
    )
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": prompt,
        "options": {"wait_for_model": True},
        "parameters": {
            "max_new_tokens": 500,
            "temperature": 0.7
        }
    }

    response = requests.post(
        "https://api-inference.huggingface.co/models/bigscience/bloomz",
        headers=headers,
        json=payload,
        timeout=120
    )

    print("Status code HF:", response.status_code)
    print("Response HF:", response.text)

    data = response.json()
    if not isinstance(data, list) or "generated_text" not in data[0]:
        raise ValueError("La réponse HF ne contient pas 'generated_text'.")
    return data[0]["generated_text"]

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
        post { title slug }
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
