#!/bin/bash
# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# N'ouvre que la base fictive dédiée, jamais hub/hub.sqlite.
set -eu
export PATH="${PATH}:/opt/homebrew/bin:/usr/local/bin"
ICI="$(cd -- "$(dirname -- "$0")" && pwd)"
cd "$ICI"
fin() {
    code=$?
    if [ "$code" -ne 0 ]; then
        echo "Démonstration interrompue. Consulter l'erreur ci-dessus."
        if [ -t 0 ]; then read -r -p "Entrée pour fermer… " reponse || true; fi
    fi
}
trap fin EXIT
PYTHON="$ICI/.demo-python/bin/python"
if [ ! -x "$PYTHON" ]; then
    INTERPRETE=""
    for candidat in python3 python3.14 python3.13 python3.12 python3.11 python3.10; do
        if command -v "$candidat" >/dev/null 2>&1 && "$candidat" -c 'import sys; sys.exit(sys.version_info < (3,10))' 2>/dev/null; then
            INTERPRETE="$(command -v "$candidat")"
            break
        fi
    done
    if [ -z "$INTERPRETE" ]; then
        echo "Installer Python 3.10 ou plus récent depuis python.org, puis relancer ce fichier."
        exit 2
    fi
    "$INTERPRETE" -m venv "$ICI/.demo-python"
fi
if ! "$PYTHON" -c 'import sys; sys.exit(sys.version_info < (3,10))' 2>/dev/null; then
    echo "L'environnement .demo-python nécessite Python 3.10 ou plus récent."
    exit 2
fi
if ! "$PYTHON" -c 'import flask, PIL' 2>/dev/null; then
    echo "Installation des dépendances de démonstration (Internet nécessaire)…"
    "$PYTHON" -m pip install -r "$ICI/hub/demonstrations/requirements.txt"
fi
"$PYTHON" "$ICI/hub/outils/demonstration_slo.py" "$@"
