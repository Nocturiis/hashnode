import os
import sys
import requests
from datetime import datetime
import json

# --- Récupération et vérification des clés d'API ---
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HASHNODE_API_KEY = os.getenv("HASHNODE_API_KEY")

if not HUGGINGFACE_API_KEY:
    print("❌ ERREUR : HUGGINGFACE_API_KEY n'est pas défini. Assurez-vous que la variable d'environnement est correctement passée.")
    sys.exit(1)

if not HASHNODE_API_KEY:
    print("❌ ERREUR : HASHNODE_API_KEY n'est pas défini. Assurez-vous que la variable d'environnement est correctement passée.")
    sys.exit(1)

# --- Définit le modèle HF à utiliser et l'URL de l'API ---
# Changement du modèle vers un modèle de génération de texte plus petit et plus fiable.
HF_MODEL_NAME = "distilbert/distilgpt2"
HF_API_INFERENCE_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL_NAME}"


# --- Test d'authentification Hugging Face ---
def test_hf_auth():
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    # Requête de test simple pour un modèle de génération de texte
    payload = {"inputs": "Bonjour"}

    print(f"🔎 Test d'authentification HF avec modèle '{HF_MODEL_NAME}' à l'URL: {HF_API_INFERENCE_URL}")
    try:
        resp = requests.post(HF_API_INFERENCE_URL, headers=headers, json=payload, timeout=30) # Timeout plus court car plus rapide
        print(f"Auth test HF status: {resp.status_code}")
        print(f"Auth test HF response: {resp.text}")

        # Les codes 200 (OK) ou 503 (Service Indisponible - chargement du modèle) sont acceptables
        if resp.status_code == 200 or resp.status_code == 503:
            print("✅ Authentification Hugging Face réussie et modèle accessible (ou en cours de chargement).")
            try:
                response_data = resp.json()
                if isinstance(response_data, list) and response_data and "generated_text" in response_data[0]:
                    print("✅ Réponse du modèle au format attendu (contient 'generated_text').")
                else:
                    print("⚠️ Réponse du modèle valide mais ne contient pas 'generated_text' dans le format attendu.")
            except json.JSONDecodeError:
                print("⚠️ Réponse du modèle non JSON valide. Cela pourrait être un problème de serveur.")
        elif resp.status_code == 401:
            print("❌ Échec de l’authentification HF: 401 Unauthorized. Clé API incorrecte ou permissions insuffisantes.")
            sys.exit(1)
        elif resp.status_code == 404:
            print(f"❌ Échec de l’authentification HF: 404 Not Found. Le modèle '{HF_MODEL_NAME}' n'est pas déployé publiquement ou l'URL est incorrecte.")
            print("Vérifiez la disponibilité de ce modèle sur l'API d'inférence gratuite.")
            sys.exit(1)
        else:
            print(f"❌ Échec de l’authentification HF. Statut inattendu: {resp.status_code}, Réponse: {resp.text}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ ERREUR réseau ou connexion lors du test d'authentification HF : {e}")
        sys.exit(1)

test_hf_auth()

# --- Génération de l'article via HuggingFace Inference API ---
def generate_article():
    # Prompt pour l'article de blog
    prompt = (
        "Rédige un article de blog (~750 mots) en français sur une tendance actuelle "
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
            "max_new_tokens": 750, # Gardons 750 tokens pour un bon équilibre qualité/fiabilité
            "temperature": 0.7
        }
    }

    print(f"\n🚀 Tentative de génération d'article avec le modèle '{HF_MODEL_NAME}'...")
    try:
        response = requests.post(
            HF_API_INFERENCE_URL,
            headers=headers,
            json=payload,
            timeout=300 # Retour à un timeout plus court, car ce modèle est plus rapide
        )
        response.raise_for_status()

        print("Status code HF:", response.status_code)
        print("Response HF:", response.text)

        data = response.json()
        
        # Le format de réponse pour distilgpt2 est une liste de dictionnaires avec 'generated_text'
        if not isinstance(data, list) or not data or "generated_text" not in data[0]:
            raise ValueError(f"La réponse HF ne contient pas 'generated_text'. Réponse complète: {data}")
        
        generated_full_text = data[0]["generated_text"]
        # Distilgpt2 renvoie le prompt inclus, nous devons le retirer
        if generated_full_text.startswith(prompt):
            article_content = generated_full_text[len(prompt):].strip()
        else:
            article_content = generated_full_text # Au cas où, on prend tout
            
        return article_content
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

        publication_id = data['data']['me']['publication']['_id']
        print(f"✅ ID de publication Hashnode récupéré : {publication_id}")
        return publication_id
    except requests.exceptions.RequestException as e:
        print(f"❌ ERREUR HTTP lors de la récupération de l'ID de publication Hashnode : {e}")
        if 'resp' in locals() and resp is not None:
            print(f"Réponse Hashnode en cas d'erreur HTTP : {resp.text}")
        sys.exit(1)
    except KeyError as e:
        print(f"❌ ERREUR : Impossible de trouver l'ID de publication dans la réponse Hashnode. Vérifiez votre clé ou les permissions. Détails: {e}, Réponse: {resp.text if 'resp' in locals() else 'Pas de réponse.'}")
        sys.exit(1)


# --- Publication de l'article sur Hashnode ---
def publish_article(content):
    publication_id = get_publication_id()
    title = "Article IA - " + datetime.now().strftime("%d %B %Y - %H:%M")

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
        "Authorization": f"Bearer {HASHNODE_API_KEY}"
    }

    print(f"\n✍️ Tentative de publication de l'article '{title}' sur Hashnode...")
    try:
        resp = requests.post(HASHNODE_API_URL, json={"query": mutation, "variables": variables}, headers=headers)
        resp.raise_for_status()
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