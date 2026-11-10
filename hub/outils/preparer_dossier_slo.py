#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Reconstruit le fichier à importer. N'ouvre ni serveur ni base de données."""
import json
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1] / 'exemples'
SOURCE = RACINE / 'DEMO_SLO_001'


def construire():
    rapports = json.loads((SOURCE / 'comptes_rendus/manifest.json').read_text(encoding='utf-8'))
    for r in rapports:
        ext = '.html' if r['format'] == 'html' else '.txt'
        r['texte'] = (SOURCE / 'comptes_rendus' / (r['gabarit'] + ext)).read_text(encoding='utf-8')
    return {'type': 'monolithe_dossier', 'version': 1, 'dossier': 'DEMO_SLO_001',
            'nom': 'FICTIF – TEST – Smith-Lemli-Opitz', 'operateur': 'Codex', 'fictif': True,
            'saisies': [json.loads(p.read_text(encoding='utf-8')) for p in sorted((SOURCE / 'modules').glob('*.json'))],
            'comptes_rendus': rapports}


if __name__ == '__main__':
    (RACINE / 'DEMO_SLO_001.json').write_text(
        json.dumps(construire(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('hub/exemples/DEMO_SLO_001.json prêt pour l’import habituel.')
