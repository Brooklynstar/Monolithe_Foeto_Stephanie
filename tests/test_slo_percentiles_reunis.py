# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Le même dossier SLO utilise les trois familles de résultats, dans le Hub normal."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'hub/app'))
import ingest,serveur


class SLOPercentilesReunis(unittest.TestCase):
    def test_slo_accessible_organes_neuro_placenta_et_reouverture(self):
        with tempfile.TemporaryDirectory(prefix='slo-reuni-') as tmp:
            base=Path(tmp);ingest.arborescence(base);cx,_=ingest.ouvrir(base/'hub.sqlite')
            ingest.migrer(cx,ROOT/'hub/app/migrations',bavard=False);cx.close()
            client=serveur.creer_app(base,ROOT).test_client()
            fixture=ROOT/'hub/exemples/DEMO_SLO_001.json';original=fixture.read_bytes()
            self.assertEqual(client.post('/api/deposer',data={'fichiers':(io.BytesIO(original),'DEMO_SLO_001.json')}).status_code,200)
            self.assertEqual(client.post('/api/ingerer').json['ingerees'],1)
            d=client.get('/api/dossiers/DEMO_SLO_001').json
            self.assertEqual(len(d['saisies']),8)
            self.assertIn('FICTIF',d['remarques'])
            aut=client.get('/api/saisie/DEMO_SLO_001/autopsie').json
            for e in aut['etapes']:
                for c in e['champs']:
                    if c['id']=='foie_masse':c['grammes']=14.33
            self.assertEqual(client.post('/api/saisie',json=aut).status_code,200)
            neu=client.get('/api/saisie/DEMO_SLO_001/neuropath').json
            for e in neu['etapes']:
                for c in e['champs']:
                    if c['id']=='masse_enc':c['valeur']=38.75
                    elif c['id']=='masse_cerv':c['valeur']=2.19
            self.assertEqual(client.post('/api/saisie',json=neu).status_code,200)
            organes=client.get('/api/dossiers/DEMO_SLO_001/percentiles-organes').json
            self.assertEqual(next(l for l in organes['autopsie']['lignes'] if l['id']=='foie_masse')['percentile_gc'],50)
            self.assertTrue(all(l['percentile']==50 for l in organes['neuropath']['lignes']))
            placenta19=client.get('/api/dossiers/DEMO_SLO_001/percentiles-placenta').json['resultats']
            self.assertIsNone(placenta19['position_percentile'])
            self.assertIsNone(placenta19['percentile_exact'])
            for g in ('complet','synthese'):
                r=client.post('/api/dossiers/DEMO_SLO_001/cr',json={'gabarit':g})
                self.assertEqual(r.status_code,200,r.text);self.assertIn('P50,00',r.json['texte'])
            # Seule la copie temporaire du scénario est passée à 28 SA pour un cas positif Redline.
            admin=client.get('/api/saisie/DEMO_SLO_001/administratif').json
            admin['issue']['terme_sa']=28
            self.assertEqual(client.post('/api/saisie',json=admin).status_code,200)
            plac=client.get('/api/saisie/DEMO_SLO_001/macro_placenta').json
            plac['conditions_masse']='fraiche_paree'
            for sec in plac['sections']:
                if 'masse' in sec['champs']:sec['champs']['masse']=214
                if 'terme_sa' in sec['champs']:sec['champs']['terme_sa']=28
            self.assertEqual(client.post('/api/saisie',json=plac).status_code,200)
            self.assertEqual(client.get('/api/dossiers/DEMO_SLO_001/percentiles-placenta').json['resultats']['position_percentile'],'P50')
            for g in ('complet','synthese','placenta'):
                r=client.post('/api/dossiers/DEMO_SLO_001/cr',json={'gabarit':g})
                self.assertEqual(r.status_code,200,r.text)
                self.assertIn('214 g',r.json['texte']);self.assertIn('P50',r.json['texte'])
            autre=serveur.creer_app(base,ROOT).test_client()
            self.assertEqual(autre.get('/api/dossiers/DEMO_SLO_001').status_code,200)
            export=autre.get('/api/dossiers/DEMO_SLO_001/export.json')
            self.assertEqual(export.status_code,200);self.assertEqual(len(export.json['saisies']),8)
            self.assertEqual(fixture.read_bytes(),original)


if __name__=='__main__':unittest.main()
