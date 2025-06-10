import os
import sys
import requests
from datetime import datetime
import json

# --- Récupération et vérification des clés d'API ---
# HUGGINGFACE_API_KEY n'est plus nécessaire pour la génération de texte,
# mais si vous la gardez pour d'autres usages, pas de souci.
# Je la remplace par MISTRAL_API_KEY pour la génération.
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY") # Nouvelle clé pour Mistral AI
HASHNODE_API_KEY = os.getenv("HASHNODE_API_KEY")

if not MISTRAL_API_KEY:
    print("❌ ERREUR : MISTRAL_API_KEY n'est pas défini. Assurez-vous que la variable d'environnement est correctement passée et que vous avez créé une clé API Mistral AI.")
    sys.exit(1)

if not HASHNODE_API_KEY:
    print("❌ ERREUR : HASHNODE_API_KEY n'est pas défini. Assurez-vous que la variable d'environnement est correctement passée.")
    sys.exit(1)

# --- Définit le modèle Mistral AI à utiliser et l'URL de l'API ---
MISTRAL_MODEL_NAME = "mistral-tiny" # Ou "mistral-small" si vous voulez un peu plus de qualité (et un peu plus de coûts)
MISTRAL_API_BASE_URL = "https://api.mistral.ai/v1/chat/completions" # Endpoint pour les chat completions de Mistral

# --- Test d'authentification Mistral AI ---
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
                "content": "Test de connexion."
            }
        ]
    }

    print(f"🔎 Test d'authentification Mistral AI avec modèle '{MISTRAL_MODEL_NAME}' à l'URL: {MISTRAL_API_BASE_URL}")
    try:
        resp = requests.post(MISTRAL_API_BASE_URL, headers=headers, json=payload, timeout=30)
        print(f"Auth test Mistral status: {resp.status_code}")
        print(f"Auth test Mistral response: {resp.text}")

        if resp.status_code == 200:
            print("✅ Authentification Mistral AI réussie et modèle accessible.")
            try:
                response_data = resp.json()
                if "choices" in response_data and response_data["choices"]:
                    print("✅ Réponse du modèle au format attendu (contient 'choices').")
                else:
                    print("⚠️ Réponse du modèle valide mais ne contient pas 'choices' dans le format attendu.")
            except json.JSONDecodeError:
                print("⚠️ Réponse du modèle non JSON valide. Cela pourrait être un problème de serveur Mistral AI.")
        elif resp.status_code == 401:
            print("❌ Échec de l’authentification Mistral AI: 401 Unauthorized. Clé API incorrecte ou permissions insuffisantes.")
            sys.exit(1)
        else:
            print(f"❌ Échec de l’authentification Mistral AI. Statut inattendu: {resp.status_code}, Réponse: {resp.text}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ ERREUR réseau ou connexion lors du test d'authentification Mistral AI : {e}")
        sys.exit(1)

test_mistral_auth()

# --- Génération de l'article via Mistral AI API ---
def generate_article():
    # Prompt pour l'article de blog
    # Mistral-tiny est plus concis, 750 tokens est un bon objectif pour cet article
    article_prompt = (
        "Rédige un article de blog (~750 mots) en français sur une tendance actuelle "
        "en intelligence artificielle, avec un titre accrocheur et une conclusion."
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
        "max_tokens": 750 # Mistral utilise max_tokens au lieu de max_new_tokens
    }

    print(f"\n🚀 Tentative de génération d'article avec le modèle '{MISTRAL_MODEL_NAME}'...")
    try:
        response = requests.post(
            MISTRAL_API_BASE_URL,
            headers=headers,
            json=payload,
            timeout=120 # Timeout de 2 minutes, généralement suffisant pour Mistral Tiny
        )
        response.raise_for_status()

        print("Status code Mistral:", response.status_code)
        print("Response Mistral:", response.text)

        data = response.json()
        
        # Extraction du texte généré selon le format de réponse de l'API chat completions (Mistral)
        if 'choices' in data and data['choices'] and 'message' in data['choices'][0] and 'content' in data['choices'][0]['message']:
            article_content = data['choices'][0]['message']['content'].strip()
            print("DEBUG: Réponse traitée comme Chat Completions API de Mistral AI.")
        else:
            raise ValueError(f"La réponse de Mistral AI ne contient pas le format de chat completions attendu. Réponse complète: {data}")
        
        return article_content
    except requests.exceptions.RequestException as e:
        print(f"❌ ERREUR HTTP lors de la génération de l'article avec Mistral AI : {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ ERREUR de données dans la réponse Mistral AI : {e}")
        sys.exit(1)

# --- Récupération de l'ID de la publication Hashnode ---
HASHNODE_API_URL = "https://gql.hashnode.com/"

def get_publication_id():
    query = """
    query {
      me {
        publications(first: 1) {
          edges {
            node {
              id # <<<<<< MODIFIÉ ICI : _id changé en id
              # handle # Vous pouvez le décommenter pour voir le handle si besoin
              # title # Vous pouvez le décommenter pour voir le titre si besoin
            }
          }
        }
      }
    }
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HASHNODE_API_KEY}"
    }
    print("\n🔎 Récupération de l'ID de publication Hashnode...")
    try:
        resp = requests.post(HASHNODE_API_URL, json={"query": query}, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        
        if 'errors' in data:
            print(f"❌ ERREUR GraphQL de Hashnode lors de la récupération de l'ID de publication : {data['errors']}")
            sys.exit(1)

        # Accédez à la première publication via edges et node
        if not data.get('data') or \
           not data['data'].get('me') or \
           not data['data']['me'].get('publications') or \
           not data['data']['me']['publications'].get('edges') or \
           not data['data']['me']['publications']['edges']:
            raise KeyError("Aucune publication trouvée ou chemin inattendu dans la réponse Hashnode. Vérifiez votre compte ou le schéma de l'API.")
            
        # MODIFIÉ ICI : _id changé en id
        publication_id = data['data']['me']['publications']['edges'][0]['node']['id']
        print(f"✅ ID de publication Hashnode récupéré : {publication_id}")
        return publication_id
    except requests.exceptions.RequestException as e:
        print(f"❌ ERREUR HTTP lors de la récupération de l'ID de publication Hashnode : {e}")
        if 'resp' in locals() and resp is not None:
            print(f"Réponse Hashnode en cas d'erreur HTTP : {resp.text}")
        sys.exit(1)
    except KeyError as e:
        print(f"❌ ERREUR : Impossible de trouver l'ID de publication dans la réponse Hashnode. Détails: {e}, Réponse: {resp.text if 'resp' in locals() else 'Pas de réponse.'}")
        sys.exit(1)

# --- Publication de l'article sur Hashnode ---
def publish_article(content):
    publication_id = get_publication_id()
    title = "Article IA - " + datetime.now().strftime("%d %B %Y - %H:%M")

    # MODIFIÉ ICI : Utiliser 'CreateDraftInput' et 'createDraft'
    mutation = """
    mutation CreateDraft($input: CreateDraftInput!) { # <<<< MODIFIÉ
      createDraft(input: $input) { # <<<< MODIFIÉ
        post {
          id # Assurez-vous que c'est 'id' et non '_id' ici aussi
          title
          slug
          url # Ajouter l'URL pour un message de succès plus informatif
        }
      }
    }
    """
    variables = {
        "input": {
            "title": title,
            "contentMarkdown": content,
            "publicationId": publication_id,
            "tags": [ # <<<< MODIFIÉ ICI : Correction de la syntaxe
                {
                    "_id": "64d3ac20b4110f0001e6aa5b",
                    "name": "Artificial Intelligence"
                }
            ],
            "coverImageOptions": {"enabled": False},
            "isPublished": True # <<<< Ajouté pour publier directement
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HASHNODE_API_KEY}"
    }

    print(f"\n✍️ Tentative de publication de l'article '{title}' sur Hashnode...")
    try:
        resp = requests.post(HASHNODE_API_URL, json={"query": mutation, "variables": variables}, headers=headers)
        resp.raise_for_status()
        print("Publish status:", resp.status_code)
        print("Publish response:", resp.text)
        
        # Parse la réponse pour afficher l'URL du post si possible
        post_url = None
        if 'data' in resp.json() and \
           'createDraft' in resp.json()['data'] and \
           'post' in resp.json()['data']['createDraft'] and \
           'url' in resp.json()['data']['createDraft']['post']:
            post_url = resp.json()['data']['createDraft']['post']['url']
            print(f"✅ Article publié avec succès : {title} à l'URL : {post_url}")
        else:
            print(f"✅ Article publié avec succès (URL non récupérée) : {title}")

    except requests.exceptions.RequestException as e:
        print(f"❌ ERREUR HTTP lors de la publication de l'article sur Hashnode : {e}")
        print(f"Réponse Hashnode en cas d'erreur : {resp.text if 'resp' in locals() else 'Pas de réponse.'}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Une erreur inattendue est survenue lors de la publication : {e}")
        sys.exit(1)