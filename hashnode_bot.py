import os
import sys
import requests
from datetime import datetime

# --- Récupération et vérification des clés d'API ---
# CORRECTION ICI : os.getenv() doit prendre le NOM de la variable d'environnement
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HASHNODE_API_KEY = os.getenv("HASHNODE_API_KEY") # J'ai aussi corrigé un espace étrange ici

if not HUGGINGFACE_API_KEY:
    print("❌ ERREUR : HUGGINGFACE_API_KEY n'est pas défini. Assurez-vous que la variable d'environnement est correctement passée.")
    sys.exit(1)

if not HASHNODE_API_KEY:
    print("❌ ERREUR : HASHNODE_API_KEY n'est pas défini. Assurez-vous que la variable d'environnement est correctement passée.")
    sys.exit(1)

# --- Test d'authentification Hugging Face ---
def test_hf_auth():
    # Ici, la clé est utilisée directement à partir de la variable globale, c'est correct
    resp = requests.get(
        "https://api-inference.huggingface.co/models/bigscience/bloomz",
        headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    )
    print("🔎 Auth test HF status:", resp.status_code)
    # 503 est un code attendu pour les modèles qui se chargent (cold start)
    if resp.status_code not in (200, 503):
        print(f"❌ Échec de l’authentification HF. Statut: {resp.status_code}, Réponse: {resp.text}")
        sys.exit(1)
    else:
        print("✅ Authentification Hugging Face réussie ou modèle en chargement.")

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

    print("\n🚀 Tentative de génération d'article avec le modèle Bloomz...")
    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/bigscience/bloomz",
            headers=headers,
            json=payload,
            timeout=300 # Augmenter le timeout pour Bloomz, car il peut être lent à charger
        )
        response.raise_for_status() # Lève une exception pour les codes d'erreur HTTP

        print("Status code HF:", response.status_code)
        print("Response HF:", response.text)

        data = response.json()
        if not isinstance(data, list) or not data or "generated_text" not in data[0]:
            raise ValueError(f"La réponse HF ne contient pas 'generated_text'. Réponse complète: {data}")
        return data[0]["generated_text"]
    except requests.exceptions.RequestException as e:
        print(f"❌ ERREUR HTTP lors de la génération de l'article : {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ ERREUR de données dans la réponse HF : {e}")
        sys.exit(1)

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
        "Authorization": HASHNODE_API_KEY # C'est correct d'utiliser la variable ici
    }
    print("\n🔎 Récupération de l'ID de publication Hashnode...")
    try:
        resp = requests.post(HASHNODE_API_URL, json={"query": query}, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        publication_id = data['data']['me']['publication']['_id']
        print(f"✅ ID de publication Hashnode récupéré : {publication_id}")
        return publication_id
    except requests.exceptions.RequestException as e:
        print(f"❌ ERREUR HTTP lors de la récupération de l'ID de publication Hashnode : {e}")
        sys.exit(1)
    except KeyError as e:
        print(f"❌ ERREUR : Impossible de trouver l'ID de publication dans la réponse Hashnode. Vérifiez votre clé ou les permissions. Détails: {e}, Réponse: {resp.text}")
        sys.exit(1)


# --- Publication de l'article sur Hashnode ---
def publish_article(content):
    publication_id = get_publication_id()
    title = "Article IA - " + datetime.now().strftime("%d %B %Y - %H:%M") # Ajout de l'heure pour l'unicité

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

    print(f"\n✍️ Tentative de publication de l'article '{title}' sur Hashnode...")
    try:
        resp = requests.post(HASHNODE_API_URL, json={"query": mutation, "variables": variables}, headers=headers)
        resp.raise_for_status() # Lève une exception pour les codes d'erreur HTTP
        print("Publish status:", resp.status_code)
        print("Publish response:", resp.text)
        print(f"✅ Article publié avec succès : {title}")
    except requests.exceptions.RequestException as e:
        print(f"❌ ERREUR HTTP lors de la publication de l'article sur Hashnode : {e}")
        print(f"Réponse Hashnode en cas d'erreur : {resp.text if 'resp' in locals() else 'Pas de réponse.'}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Une erreur inattendue est survenue lors de la publication : {e}")
        sys.exit(1)

# --- Exécution principale ---
if __name__ == "__main__":
    print("Démarrage du bot Hashnode.")
    try:
        article = generate_article()
        publish_article(article)
        print("\n🎉 Bot Hashnode terminé avec succès !")
    except Exception as e:
        print(f"\nFATAL ERROR: Une erreur critique est survenue : {e}")
        sys.exit(1)