#!/bin/bash
# SPDX-License-Identifier: CC-BY-NC-SA-4.0 | Monolithe Fœto — Stéphanie
set -eu

# Le Terminal du Finder n'a pas toujours les chemins de Python/Homebrew.
export PATH="${PATH}:/opt/homebrew/bin:/usr/local/bin"
ICI="$(cd -- "$(dirname -- "$0")" && pwd)"
cd "$ICI"

erreur_sortie() {
    code=$?
    if [ "$code" -ne 0 ]; then
        echo
        echo "Lancement interrompu. Les détails de l'erreur sont affichés ci-dessus."
        if [ -t 0 ]; then
            read -r -p "Appuyer sur Entrée pour fermer… " reponse || true
        fi
    fi
}
trap erreur_sortie EXIT

compatible() {
    "$1" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null
}

PYTHON="$ICI/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
    INTERPRETE=""
    for candidat in python3 python3.14 python3.13 python3.12 python3.11 python3.10; do
        if command -v "$candidat" >/dev/null 2>&1 && compatible "$candidat"; then
            INTERPRETE="$(command -v "$candidat")"
            break
        fi
    done
    if [ -z "$INTERPRETE" ]; then
        echo "Python 3.10 ou plus récent est nécessaire."
        echo "Installer Python pour macOS depuis https://www.python.org/downloads/macos/"
        echo "puis refaire un double-clic sur serveur.command."
        exit 2
    fi
    echo "Préparation de Python dans ce dossier (premier lancement)…"
    "$INTERPRETE" -m venv "$ICI/.venv"
fi
if ! compatible "$PYTHON"; then
    echo "L'environnement .venv est incompatible. Voir hub/README.md, section macOS."
    exit 2
fi

# Réseau au premier lancement ou si les dépendances ont changé/manquent.
# Aucun paquet n'est installé dans le Python système ou celui d'un autre hub.
if ! cmp -s "$ICI/requirements.txt" "$ICI/.venv/requirements-installes.txt" ||
   ! "$PYTHON" -c 'import flask, PIL' 2>/dev/null; then
    echo "Installation des dépendances (connexion Internet nécessaire)…"
    "$PYTHON" -m pip install -r "$ICI/requirements.txt"
    cp "$ICI/requirements.txt" "$ICI/.venv/requirements-installes.txt"
fi

# Facultatif : réutiliser la base ordinaire d'une installation existante.
BASE="$ICI/.."
CONFIG="$ICI/../../base_locale.txt"
if [ -f "$CONFIG" ]; then
    IFS= read -r BASE < "$CONFIG" || [ -n "$BASE" ]
    BASE="${BASE%$'\r'}"
    case "$BASE" in
        /*) ;;
        *) echo "base_locale.txt doit contenir le chemin absolu du dossier hub existant."; exit 2 ;;
    esac
    if [ ! -f "$BASE/hub.sqlite" ]; then
        echo "Base existante introuvable : $BASE/hub.sqlite. Aucune base de remplacement créée."
        exit 2
    fi
fi

echo "Monolithe Fœto — Stéphanie (port 5006 par défaut)"
echo "Garder cette fenêtre ouverte ; Ctrl+C arrête uniquement cette version."
"$PYTHON" "$ICI/serveur.py" --base "$BASE" --ouvrir-navigateur "$@"
