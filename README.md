# 🚀 ViralPost AI

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**ViralPost AI** est une application web intelligente qui génère automatiquement des posts optimisés SEO pour les réseaux sociaux (LinkedIn, Instagram, Facebook) en utilisant l'intelligence artificielle. Créez du contenu viral, engageant et personnalisé en quelques clics !

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Utilisation](#-utilisation)
- [Structure du projet](#-structure-du-projet)
- [Technologies utilisées](#-technologies-utilisées)
- [Moteurs IA supportés](#-moteurs-ia-supportés)
- [Dépannage](#-dépannage)
- [Contribution](#-contribution)
- [Licence](#-licence)

## ✨ Fonctionnalités

### 🎯 Génération de contenu
- **Multi-plateformes** : Créez des posts optimisés pour LinkedIn, Instagram et Facebook
- **Personnalisation avancée** : Choisissez le ton (professionnel, humoristique, provocateur) et définissez votre audience cible
- **Optimisation SEO** : Posts générés avec structure AIDA, hashtags pertinents et contenu riche (250-300 mots)
- **Emojis intégrés** : Contenu visuellement attractif avec emojis stratégiquement placés

### 🤖 Moteurs IA multiples
- **Ollama (Local)** : Traitement local gratuit avec modèles open-source (Llama, Mistral, Phi3, etc.)
- **Mistral AI** : API gratuite pour des résultats rapides et efficaces
- **Google AI Studio (Gemini)** : Modèles avancés pour une qualité maximale

### 💾 Gestion de l'historique
- Base de données SQLite intégrée pour sauvegarder tous vos posts
- Historique accessible depuis l'interface
- Fonction de copie rapide dans le presse-papier

### 🖥️ Interface utilisateur
- Interface moderne et intuitive avec Streamlit
- Mode desktop avec fenêtre native (pywebview)
- Boutons de régénération pour créer des variantes
- Design responsive et accessible

## 📦 Prérequis

### Obligatoire
- **Python 3.8+** : [Télécharger Python](https://www.python.org/downloads/)
- **Pip** : Généralement inclus avec Python

### Optionnel (selon le moteur IA choisi)
- **Ollama** : Pour l'utilisation locale (recommandé pour la confidentialité)
  - Installation : [https://ollama.ai](https://ollama.ai)
  - Modèles recommandés : `llama3`, `mistral`, `phi3`
- **Clé API Mistral AI** : Pour utiliser Mistral AI (gratuit)
  - Obtenir une clé : [https://console.mistral.ai/api-keys/](https://console.mistral.ai/api-keys/)
- **Clé API Google AI Studio** : Pour utiliser Gemini
  - Obtenir une clé : [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

## 🚀 Installation

### 1. Cloner le repository

```bash
git clone https://github.com/votre-username/viralpost-ai.git
cd viralpost-ai
```

### 2. Créer un environnement virtuel (recommandé)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Installer Ollama (optionnel mais recommandé)

Si vous souhaitez utiliser Ollama en local :

1. Téléchargez et installez Ollama : [https://ollama.ai](https://ollama.ai)
2. Téléchargez un modèle :
   ```bash
   ollama pull llama3
   # ou
   ollama pull mistral
   # ou
   ollama pull phi3
   ```

## ⚙️ Configuration

### 1. Créer le fichier `.env`

Copiez le fichier d'exemple :

```bash
# Windows
copy env.example.txt .env

# Linux/Mac
cp env.example.txt .env
```

### 2. Configurer vos clés API (optionnel)

Ouvrez le fichier `.env` et ajoutez vos clés API :

```env
# Google AI Studio (Gemini) - Optionnel
GOOGLE_AI_API_KEY=votre_cle_google_ai_ici

# Mistral AI - Optionnel (gratuit)
MISTRAL_API_KEY=votre_cle_mistral_ai_ici

# Ollama Configuration - Optionnel (par défaut: localhost:11434)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3
```

**⚠️ Important** : Ne commitez jamais votre fichier `.env` sur GitHub ! Il est déjà dans `.gitignore`.

### 3. Vérifier qu'Ollama est en cours d'exécution (si utilisé)

Si vous utilisez Ollama, assurez-vous qu'il est démarré :

```bash
ollama serve
```

## 💻 Utilisation

### Mode Web (Navigateur)

Lancez l'application Streamlit :

```bash
streamlit run app.py
```

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse `http://localhost:8501`

### Mode Desktop (Fenêtre native)

#### Windows
Double-cliquez sur `launch_desktop.bat` ou exécutez :

```bash
python launch_desktop.py
```

#### Linux/Mac
```bash
chmod +x launch_desktop.sh
./launch_desktop.sh
```

ou

```bash
python launch_desktop.py
```

### Guide d'utilisation

1. **Configurez le moteur IA** : Dans la barre latérale, choisissez entre Ollama, Mistral AI ou Google AI Studio
2. **Sélectionnez un modèle** : Si vous utilisez Ollama, choisissez le modèle installé
3. **Définissez les paramètres du post** :
   - **Sujet** : Le thème principal de votre post
   - **Ton** : Professionnel, humoristique ou provocateur
   - **Audience cible** : Votre public cible (ex: "Entrepreneurs", "Professionnels du marketing")
4. **Générez le post** : Cliquez sur l'onglet du réseau social souhaité (LinkedIn, Instagram, Facebook) puis sur "Générer le post"
5. **Copiez ou régénérez** : Utilisez le bouton de copie ou régénérez pour créer des variantes
6. **Consultez l'historique** : Cliquez sur "Voir l'historique" dans la barre latérale

## 📁 Structure du projet

```
viralpost-ai/
│
├── app.py                 # Application principale Streamlit
├── launch_desktop.py      # Script de lancement mode desktop
├── launch_desktop.bat     # Script batch Windows
├── launch_desktop.sh      # Script shell Linux/Mac
│
├── requirements.txt       # Dépendances Python
├── env.example.txt        # Exemple de configuration (.env)
├── .gitignore            # Fichiers ignorés par Git
│
├── README.md             # Ce fichier
│
├── viralpost_history.db  # Base de données SQLite (généré automatiquement)
└── generated_images/     # Images générées (si applicable)
```

## 🛠️ Technologies utilisées

- **Streamlit** : Framework web pour l'interface utilisateur
- **Ollama** : Infrastructure pour exécuter des modèles LLM en local
- **Python** : Langage de programmation principal
- **SQLite** : Base de données pour l'historique
- **Pandas** : Manipulation de données
- **python-dotenv** : Gestion des variables d'environnement
- **Mistral AI** : API d'IA (optionnelle)
- **Google Generative AI** : API Gemini (optionnelle)
- **pywebview** : Fenêtres natives pour le mode desktop

## 🤖 Moteurs IA supportés

### Ollama (Recommandé pour débuter)
- ✅ **Gratuit** et local (données privées)
- ✅ Aucune clé API requise
- ✅ Modèles open-source (Llama, Mistral, Phi3, etc.)
- ⚠️ Nécessite l'installation d'Ollama et d'un modèle
- 📦 **Installation** :
  ```bash
  # Installer Ollama depuis https://ollama.ai
  # Puis télécharger un modèle :
  ollama pull llama3
  ```

### Mistral AI (Gratuit)
- ✅ **Gratuit** avec clé API
- ✅ Rapide et efficace
- ✅ Pas d'installation locale requise
- ⚠️ Nécessite une clé API (gratuite)
- 🔑 **Obtenir une clé** : [https://console.mistral.ai/api-keys/](https://console.mistral.ai/api-keys/)

### Google AI Studio - Gemini
- ✅ Modèles très performants
- ✅ Qualité de génération élevée
- ⚠️ Nécessite une clé API
- ⚠️ Peut avoir des limitations de quota
- 🔑 **Obtenir une clé** : [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

## 🔧 Dépannage

### Problème : Ollama n'est pas détecté

**Solution** :
1. Vérifiez qu'Ollama est installé : `ollama --version`
2. Démarrez Ollama : `ollama serve`
3. Vérifiez qu'un modèle est installé : `ollama list`
4. Installez un modèle si nécessaire : `ollama pull llama3`

### Problème : Erreur de clé API

**Solution** :
1. Vérifiez que le fichier `.env` existe dans le répertoire racine
2. Vérifiez que la clé API est correctement formatée (sans espaces, sans guillemets)
3. Vérifiez que la clé API est valide et non expirée

### Problème : Streamlit ne démarre pas

**Solution** :
1. Vérifiez que toutes les dépendances sont installées : `pip install -r requirements.txt`
2. Vérifiez que Python 3.8+ est installé : `python --version`
3. Essayez de réinstaller Streamlit : `pip install --upgrade streamlit`

### Problème : Erreur de base de données

**Solution** :
- L'application créera automatiquement la base de données si elle n'existe pas
- Vérifiez les permissions d'écriture dans le répertoire du projet

### Problème : Mode desktop ne fonctionne pas

**Solution** :
1. Installez pywebview : `pip install pywebview`
2. Sur Linux, vous pourriez avoir besoin d'installer des dépendances système :
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-dev python3-gi python3-gi-cairo gir1.2-gtk-3.0
   
   # Fedora
   sudo dnf install python3-devel cairo-gobject-devel gobject-introspection-devel
   ```
3. Si pywebview ne fonctionne pas, utilisez le mode web standard avec `streamlit run app.py`

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. **Fork** le projet
2. Créez une **branche** pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. **Commit** vos changements (`git commit -m 'Add some AmazingFeature'`)
4. **Push** vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une **Pull Request**

### Idées de contributions
- Ajouter support pour d'autres réseaux sociaux (Twitter/X, TikTok, etc.)
- Améliorer les prompts de génération
- Ajouter des fonctionnalités d'export (PDF, Word, etc.)
- Améliorer l'interface utilisateur
- Ajouter des statistiques sur les posts générés
- Traduction dans d'autres langues

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🙏 Remerciements

- [Streamlit](https://streamlit.io/) pour le framework web
- [Ollama](https://ollama.ai/) pour l'infrastructure LLM locale
- [Mistral AI](https://mistral.ai/) pour l'API gratuite
- [Google AI](https://ai.google.dev/) pour Gemini

## 📧 Contact

Pour toute question ou suggestion, n'hésitez pas à ouvrir une [issue](https://github.com/votre-username/viralpost-ai/issues) sur GitHub.

---

**Fait avec ❤️ pour faciliter la création de contenu sur les réseaux sociaux**
