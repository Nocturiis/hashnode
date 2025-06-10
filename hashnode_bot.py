import os
import sys
import requests
from datetime import datetime
import json
import random

# --- Récupération et vérification des clés d'API ---
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
HASHNODE_API_KEY = os.getenv("HASHNODE_API_KEY")

if not MISTRAL_API_KEY:
    print("❌ ERREUR : MISTRAL_API_KEY n'est pas défini. Assurez-vous que la variable d'environnement est correctement passée et que vous avez créé une clé API Mistral AI.")
    sys.exit(1)

if not HASHNODE_API_KEY:
    print("❌ ERREUR : HASHNODE_API_KEY n'est pas défini. Assurez-vous que la variable d'environnement est correctement passée.")
    sys.exit(1)

# --- Définit le modèle Mistral AI à utiliser et l'URL de l'API ---
MISTRAL_MODEL_NAME = "mistral-tiny"
MISTRAL_API_BASE_URL = "https://api.mistral.ai/v1/chat/completions"

# --- Configuration Hashnode ---
HASHNODE_API_URL = "https://gql.hashnode.com/"

# --- MODIFIÉ ICI : Variables pour l'URL de base du dépôt GitHub ---
# Ces variables sont automatiquement fournies par GitHub Actions
GITHUB_REPOSITORY = os.getenv('GITHUB_REPOSITORY') # Format: 'user/repo'
GITHUB_REF = os.getenv('GITHUB_REF') # Format: 'refs/heads/main' ou 'refs/heads/master'
# Extraire le nom d'utilisateur et le nom du dépôt
if GITHUB_REPOSITORY:
    GITHUB_USERNAME = GITHUB_REPOSITORY.split('/')[0]
    GITHUB_REPO_NAME = GITHUB_REPOSITORY.split('/')[1]
else:
    GITHUB_USERNAME = "votre_utilisateur" # Fallback si pas en environnement GH Actions
    GITHUB_REPO_NAME = "votre_repo"      # Fallback
    print("⚠️ Variables GITHUB_REPOSITORY non trouvées. Utilisation de valeurs par défaut. Assurez-vous que le script s'exécute dans un environnement GitHub Actions.")

# Extraire le nom de la branche
if GITHUB_REF and GITHUB_REF.startswith('refs/heads/'):
    GITHUB_BRANCH = GITHUB_REF.split('/')[-1]
else:
    GITHUB_BRANCH = "main" # Fallback, généralement 'main' ou 'master'

# Le dossier où se trouvent vos images de couverture dans le dépôt
COVER_IMAGES_DIR = "covers" # Assurez-vous que c'est le bon chemin !

# --- Fonctions Utilitaires ---

def get_github_raw_base_url():
    """Construit l'URL de base pour les fichiers bruts de votre dépôt GitHub."""
    return f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO_NAME}/{GITHUB_BRANCH}"

def get_random_cover_image_url():
    """
    Liste les images dans le répertoire spécifié et retourne l'URL raw d'une image aléatoire.
    """
    image_files = []
    # Chemin absolu vers le dossier covers dans l'environnement d'exécution de l'action
    # GITHUB_WORKSPACE est le chemin par défaut du dépôt cloné par GitHub Actions
    covers_path = os.path.join(os.getenv('GITHUB_WORKSPACE', '.'), COVER_IMAGES_DIR)

    if not os.path.exists(covers_path):
        print(f"❌ ERREUR : Le dossier des images de couverture '{covers_path}' n'existe pas. Veuillez le créer ou vérifier le chemin.")
        return None

    try:
        # Lister tous les fichiers dans le dossier covers
        for filename in os.listdir(covers_path):
            # Vérifier si c'est un fichier image (extensions courantes)
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                image_files.append(filename)
        
        if not image_files:
            print(f"⚠️ Aucun fichier image trouvé dans le dossier '{covers_path}'.")
            return None
        
        # Sélectionner un fichier aléatoirement
        selected_file = random.choice(image_files)
        
        # Construire l'URL raw complète
        base_url = get_github_raw_base_url()
        full_image_url = f"{base_url}/{COVER_IMAGES_DIR}/{selected_file}"
        print(f"✅ Image de couverture sélectionnée : {selected_file}")
        return full_image_url

    except Exception as e:
        print(f"❌ ERREUR lors de la lecture des fichiers d'images de couverture : {e}")
        return None

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
    article_prompt = (
        "Rédige un article de blog professionnel et détaillé d'au moins 1500 mots en français sur un sujet (d'actualité si possible) "
        "qui concerne l'informatique dans sa globalité. "
        "Le titre doit être inclus au début du contenu de l'article (premier niveau de titre, ex: # Titre de l'Article). "
        "Ne commence pas l'article par 'Titre : ' ou 'Auteur : ' ou 'Date de publication : '. "
        "L'article doit se terminer par la signature 'Par Nathan Remacle.'. "
        "Optimise le contenu pour le SEO en incluant des mots-clés pertinents de manière naturelle. "
        "Évite les formulations qui sonnent 'IA' et adopte un ton humain et engageant."
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

    print(f"\n🚀 Tentative de génération d'article avec le modèle '{MISTRAL_MODEL_NAME}'...")
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
              id
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

        if not data.get('data') or \
           not data['data'].get('me') or \
           not data['data']['me'].get('publications') or \
           not data['data']['me']['publications'].get('edges') or \
           not data['data']['me']['publications']['edges']:
            raise KeyError("Aucune publication trouvée ou chemin inattendu dans la réponse Hashnode. Vérifiez votre compte ou le schéma de l'API.")
            
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
    
    first_line_match = content.split('\n')[0].strip()
    extracted_title = ""
    if first_line_match.startswith('# '):
        extracted_title = first_line_match[2:].strip()
        content = content[len(first_line_match):].strip() # Supprime le titre du contenu
    else:
        extracted_title = "Article du " + datetime.now().strftime("%d %B %Y - %H:%M")

    # --- MODIFIÉ ICI : Appel de la nouvelle fonction pour obtenir l'URL de l'image ---
    selected_cover_url = get_random_cover_image_url()

    # Assurez-vous que la signature est présente
    if "Par Nathan Remacle." not in content:
        content += "\n\nPar Nathan Remacle."

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
    
    # Ajouter l'URL de l'image de couverture si une a été sélectionnée
    if selected_cover_url:
        variables["input"]["coverImageOptions"] = {
            "coverImageURL": selected_cover_url,
            "isCoverImageAttributionRequired": False # Mettez True si vous ajoutez une attribution manuelle
        }
        print(f"DEBUG: Image de couverture Hashnode ajoutée aux variables: {selected_cover_url}")
    else:
        print("DEBUG: Pas d'image de couverture ajoutée (aucune URL configurée ou liste vide).")


    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HASHNODE_API_KEY}"
    }

    print(f"\n✍️ Tentative de publication de l'article '{extracted_title}' sur Hashnode...")
    print(f"DEBUG: Payload JSON envoyé à Hashnode (sans le contenu détaillé): {json.dumps(variables, indent=2)}")
    print(f"DEBUG: Début du contenu Markdown envoyé: {content[:200]}...")

    try:
        resp = requests.post(HASHNODE_API_URL, json={"query": mutation, "variables": variables}, headers=headers)
        
        print("Publish status:", resp.status_code)
        print("Publish response:", resp.text)
        
        response_data = resp.json()

        if 'errors' in response_data and response_data['errors']:
            print(f"❌ ERREUR GraphQL de Hashnode lors de la publication de l'article : {response_data['errors']}")
            sys.exit(1)

        post_url = None
        if 'data' in response_data and \
           'publishPost' in response_data['data'] and \
           'post' in response_data['data']['publishPost'] and \
           'url' in response_data['data']['publishPost']['post']:
            post_url = response_data['data']['publishPost']['post']['url']
            print(f"✅ Article publié avec succès : {extracted_title} à l'URL : {post_url}")
        else:
            print(f"✅ Article publié avec succès (URL non récupérée) : {extracted_title}")

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