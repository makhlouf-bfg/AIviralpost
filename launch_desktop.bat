@echo off
REM Script batch Windows pour lancer l'application desktop
echo ============================================
echo ViralPost AI - Application Desktop
echo ============================================
echo.

REM Vérifier que Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    echo Veuillez installer Python depuis https://www.python.org/
    pause
    exit /b 1
)

REM Lancer l'application desktop
python launch_desktop.py

REM Si erreur, afficher un message
if errorlevel 1 (
    echo.
    echo [ERREUR] Une erreur s'est produite lors du lancement
    pause
)
