#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Importer le dossier fictif exact dans une base d'essai explicitement choisie.
python hub/outils/importer_placenta_demo.py --base /chemin/base-test
"""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'hub/app'))
import ingest


def importer(base):
    jeu=json.loads((ROOT/'hub/exemples/DEMO_SLO_001.json').read_text(encoding='utf-8'))
    assert jeu['dossier']=='DEMO_SLO_001' and jeu['fictif'] is True
    ingest.arborescence(base)
    cx,_=ingest.ouvrir(base/'hub.sqlite')
    try:
        ingest.migrer(cx,ROOT/'hub/app/migrations',bavard=False)
        if cx.execute('SELECT 1 FROM dossiers WHERE numero=?',(jeu['dossier'],)).fetchone():
            raise SystemExit('DEMO_SLO_001 existe déjà : aucune donnée remplacée.')
        for doc in jeu['saisies']:
            ingest.ingerer(cx,base,json.dumps(doc,ensure_ascii=False).encode(),f"{doc['dossier']}_{doc['module']}.json",provenance='poste')
        for cr in jeu.get('comptes_rendus',[]):
            cx.execute('INSERT INTO comptes_rendus (dossier,gabarit,gabarit_version,texte,operateur,format) VALUES (?,?,?,?,?,?)',
                       (jeu['dossier'],cr['gabarit'],cr.get('gabarit_version'),cr['texte'],cr.get('operateur'),cr.get('format','texte')))
        cx.commit()
        ingest.ecrire_index(cx,base)
    except BaseException:
        cx.rollback()
        raise
    finally:
        cx.close()


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base',type=Path,required=True)
    base=ap.parse_args().base.resolve()
    base.mkdir(parents=True,exist_ok=True)
    importer(base)
    print('Dossier fictif importé dans',base)
