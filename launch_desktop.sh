#!/bin/bash
# Script shell pour Linux/Mac pour lancer l'application desktop

echo "============================================"
echo "ViralPost AI - Application Desktop"
echo "============================================"
echo ""

# Vérifier que Python est installé
if ! command -v python3 &> /dev/null; then
    echo "[ERREUR] Python 3 n'est pas installé"
    echo "Veuillez installer Python 3 depuis https://www.python.org/"
    exit 1
fi

# Lancer l'application desktop
python3 launch_desktop.py

# Si erreur, afficher un message
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERREUR] Une erreur s'est produite lors du lancement"
    read -p "Appuyez sur Entrée pour continuer..."
fi
