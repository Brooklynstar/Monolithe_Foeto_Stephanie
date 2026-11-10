#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Intègre la fonction JS commune sans dépendance réseau dans les HTML autonomes.

    python hub/outils/integrer_percentiles.py [--verifier]
    python pack_telephone.py
"""
from pathlib import Path
import sys

DEPOT = Path(__file__).resolve().parents[2]
SOURCE = DEPOT / "hub/app/web/percentiles.js"
CIBLES = (DEPOT / "Macro/biometrie_clinique.html", DEPOT / "hub/calculateur-unifie.html", DEPOT / "hub/app/dossiers.html")
DEBUT = "<!-- BEGIN percentiles.js -->"
FIN = "<!-- END percentiles.js -->"


def main():
    bloc = DEBUT + "\n<script>\n" + SOURCE.read_text(encoding="utf-8").rstrip() + "\n</script>\n" + FIN
    verifier = "--verifier" in sys.argv
    for cible in CIBLES:
        texte = cible.read_text(encoding="utf-8")
        if DEBUT in texte:
            avant, reste = texte.split(DEBUT, 1)
            _, apres = reste.split(FIN, 1)
            nouveau = avant + bloc + apres
        else:
            nouveau = texte.replace("<script>", bloc + "\n<script>", 1)
        if verifier:
            if nouveau != texte:
                raise SystemExit(f"Bloc commun périmé : {cible.relative_to(DEPOT)}")
        else:
            cible.write_text(nouveau, encoding="utf-8")


if __name__ == "__main__":
    main()
