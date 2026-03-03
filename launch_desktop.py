"""
Script de lancement pour l'application desktop ViralPost AI
Démarre Streamlit en arrière-plan et ouvre une fenêtre native avec pywebview
"""
import subprocess
import threading
import time
import sys
import os
import webbrowser
from pathlib import Path

try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    print("⚠️ pywebview non installé. Installation...")
    print("Exécutez: pip install pywebview")

try:
    import streamlit
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    print("⚠️ Streamlit non installé. Exécutez: pip install streamlit")


def check_streamlit_ready(url="http://localhost:8501", timeout=30):
    """Vérifie si Streamlit est prêt à recevoir des connexions"""
    try:
        import urllib.request
        import urllib.error
    except ImportError:
        # Python < 3.3, utiliser urllib2
        import urllib2 as urllib_request
        urllib.error = urllib_request
        urllib.request = urllib_request
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = urllib.request.urlopen(url, timeout=2)
            if response.getcode() == 200:
                return True
        except (urllib.error.URLError, OSError, Exception):
            time.sleep(1)
    return False


def start_streamlit():
    """Démarre Streamlit en arrière-plan"""
    app_path = Path(__file__).parent / "app.py"
    
    if not app_path.exists():
        print(f"❌ Erreur: Fichier {app_path} introuvable")
        sys.exit(1)
    
    print("🚀 Démarrage de Streamlit...")
    
    # Démarrer Streamlit avec des paramètres optimisés pour pywebview
    # Ne pas utiliser PIPE pour stdout/stderr sinon le processus peut bloquer quand le buffer est plein
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app_path),
            "--server.headless", "true",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false",
            "--server.fileWatcherType", "none",  # Désactiver le file watcher pour éviter les problèmes
        ],
        cwd=str(app_path.parent),  # CWD = dossier du projet pour .env et DB
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )
    
    # Attendre que Streamlit soit prêt
    print("⏳ Attente du démarrage de Streamlit...")
    if check_streamlit_ready():
        print("✅ Streamlit est prêt!")
        return process
    else:
        print("❌ Timeout: Streamlit n'a pas démarré dans les temps")
        process.terminate()
        return None


def create_window(streamlit_process):
    """Crée la fenêtre pywebview et charge Streamlit"""
    if not WEBVIEW_AVAILABLE:
        print("❌ pywebview n'est pas installé")
        print("📦 Installation: pip install pywebview")
        if streamlit_process:
            streamlit_process.terminate()
        sys.exit(1)
    
    url = "http://localhost:8501"
    
    # Créer la fenêtre avec pywebview
    print("🪟 Ouverture de la fenêtre desktop...")
    print(f"🌐 URL: {url}")
    
    window = webview.create_window(
        title="🚀 ViralPost AI - Application Desktop",
        url=url,
        width=1400,
        height=900,
        min_size=(1000, 600),
        resizable=True,
        fullscreen=False,
        on_top=False,
        background_color='#FFFFFF',
        text_select=True,  # Permettre la sélection de texte
    )
    
    # Gérer la fermeture de la fenêtre
    def on_closing():
        print("🛑 Fermeture de l'application...")
        if streamlit_process:
            print("🛑 Arrêt de Streamlit...")
            streamlit_process.terminate()
            streamlit_process.wait(timeout=5)
        print("✅ Application fermée proprement")
    
    # Démarrer pywebview (c'est bloquant)
    try:
        webview.start(debug=False)
    except KeyboardInterrupt:
        print("\n⚠️ Interruption utilisateur")
    finally:
        on_closing()


def main():
    """Point d'entrée principal"""
    print("=" * 60)
    print("🚀 ViralPost AI - Application Desktop")
    print("=" * 60)
    print()
    
    # Vérifier que Streamlit est disponible
    if not STREAMLIT_AVAILABLE:
        print("❌ Streamlit n'est pas installé")
        print("📦 Installation: pip install streamlit")
        sys.exit(1)
    
    # Démarrer Streamlit
    streamlit_process = start_streamlit()
    
    if not streamlit_process:
        print("❌ Impossible de démarrer Streamlit")
        sys.exit(1)
    
    try:
        # Si pywebview n'est pas disponible, ouvrir dans le navigateur par défaut
        if not WEBVIEW_AVAILABLE:
            print("⚠️ pywebview n'est pas installé")
            print("📦 Installation: pip install pywebview")
            print("🌐 Ouverture dans le navigateur par défaut...")
            time.sleep(2)  # Attendre que Streamlit soit complètement prêt
            webbrowser.open("http://localhost:8501")
            
            # Attendre que l'utilisateur ferme manuellement
            try:
                streamlit_process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Arrêt de Streamlit...")
                streamlit_process.terminate()
        else:
            # Créer et afficher la fenêtre pywebview
            create_window(streamlit_process)
    except Exception as e:
        print(f"❌ Erreur: {e}")
        if streamlit_process:
            streamlit_process.terminate()
        sys.exit(1)


if __name__ == "__main__":
    main()
