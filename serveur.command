#!/bin/bash
# SPDX-License-Identifier: CC-BY-NC-SA-4.0 | Monolithe Fœto — Stéphanie
# Double-clic dans le Finder, quel que soit le dossier courant.
exec /bin/bash "$(cd -- "$(dirname -- "$0")" && pwd)/hub/app/serveur.command" "$@"
