# ✍️ Automatisation de la Publication de Blog avec Mistral AI et Hashnode (Français & Anglais)

Ce dépôt contient les scripts Python et les workflows GitHub Actions nécessaires pour générer et publier automatiquement des articles de blog sur Hashnode, en utilisant l'API de Mistral AI. Le projet est configuré pour gérer deux blogs distincts : un en français et un en anglais, chacun avec son propre workflow et sa propre publication Hashnode.

---

## 🇫🇷 Français

### Introduction

Ce bot est conçu pour automatiser la création et la publication de contenu sur Hashnode. Il utilise l'intelligence artificielle de Mistral AI pour générer des articles de blog originaux et les publie ensuite sur une publication Hashnode spécifique, avec une image de couverture aléatoire provenant du dépôt.

### Fonctionnalités

* **Génération d'articles par IA :** Utilise l'API de Mistral AI pour créer des articles de blog détaillés et optimisés pour le SEO.
* **Publication automatisée sur Hashnode :** Publie les articles générés sur votre blog Hashnode.
* **Gestion des images de couverture :** Sélectionne une image de couverture aléatoire parmi celles présentes dans le dossier `covers/` de votre dépôt GitHub.
* **Support multilingue :** Séparation des workflows pour des blogs français et anglais.
* **Déclenchement quotidien via GitHub Actions :** Les articles sont générés et publiés automatiquement chaque jour à des heures définies.

### Prérequis

Avant de commencer, assurez-vous d'avoir les éléments suivants :

1.  **Un compte Hashnode** avec au moins deux publications (une pour le français, une pour l'anglais).
2.  **Une clé API Mistral AI.**
3.  **Une clé API Hashnode.**
4.  **Un dépôt GitHub** pour héberger ce code.
5.  Un dossier `covers/` à la racine de votre dépôt contenant des images (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`) pour vos articles.

### Configuration

#### 1. Variables d'environnement / Secrets GitHub

Ajoutez les secrets suivants à votre dépôt GitHub (onglet `Settings` > `Secrets and variables` > `Actions` > `New repository secret`):

* `MISTRAL_API_KEY`: Votre clé API pour Mistral AI.
* `HASHNODE_API_KEY`: Votre clé API pour Hashnode.

#### 2. Préparation des publications Hashnode

* **Blog Français :** Le script français (`hashnode_bot.py`) est configuré pour trouver la première publication associée à votre compte Hashnode. Assurez-vous que c'est celle que vous souhaitez utiliser pour les articles en français.
* **Blog Anglais :**
    1.  Créez une **nouvelle publication Hashnode dédiée** à votre blog anglais.
    2.  Accédez au tableau de bord de cette nouvelle publication. L'URL ressemblera à `https://hashnode.com/<VOTRE_PUBLICATION_ID_ICI>/dashboard`.
    3.  Copiez la longue chaîne alphanumérique (votre ID de publication anglaise) depuis cette URL.
    4.  Dans le fichier `english_hashnode_bot.py`, remplacez `"PASTE_YOUR_ACTUAL_ENGLISH_PUBLICATION_ID_HERE"` par cet ID.

#### 3. Fichiers Python

* `hashnode_bot.py`: Script principal pour la génération et la publication d'articles **en français**.
* `english_hashnode_bot.py`: Script principal pour la génération et la publication d'articles **en anglais**.
    * **N'oubliez pas de mettre à jour la variable `ENGLISH_HASHNODE_PUBLICATION_ID` dans ce fichier !**

#### 4. Dossier des images de couverture

Créez un dossier nommé `covers` à la racine de votre dépôt. Placez-y toutes les images que vous souhaitez utiliser comme couvertures d'articles. Le bot sélectionnera une image aléatoirement à chaque exécution.

#### 5. Dépendances Python

Créez un fichier `requirements.txt` à la racine de votre dépôt avec le contenu suivant :

```
requests
```

### Exécution (via GitHub Actions)

Ce projet est conçu pour être exécuté automatiquement via GitHub Actions. Deux workflows sont configurés :

* `.github/workflows/daily_french_blog.yml`: Déclenche la publication d'un article français quotidiennement (par défaut à minuit UTC).
* `.github/workflows/daily_english_blog.yml`: Déclenche la publication d'un article anglais quotidiennement (par défaut à 1h du matin UTC).

Vous pouvez également déclencher ces workflows manuellement via l'onglet "Actions" de votre dépôt GitHub en sélectionnant le workflow et en cliquant sur "Run workflow".

### Structure du Dépôt

```
.
├── .github/
│   └── workflows/
│       ├── daily_french_blog.yml
│       └── daily_english_blog.yml
├── covers/
│   ├── image1.png
│   ├── image2.jpg
│   └── ...
├── hashnode_bot.py
├── english_hashnode_bot.py
└── requirements.txt
└── README.md
```

### Contribuer

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir des "issues" pour des suggestions ou des "pull requests" pour des améliorations.

### Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

## 🇬🇧 English

### Introduction

This repository contains the Python scripts and GitHub Actions workflows required to automatically generate and publish blog posts on Hashnode, using the Mistral AI API. The project is set up to manage two distinct blogs: one in French and one in English, each with its own workflow and Hashnode publication.

### Features

* **AI Article Generation:** Uses the Mistral AI API to create detailed and SEO-optimized blog posts.
* **Automated Hashnode Publishing:** Publishes generated articles to your specific Hashnode blog.
* **Cover Image Management:** Selects a random cover image from the `covers/` directory in your GitHub repository.
* **Multilingual Support:** Separate workflows for French and English blogs.
* **Daily Trigger via GitHub Actions:** Articles are generated and published automatically daily at defined times.

### Prerequisites

Before you begin, ensure you have the following:

1.  **A Hashnode account** with at least two publications (one for French, one for English).
2.  **A Mistral AI API Key.**
3.  **A Hashnode API Key.**
4.  **A GitHub repository** to host this code.
5.  A `covers/` folder at the root of your repository containing images (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`) for your articles.

### Setup

#### 1. Environment Variables / GitHub Secrets

Add the following secrets to your GitHub repository (go to `Settings` tab > `Secrets and variables` > `Actions` > `New repository secret`):

* `MISTRAL_API_KEY`: Your Mistral AI API key.
* `HASHNODE_API_KEY`: Your Hashnode API key.

#### 2. Hashnode Publication Preparation

* **French Blog:** The French script (`hashnode_bot.py`) is configured to find the first publication associated with your Hashnode account. Ensure this is the one you intend to use for French articles.
* **English Blog:**
    1.  Create a **new, dedicated Hashnode publication** for your English blog.
    2.  Go to the dashboard of this new publication. The URL will look like `https://hashnode.com/<YOUR_PUBLICATION_ID_HERE>/dashboard`.
    3.  Copy the long alphanumeric string (your English publication ID) from this URL.
    4.  In the `english_hashnode_bot.py` file, replace `"PASTE_YOUR_ACTUAL_ENGLISH_PUBLICATION_ID_HERE"` with this ID.

#### 3. Python Files

* `hashnode_bot.py`: Main script for generating and publishing articles **in French**.
* `english_hashnode_bot.py`: Main script for generating and publishing articles **in English**.
    * **Don't forget to update the `ENGLISH_HASHNODE_PUBLICATION_ID` variable in this file!**

#### 4. Cover Images Folder

Create a folder named `covers` at the root of your repository. Place all images you wish to use as article covers there. The bot will randomly select an image for each run.

#### 5. Python Dependencies

Create a `requirements.txt` file at the root of your repository with the following content:

```
requests
```

### Execution (via GitHub Actions)

This project is designed for automatic execution via GitHub Actions. Two workflows are configured:

* `.github/workflows/daily_french_blog.yml`: Triggers the publication of a French article daily (default at midnight UTC).
* `.github/workflows/daily_english_blog.yml`: Triggers the publication of an English article daily (default at 1 AM UTC).

You can also manually trigger these workflows via the "Actions" tab in your GitHub repository by selecting the workflow and clicking "Run workflow".

### Repository Structure

```
.
├── .github/
│   └── workflows/
│       ├── daily_french_blog.yml
│       └── daily_english_blog.yml
├── covers/
│   ├── image1.png
│   ├── image2.jpg
│   └── ...
├── hashnode_bot.py
├── english_hashnode_bot.py
└── requirements.txt
└── README.md
```

### Contributing

Contributions are welcome! Feel free to open issues for suggestions or pull requests for improvements.

### License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
```
