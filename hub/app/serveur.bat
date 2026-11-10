@echo off
rem SPDX-License-Identifier: CC-BY-NC-SA-4.0 | Hub Light
rem Demarre le serveur local du hub et ouvre la page de gestion.
rem Cherche le premier python trouve : un python portable pose a cote
rem (python\python.exe ou WPy64-*\python-*\python.exe), sinon celui du PATH.
setlocal
cd /d "%~dp0"

set PORT=5006
if not "%~1"=="" set PORT=%~1

set PY=
if exist "%~dp0python\python.exe" set PY="%~dp0python\python.exe"
if not defined PY for /d %%D in ("%~dp0WPy*") do (
  for /d %%P in ("%%D\python-*") do if exist "%%P\python.exe" set PY="%%P\python.exe"
)
if not defined PY (
  where py >nul 2>&1 && set PY=py -3
)
if not defined PY (
  where python >nul 2>&1 && set PY=python
)
if not defined PY (
  echo Aucun interpreteur Python trouve.
  echo Poser un python portable dans "%~dp0python\" ou l'ajouter au PATH.
  pause
  exit /b 2
)

%PY% -c "import sys; sys.exit(sys.version_info < (3,10))" 2>nul
if errorlevel 1 (
  echo Python 3.10 ou plus recent est necessaire.
  pause
  exit /b 2
)
%PY% -c "import flask, PIL" 2>nul
if errorlevel 1 (
  rem Reseau bloque par defaut : on installe d'abord depuis les roues ^(.whl^)
  rem livrees dans python\wheels\, et on n'essaie le reseau qu'en dernier.
  echo Flask ou Pillow est absent. Installation depuis python\wheels\ ^(sans reseau^)...
  %PY% -m pip install --no-index --find-links "%~dp0python\wheels" -r "%~dp0requirements.txt"
  if errorlevel 1 (
    echo Pas de roues utilisables ici. Essai par le reseau...
    %PY% -m pip install -r "%~dp0requirements.txt"
    if errorlevel 1 (
      echo.
      echo Installation impossible ^(reseau bloque et pas de roues^).
      echo Utiliser le dossier app\ complet, avec son python\ fourni.
      echo Sans Flask, l'ingestion en ligne de commande marche toujours : ingest.bat
      pause
      exit /b 3
    )
  )
)

rem Choix facultatif de la base habituelle, sans recopier les dossiers.
set "BASE=%~dp0.."
if exist "%~dp0..\..\base_locale.txt" set /p BASE=<"%~dp0..\..\base_locale.txt"
if exist "%~dp0..\..\base_locale.txt" if not exist "%BASE%\hub.sqlite" (
  echo Base existante introuvable. Verifier base_locale.txt.
  pause
  exit /b 2
)

rem Ce dossier (app\) contient tout le code et, s'il est la, le python
rem portable. Les donnees vivent un cran au-dessus, dans le dossier parent.
%PY% "%~dp0serveur.py" --port %PORT% --base "%BASE%" --ouvrir-navigateur
set "CODE_SORTIE=%ERRORLEVEL%"
if not "%CODE_SORTIE%"=="0" echo Lancement interrompu. Voir les erreurs ci-dessus.
pause
exit /b %CODE_SORTIE%
