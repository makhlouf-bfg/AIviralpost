import streamlit as st
import ollama
import sqlite3
import pandas as pd
from datetime import datetime
import json
import subprocess
import base64
import os
import hashlib


# Chargement des variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    # Charger .env en UTF-8 explicitement pour éviter les problèmes sur Windows
    try:
        load_dotenv(encoding='utf-8')
        ENV_LOADED = True
    except Exception as e:
        # Si erreur de chargement, continuer sans .env (peut utiliser variables système)
        ENV_LOADED = False
        print(f"⚠️ Erreur lors du chargement du fichier .env: {e}")
        print("   L'application continuera sans fichier .env (variables système uniquement)")
except ImportError:
    ENV_LOADED = False
    print("⚠️ python-dotenv non installé. Installez-le avec: pip install python-dotenv")

# Hash du mot de passe (pour protéger les clés API du .env)
# Hash SHA256 du mot de passe : cacher dans une variable non évidente
_PASS_HASH = hashlib.sha256(b'Maklyesbfg2006@!').hexdigest()

def check_password(password):
    """Vérifie si le mot de passe est correct"""
    if not password:
        return False
    # Vérifier le hash
    return hashlib.sha256(password.encode('utf-8')).hexdigest() == _PASS_HASH

# Configuration Google AI Studio (Gemini) et Mistral AI
# Priorité : variables d'environnement (.env ou Streamlit Cloud Secrets injectés en env)
# puis st.secrets (Streamlit Community Cloud)
def _get_env_or_secret(key):
    v = os.getenv(key)
    if v:
        return v
    try:
        return st.secrets.get(key)
    except Exception:
        return None

_GOOGLE_AI_API_KEY_ENV = _get_env_or_secret("GOOGLE_AI_API_KEY")
_MISTRAL_API_KEY_ENV = _get_env_or_secret("MISTRAL_API_KEY")

# Configuration de la page
st.set_page_config(
    page_title="ViralPost AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS personnalisés
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1DA1F2;
        text-align: center;
        margin-bottom: 2rem;
    }
    .post-container {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1DA1F2;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1DA1F2;
        color: white;
        font-weight: bold;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #0d8bd9;
    }
    </style>
""", unsafe_allow_html=True)

# Initialisation de la base de données avec cache Streamlit
@st.cache_resource
def init_database():
    """
    Initialise la connexion SQLite avec support multi-thread pour Streamlit.
    Utilise @st.cache_resource pour éviter de créer plusieurs connexions.
    """
    conn = sqlite3.connect('viralpost_history.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_creation TEXT,
            modele TEXT,
            sujet TEXT,
            ton TEXT,
            audience TEXT,
            reseau TEXT,
            contenu TEXT,
            prompt_utilise TEXT,
            image_path TEXT
        )
    ''')
    # Ajouter la colonne image_path si elle n'existe pas (migration)
    try:
        c.execute('ALTER TABLE posts ADD COLUMN image_path TEXT')
    except sqlite3.OperationalError:
        pass  # La colonne existe déjà
    conn.commit()
    return conn

# Sauvegarder un post dans la base de données
def save_post(conn, modele, sujet, ton, audience, reseau, contenu, prompt, image_path=None):
    """
    Sauvegarde un post dans la base de données.
    Utilise la connexion mise en cache par @st.cache_resource avec check_same_thread=False.
    """
    try:
        c = conn.cursor()
        c.execute('''
            INSERT INTO posts (date_creation, modele, sujet, ton, audience, reseau, contenu, prompt_utilise, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), modele, sujet, ton, audience, reseau, contenu, prompt, image_path))
        conn.commit()
    except sqlite3.Error as e:
        # En cas d'erreur, récupérer la connexion mise en cache
        # @st.cache_resource garantit qu'on obtient toujours la même instance
        conn = init_database()
        c = conn.cursor()
        c.execute('''
            INSERT INTO posts (date_creation, modele, sujet, ton, audience, reseau, contenu, prompt_utilise, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), modele, sujet, ton, audience, reseau, contenu, prompt, image_path))
        conn.commit()

# Récupérer l'historique
def get_history(conn):
    return pd.read_sql_query('''
        SELECT id, date_creation, modele, sujet, ton, audience, reseau, contenu, image_path
        FROM posts
        ORDER BY date_creation DESC
        LIMIT 50
    ''', conn)

# Templates de prompts pour chaque réseau social
def get_linkedin_prompt(sujet, ton, audience):
    ton_fr = {"professionnel": "professionnel et sérieux", "humoristique": "humoristique et engageant", "provocateur": "provocateur et percutant"}[ton]
    
    return f"""Crée un post LinkedIn professionnel LONG et DÉTAILLÉ (minimum 250-300 mots) optimisé pour le SEO avec la structure AIDA (Attention, Intérêt, Désir, Action).

Sujet: {sujet}
Ton: {ton_fr}
Audience cible: {audience}

STRUCTURE REQUISE:
1. ACCROCHE FORTE (première ligne percutante pour capter l'attention)
2. SAUT DE LIGNE (une ligne vide)
3. CORPS DU POST DÉTAILLÉ (développe le sujet en profondeur avec la structure AIDA):
   - Attention: accroche qui intrigue avec contexte et statistiques si pertinent
   - Intérêt: information pertinente, exemples concrets, cas d'usage, données chiffrées
   - Désir: bénéfices détaillés pour l'audience, avantages spécifiques, valeur ajoutée
   - Action: call-to-action clair et engageant
4. DÉVELOPPEMENT RICHE: Ajoute des exemples, des anecdotes, des conseils pratiques, des insights
5. SAUTS DE LIGNE entre les sections principales (utilise des sauts de lignes pour aérer le texte)
6. 5-8 HASHTAGS SEO pertinents et spécifiques à la fin (commençant par #)

IMPORTANT: 
- Le post doit faire MINIMUM 250-300 mots pour être optimisé SEO
- OBLIGATOIRE: Utilise 8-12 emojis pertinents stratégiquement placés dans tout le post (🔒 🔐 🛡️ ⚠️ 💡 ✅ 📊 🚀 etc.)
- Développe chaque point en détail avec des exemples concrets
- Utilise un vocabulaire riche et varié
- Structure le contenu avec des sauts de ligne pour améliorer la lisibilité
- Sois spécifique et détaillé, évite les généralités
- INTÈGRE les emojis naturellement dans le texte, pas seulement à la fin

RÉPONSE ATTENDUE: Le post complet avec emojis intégrés, sans explications supplémentaires."""

def get_instagram_prompt(sujet, ton, audience):
    ton_fr = {"professionnel": "professionnel", "humoristique": "décontracté et humoristique", "provocateur": "audacieux et provocateur"}[ton]
    
    return f"""Crée un post Instagram LONG et DÉTAILLÉ (minimum 200-250 mots) captivant, visuel et optimisé SEO.

Sujet: {sujet}
Ton: {ton_fr}
Audience cible: {audience}

STRUCTURE REQUISE:
1. ACCROCHE PERCUTANTE (première ligne très accrocheuse avec emoji, max 150 caractères)
2. Utilise BEAUCOUP D'EMOJIS stratégiquement placés (au moins 15-20 emojis pertinents) pour le rendre visuel et engageant
3. CORPS DU POST DÉVELOPPÉ:
   - Paragraphe 1: Introduction détaillée avec contexte et exemples
   - Paragraphe 2: Développement du sujet avec conseils pratiques, astuces, insights
   - Paragraphe 3: Conclusion engageante avec valeur ajoutée
   - Utilise des emojis comme puces (➡️ 💡 ⭐ ✨ 🎯) pour structurer visuellement
4. STYLE VISUEL RICHE: utilise des sauts de ligne, des espaces, des emojis et des séparateurs visuels pour créer un design attractif
5. DÉTAILS ET EXEMPLES: Ajoute des conseils concrets, des astuces pratiques, des données si pertinent
6. À LA FIN, ajoute un bloc de hashtags SEO cachés séparé par une ligne vide (15-20 hashtags pertinents):
   #hashtag1 #hashtag2 #hashtag3 #hashtag4 #hashtag5 #hashtag6 #hashtag7 #hashtag8 #hashtag9 #hashtag10 #hashtag11 #hashtag12 #hashtag13 #hashtag14 #hashtag15

IMPORTANT:
- Le post doit faire MINIMUM 200-250 mots (sans compter les hashtags)
- OBLIGATOIRE: Utilise ABSOLUMENT 20-25 emojis pertinents dans tout le post (💡 ✨ 🎯 ⭐ 🔥 💪 🚀 📱 💬 ❤️ 💎 🎨 🌟 💼 🎁 etc.)
- Développe le contenu en détail avec des exemples concrets
- INTÈGRE les emojis dans chaque phrase, pas seulement au début ou à la fin
- Utilise des emojis comme puces visuelles (➡️ 💡 ⭐ ✨ 🎯) pour structurer
- Structure visuellement avec des sauts de ligne et des emojis-puces
- Sois spécifique, détaillé et engageant
- Les emojis doivent être NATURELS et pertinents au contenu

RÉPONSE ATTENDUE: Le post complet avec emojis intégrés partout, sans explications supplémentaires."""

def get_facebook_prompt(sujet, ton, audience):
    ton_fr = {"professionnel": "amical et professionnel", "humoristique": "décontracté et humoristique", "provocateur": "audacieux et engageant"}[ton]
    
    return f"""Crée un post Facebook LONG et DÉTAILLÉ (minimum 200-250 mots) avec un style communautaire qui encourage l'interaction, optimisé SEO.

Sujet: {sujet}
Ton: {ton_fr}
Audience cible: {audience}

STRUCTURE REQUISE:
1. INTRO ENGAGEANTE DÉTAILLÉE qui crée un sentiment de communauté (paragraphe développé avec contexte)
2. CORPS DU POST DÉVELOPPÉ:
   - Paragraphe 1: Développement du sujet avec exemples concrets, anecdotes, conseils pratiques
   - Paragraphe 2: Approfondissement avec insights, astuces, valeur ajoutée pour l'audience
   - Paragraphe 3: Transition vers l'interaction avec éléments engageants
3. INCITE À L'INTERACTION: pose 3-4 QUESTIONS DIRECTES et variées à la fin pour encourager les commentaires
4. STYLE COMMUNautaire: utilise "vous", "nous", "partagez votre expérience", "dites-moi", "racontez-nous"
5. DÉTAILS RICHES: Ajoute des exemples personnels, des conseils pratiques, des réflexions approfondies
6. Ferme par un appel à l'engagement fort (ex: "Qu'en pensez-vous?", "Partagez votre avis en commentaire", "Racontez-nous votre expérience")

IMPORTANT:
- Le post doit faire MINIMUM 200-250 mots pour être optimisé SEO
- OBLIGATOIRE: Utilise 10-15 emojis pertinents stratégiquement placés dans tout le post (👥 💬 💡 ❤️ 🤝 🎯 ✨ 🔥 💪 🚀 📝 💎 etc.)
- Développe chaque point en détail avec des exemples concrets
- Utilise un ton conversationnel mais informatif
- Structure avec des sauts de ligne pour améliorer la lisibilité
- Sois spécifique et détaillé, évite les généralités
- INTÈGRE les emojis naturellement dans le texte pour créer de l'engagement

RÉPONSE ATTENDUE: Le post complet avec emojis intégrés et questions d'interaction, sans explications supplémentaires."""

# Fonction pour créer un bouton de copie avec JavaScript
def create_copy_button(text, button_key):
    # Encoder le texte en base64 pour éviter les problèmes de caractères spéciaux
    text_encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
    
    return st.markdown(f"""
    <button id="copy-btn-{button_key}" 
    style="background-color: #1DA1F2; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; width: 100%; font-weight: bold; margin-top: 10px;">
    📋 Copier dans le presse-papier
    </button>
    <script>
    (function() {{
        var btn = document.getElementById('copy-btn-{button_key}');
        if (btn) {{
            btn.addEventListener('click', function() {{
                var text = atob('{text_encoded}');
                navigator.clipboard.writeText(text).then(function() {{
                    alert('✅ Copié dans le presse-papier!');
                }}, function(err) {{
                    alert('Erreur lors de la copie: ' + err);
                }});
            }});
        }}
    }})();
    </script>
    """, unsafe_allow_html=True)

# Obtenir un modèle Gemini disponible
def get_available_gemini_model(genai):
    """
    Liste les modèles Gemini disponibles et retourne le premier qui supporte generateContent.
    """
    try:
        available_models = genai.list_models()
        for model in available_models:
            if 'generateContent' in model.supported_generation_methods:
                # Retirer le préfixe "models/" si présent
                model_name = model.name.replace('models/', '')
                return model_name
        return None
    except Exception:
        return None

# Fonction pour obtenir les clés API (priorité aux clés utilisateur, puis .env si mot de passe OK)
def get_api_keys():
    """Retourne les clés API en priorisant les clés de session_state (utilisateur), puis .env si protégé"""
    # Clés de l'utilisateur (widgets ou sauvegardées)
    user_mistral = st.session_state.get('input_mistral_key') or st.session_state.get('user_mistral_api_key') or ''
    user_google = st.session_state.get('input_google_key') or st.session_state.get('user_google_api_key') or ''
    
    # Convertir chaînes vides en None
    user_mistral = user_mistral.strip() if user_mistral else None
    user_google = user_google.strip() if user_google else None
    
    # Clés du .env (protégées par mot de passe)
    env_mistral = None
    env_google = None
    if st.session_state.get('env_unlocked', False):
        env_mistral = _MISTRAL_API_KEY_ENV
        env_google = _GOOGLE_AI_API_KEY_ENV
    
    # Priorité : clés utilisateur > clés .env
    mistral_key = user_mistral if user_mistral else env_mistral
    google_key = user_google if user_google else env_google
    
    return mistral_key, google_key

# Générer un post avec Ollama, Google AI Studio (Gemini) ou Mistral AI
def generate_post(prompt, modele, use_google_ai=False, use_mistral_ai=False):
    system_message = 'Tu es un expert en création de contenu viral et SEO pour les réseaux sociaux. Tu crées des posts LONGs, DÉTAILLÉS, engageants et optimisés SEO pour LinkedIn, Instagram et Facebook. Tes posts sont toujours développés en profondeur avec des exemples concrets, des conseils pratiques et un contenu riche. TU DOIS TOUJOURS INTÉGRER DES EMOJIS dans tes posts - c\'est OBLIGATOIRE et essentiel pour l\'engagement.'
    
    # Obtenir les clés API (utilisateur en priorité, puis .env)
    MISTRAL_API_KEY, GOOGLE_AI_API_KEY = get_api_keys()
    
    # Utilisation de Mistral AI si disponible et demandé
    if use_mistral_ai and MISTRAL_API_KEY:
        try:
            from mistralai import Mistral
            
            client = Mistral(api_key=MISTRAL_API_KEY)
            # Utiliser un modèle Mistral gratuit (mistral-small-latest ou mistral-tiny)
            model_name = "mistral-small-latest"  # Modèle gratuit recommandé
            
            full_prompt = f"{system_message}\n\n{prompt}"
            chat_response = client.chat.complete(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ]
            )
            return chat_response.choices[0].message.content.strip()
        except ImportError:
            st.error("Bibliothèque mistralai non installée. Installez avec: pip install mistralai")
            return None
        except Exception as e:
            st.error(f"Erreur avec Mistral AI: {str(e)}")
            st.info("Vérifiez que votre clé API Mistral AI est correcte dans le fichier .env")
            return None
    
    # Utilisation de Google AI Studio (Gemini) si disponible et demandé
    if use_google_ai and GOOGLE_AI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GOOGLE_AI_API_KEY)
            
            # Essayer de trouver un modèle disponible dynamiquement
            available_model = get_available_gemini_model(genai)
            
            # Si aucun modèle trouvé, essayer une liste de modèles modernes,
            # puis des modèles plus anciens en secours. En cas d'erreur (quota,
            # modèle indisponible, etc.), on passe automatiquement au suivant.
            model_names = [
                # Modèle détecté dynamiquement (priorité)
                available_model,
                # Nouveaux modèles texte Gemini (gratuits selon le quota Google)
                'gemini-3.1-pro-preview',
                'gemini-3-pro-preview',
                'gemini-3-flash-preview',
                'gemini-3.1-flash-lite-preview',
                'gemini-2.5-pro',
                'gemini-2.5-flash',
                # Anciens modèles en dernier recours
                'gemini-1.5-flash',
                'gemini-1.5-flash-002',
                'gemini-1.5-pro',
                'gemini-pro',
            ]
            model_names = [m for m in model_names if m]  # Retirer None
            
            last_error = None
            for model_name in model_names:
                try:
                    model = genai.GenerativeModel(model_name)
                    full_prompt = f"{system_message}\n\n{prompt}"
                    response = model.generate_content(full_prompt)
                    return response.text.strip()
                except Exception as e:
                    last_error = e
                    continue
            
            # Si aucun modèle n'a fonctionné
            if last_error:
                st.error(f"Erreur avec Google AI Studio: {str(last_error)}")
                st.info("Aucun modèle Gemini disponible. Essayez de mettre à jour la bibliothèque: pip install --upgrade google-generativeai")
            return None
            
        except ImportError:
            st.error("Bibliothèque google-generativeai non installée. Installez avec: pip install google-generativeai")
            return None
        except Exception as e:
            st.error(f"Erreur avec Google AI Studio: {str(e)}")
            st.info("Vérifiez que votre clé API Google AI Studio est correcte dans le fichier .env")
            return None
    
    # Utilisation d'Ollama (par défaut)
    try:
        response = ollama.chat(
            model=modele,
            messages=[
                {
                    'role': 'system',
                    'content': system_message
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        )
        # Extraction du contenu de la réponse
        if 'message' in response and 'content' in response['message']:
            return response['message']['content'].strip()
        elif 'content' in response:
            return response['content'].strip()
        else:
            st.error("Format de réponse Ollama inattendu.")
            return None
    except Exception as e:
        error_msg = str(e)
        if 'model' in error_msg.lower() or 'not found' in error_msg.lower():
            st.error(f"Modèle '{modele}' non trouvé. Vérifiez qu'il est installé avec: `ollama pull {modele}`")
        else:
            st.error(f"Erreur lors de la génération: {error_msg}")
            st.info("Assurez-vous qu'Ollama est en cours d'exécution. Vous pouvez le démarrer avec: `ollama serve`")
        return None

# Interface principale
def main():
    # Header
    st.markdown('<div class="main-header">🚀 ViralPost AI</div>', unsafe_allow_html=True)
    
    # Initialisation de la base de données (mise en cache avec @st.cache_resource)
    # La connexion est partagée entre tous les threads Streamlit grâce à check_same_thread=False
    st.session_state.db_conn = init_database()
    
    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Initialiser les clés si non définies dans session_state
        if 'user_mistral_api_key' not in st.session_state:
            st.session_state.user_mistral_api_key = ''
        if 'user_google_api_key' not in st.session_state:
            st.session_state.user_google_api_key = ''
        if 'env_unlocked' not in st.session_state:
            st.session_state.env_unlocked = False
        
        # Section Clés API personnelles
        with st.expander("🔑 Clés API personnelles", expanded=False):
            st.info("💡 Entrez vos propres clés API ici. Elles auront priorité sur celles du .env")
            
            # Clé API Mistral AI utilisateur
            user_mistral_key = st.text_input(
                "Clé API Mistral AI (optionnel)",
                value=st.session_state.user_mistral_api_key,
                type="password",
                key="input_mistral_key",
                help="Obtenez votre clé gratuitement sur https://console.mistral.ai/api-keys/"
            )
            if user_mistral_key:
                st.session_state.user_mistral_api_key = user_mistral_key
            
            # Clé API Google AI utilisateur
            user_google_key = st.text_input(
                "Clé API Google AI Studio (optionnel)",
                value=st.session_state.user_google_api_key,
                type="password",
                key="input_google_key",
                help="Obtenez votre clé sur https://aistudio.google.com/app/apikey"
            )
            if user_google_key:
                st.session_state.user_google_api_key = user_google_key
            
            # Bouton pour effacer les clés
            if st.session_state.user_mistral_api_key or st.session_state.user_google_api_key:
                if st.button("🗑️ Effacer mes clés API", key="clear_user_keys"):
                    st.session_state.user_mistral_api_key = ''
                    st.session_state.user_google_api_key = ''
                    st.rerun()
            
            st.divider()
            
            # Accès aux clés API du .env (protégé par mot de passe)
            st.caption("🔒 Clés API du projet (nécessite un mot de passe)")
            password_input = st.text_input(
                "Mot de passe pour accéder aux clés .env",
                value="",
                type="password",
                key="env_password_input",
                help="Entrez le mot de passe pour utiliser les clés API configurées dans le .env"
            )
            
            # Vérifier le mot de passe seulement si une nouvelle tentative est faite
            if 'last_password_input' not in st.session_state:
                st.session_state.last_password_input = ''
            
            if password_input and password_input != st.session_state.last_password_input:
                st.session_state.last_password_input = password_input
                if check_password(password_input):
                    st.session_state.env_unlocked = True
                    st.success("✅ Mot de passe correct ! Clés .env déverrouillées")
                else:
                    st.session_state.env_unlocked = False
                    st.error("❌ Mot de passe incorrect")
            
            # Afficher le statut si déverrouillé
            if st.session_state.env_unlocked:
                st.success("🔓 Clés .env déverrouillées")
        
        # Obtenir les clés API actuelles (utilisateur en priorité, puis .env si déverrouillé)
        mistral_key, google_key = get_api_keys()
        
        # Choix du moteur IA
        engine_options = ["Ollama (Local)"]
        if mistral_key:
            engine_options.append("Mistral AI (Gratuit)")
        if google_key:
            engine_options.append("Google AI Studio (Gemini)")
        
        # Déterminer l'index par défaut (toujours dans la plage valide)
        default_index = 0
        if 'use_mistral_ai' in st.session_state and st.session_state.use_mistral_ai and "Mistral AI (Gratuit)" in engine_options:
            default_index = engine_options.index("Mistral AI (Gratuit)")
        elif 'use_google_ai' in st.session_state and st.session_state.use_google_ai and "Google AI Studio (Gemini)" in engine_options:
            default_index = engine_options.index("Google AI Studio (Gemini)")
        default_index = min(default_index, len(engine_options) - 1)
        default_index = max(0, default_index)
        
        engine_choice = st.radio(
            "Moteur IA",
            options=engine_options,
            index=default_index
        )
        use_mistral_ai = (engine_choice == "Mistral AI (Gratuit)")
        use_google_ai = (engine_choice == "Google AI Studio (Gemini)")
        st.session_state.use_mistral_ai = use_mistral_ai
        st.session_state.use_google_ai = use_google_ai
        
        if not use_mistral_ai and not use_google_ai:
            # Liste des modèles Ollama
            try:
                result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Parser la sortie de 'ollama list' pour extraire les noms de modèles
                    lines = result.stdout.strip().split('\n')[1:]  # Ignorer la ligne d'en-tête
                    available_models = [line.split()[0] for line in lines if line.strip() and not line.startswith('NAME')]
                    if not available_models:
                        st.warning("Aucun modèle Ollama détecté. Veuillez installer un modèle avec: `ollama pull llama3`")
                        available_models = ['llama3', 'mistral', 'phi3']
                else:
                    available_models = ['llama3', 'mistral', 'phi3']
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
                st.warning("Impossible de se connecter à Ollama. Assurez-vous qu'Ollama est installé et en cours d'exécution.")
                available_models = ['llama3', 'mistral', 'phi3']
            
            modele = st.selectbox(
                "Modèle Ollama",
                options=available_models,
                index=0 if available_models else None
            )
            st.session_state.current_modele = modele
        elif use_mistral_ai:
            modele = "mistral-small-latest"  # Modèle Mistral AI par défaut
            st.session_state.current_modele = modele
            if not mistral_key:
                st.error("⚠️ Clé API Mistral AI non trouvée!")
                st.info("💡 Entrez votre clé API Mistral AI dans la section '🔑 Clés API personnelles' ci-dessus")
        else:
            modele = "gemini-1.5-flash"  # Modèle Google AI par défaut
            st.session_state.current_modele = modele
            if not google_key:
                st.error("⚠️ Clé API Google AI Studio non trouvée!")
                st.info("💡 Entrez votre clé API Google AI dans la section '🔑 Clés API personnelles' ci-dessus")
        
        # Afficher des messages informatifs
        if not mistral_key and not use_mistral_ai:
            st.info("💡 Pour utiliser Mistral AI (gratuit), entrez votre clé API dans la section '🔑 Clés API personnelles'")
        if not google_key and not use_google_ai:
            st.info("💡 Pour utiliser Google AI Studio, entrez votre clé API dans la section '🔑 Clés API personnelles'")
        
        st.divider()
        st.header("📝 Paramètres du Post")
        
        sujet = st.text_area(
            "Sujet du post",
            placeholder="Ex: Les bienfaits du télétravail...",
            height=100
        )
        
        ton = st.selectbox(
            "Ton",
            options=["professionnel", "humoristique", "provocateur"],
            index=0
        )
        
        audience = st.text_input(
            "Audience cible",
            placeholder="Ex: Entrepreneurs, Professionnels du marketing..."
        )
        
        st.divider()
        
        # Bouton pour voir l'historique
        if st.button("📚 Voir l'historique"):
            st.session_state.show_history = True
        else:
            if 'show_history' not in st.session_state:
                st.session_state.show_history = False
    
    # Affichage de l'historique dans la sidebar si demandé
    if st.session_state.show_history:
        with st.sidebar:
            st.divider()
            st.subheader("📚 Historique récent")
            history_df = get_history(st.session_state.db_conn)
            if not history_df.empty:
                for idx, row in history_df.head(10).iterrows():
                    with st.expander(f"{row['reseau']} - {row['date_creation'][:16]}"):
                        st.write(f"**Sujet:** {row['sujet']}")
                        st.write(f"**Ton:** {row['ton']}")
                        st.text_area("Contenu", value=row['contenu'], height=100, key=f"hist_{row['id']}")
                        create_copy_button(row['contenu'], f"hist_copy_{row['id']}")
            else:
                st.info("Aucun post dans l'historique")
    
    # Zone principale - Onglets pour les réseaux sociaux
    if not sujet or not audience:
        st.info("👈 Veuillez remplir le sujet et l'audience cible dans la barre latérale pour commencer.")
    else:
        tab1, tab2, tab3 = st.tabs(["💼 LinkedIn", "📸 Instagram", "👥 Facebook"])
        
        # Onglet LinkedIn
        with tab1:
            st.subheader("Générer un post LinkedIn")
            col1, col2 = st.columns([3, 1])
            
            with col1:
                use_google_ai = st.session_state.get('use_google_ai', False)
                use_mistral_ai = st.session_state.get('use_mistral_ai', False)
                modele = st.session_state.get('current_modele', 'llama3')
                if use_mistral_ai:
                    engine_name = "Mistral AI"
                elif use_google_ai:
                    engine_name = "Google AI Studio"
                else:
                    engine_name = "Ollama"
                if st.button("🚀 Générer le post LinkedIn", key="gen_linkedin"):
                    with st.spinner(f"Génération en cours avec {engine_name}..."):
                        prompt = get_linkedin_prompt(sujet, ton, audience)
                        post_content = generate_post(prompt, modele, use_google_ai, use_mistral_ai)
                        
                        if post_content:
                            st.session_state.linkedin_post = post_content
                            st.session_state.linkedin_prompt = prompt
                            
                            save_post(
                                st.session_state.db_conn,
                                modele, sujet, ton, audience,
                                "LinkedIn", post_content, prompt, None
                            )
                            st.success("Post généré avec succès!")
            
            if 'linkedin_post' in st.session_state:
                st.markdown('<div class="post-container">', unsafe_allow_html=True)
                st.markdown("### Votre post LinkedIn")
                
                st.text_area(
                    "Contenu",
                    value=st.session_state.linkedin_post,
                    height=300,
                    key="linkedin_display",
                    label_visibility="collapsed"
                )
                
                col_copy, col_regen = st.columns([1, 1])
                with col_copy:
                    create_copy_button(st.session_state.linkedin_post, "linkedin_copy")
                
                with col_regen:
                    if st.button("🔄 Régénérer", key="regen_linkedin"):
                        use_google_ai = st.session_state.get('use_google_ai', False)
                        use_mistral_ai = st.session_state.get('use_mistral_ai', False)
                        modele = st.session_state.get('current_modele', 'llama3')
                        with st.spinner("Régénération en cours..."):
                            prompt = get_linkedin_prompt(sujet, ton, audience)
                            post_content = generate_post(prompt, modele, use_google_ai, use_mistral_ai)
                            if post_content:
                                st.session_state.linkedin_post = post_content
                                st.session_state.linkedin_prompt = prompt
                                save_post(
                                    st.session_state.db_conn,
                                    modele, sujet, ton, audience,
                                    "LinkedIn", post_content, prompt, None
                                )
                                st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Onglet Instagram
        with tab2:
            st.subheader("Générer un post Instagram")
            col1, col2 = st.columns([3, 1])
            
            with col1:
                use_google_ai = st.session_state.get('use_google_ai', False)
                use_mistral_ai = st.session_state.get('use_mistral_ai', False)
                modele = st.session_state.get('current_modele', 'llama3')
                if use_mistral_ai:
                    engine_name = "Mistral AI"
                elif use_google_ai:
                    engine_name = "Google AI Studio"
                else:
                    engine_name = "Ollama"
                if st.button("🚀 Générer le post Instagram", key="gen_instagram"):
                    with st.spinner(f"Génération en cours avec {engine_name}..."):
                        prompt = get_instagram_prompt(sujet, ton, audience)
                        post_content = generate_post(prompt, modele, use_google_ai, use_mistral_ai)
                        
                        if post_content:
                            st.session_state.instagram_post = post_content
                            st.session_state.instagram_prompt = prompt
                            
                            save_post(
                                st.session_state.db_conn,
                                modele, sujet, ton, audience,
                                "Instagram", post_content, prompt, None
                            )
                            st.success("Post généré avec succès!")
            
            if 'instagram_post' in st.session_state:
                st.markdown('<div class="post-container">', unsafe_allow_html=True)
                st.markdown("### Votre post Instagram")
                
                st.text_area(
                    "Contenu",
                    value=st.session_state.instagram_post,
                    height=300,
                    key="instagram_display",
                    label_visibility="collapsed"
                )
                
                col_copy, col_regen = st.columns([1, 1])
                with col_copy:
                    create_copy_button(st.session_state.instagram_post, "instagram_copy")
                
                with col_regen:
                    if st.button("🔄 Régénérer", key="regen_instagram"):
                        use_google_ai = st.session_state.get('use_google_ai', False)
                        use_mistral_ai = st.session_state.get('use_mistral_ai', False)
                        modele = st.session_state.get('current_modele', 'llama3')
                        with st.spinner("Régénération en cours..."):
                            prompt = get_instagram_prompt(sujet, ton, audience)
                            post_content = generate_post(prompt, modele, use_google_ai, use_mistral_ai)
                            if post_content:
                                st.session_state.instagram_post = post_content
                                st.session_state.instagram_prompt = prompt
                                save_post(
                                    st.session_state.db_conn,
                                    modele, sujet, ton, audience,
                                    "Instagram", post_content, prompt, None
                                )
                                st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Onglet Facebook
        with tab3:
            st.subheader("Générer un post Facebook")
            col1, col2 = st.columns([3, 1])
            
            with col1:
                use_google_ai = st.session_state.get('use_google_ai', False)
                use_mistral_ai = st.session_state.get('use_mistral_ai', False)
                modele = st.session_state.get('current_modele', 'llama3')
                if use_mistral_ai:
                    engine_name = "Mistral AI"
                elif use_google_ai:
                    engine_name = "Google AI Studio"
                else:
                    engine_name = "Ollama"
                if st.button("🚀 Générer le post Facebook", key="gen_facebook"):
                    with st.spinner(f"Génération en cours avec {engine_name}..."):
                        prompt = get_facebook_prompt(sujet, ton, audience)
                        post_content = generate_post(prompt, modele, use_google_ai, use_mistral_ai)
                        
                        if post_content:
                            st.session_state.facebook_post = post_content
                            st.session_state.facebook_prompt = prompt
                            
                            save_post(
                                st.session_state.db_conn,
                                modele, sujet, ton, audience,
                                "Facebook", post_content, prompt, None
                            )
                            st.success("Post généré avec succès!")
            
            if 'facebook_post' in st.session_state:
                st.markdown('<div class="post-container">', unsafe_allow_html=True)
                st.markdown("### Votre post Facebook")
                
                st.text_area(
                    "Contenu",
                    value=st.session_state.facebook_post,
                    height=300,
                    key="facebook_display",
                    label_visibility="collapsed"
                )
                
                col_copy, col_regen = st.columns([1, 1])
                with col_copy:
                    create_copy_button(st.session_state.facebook_post, "facebook_copy")
                
                with col_regen:
                    if st.button("🔄 Régénérer", key="regen_facebook"):
                        use_google_ai = st.session_state.get('use_google_ai', False)
                        use_mistral_ai = st.session_state.get('use_mistral_ai', False)
                        modele = st.session_state.get('current_modele', 'llama3')
                        with st.spinner("Régénération en cours..."):
                            prompt = get_facebook_prompt(sujet, ton, audience)
                            post_content = generate_post(prompt, modele, use_google_ai, use_mistral_ai)
                            if post_content:
                                st.session_state.facebook_post = post_content
                                st.session_state.facebook_prompt = prompt
                                save_post(
                                    st.session_state.db_conn,
                                    modele, sujet, ton, audience,
                                    "Facebook", post_content, prompt, None
                                )
                                st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
