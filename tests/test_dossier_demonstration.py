# SPDX-License-Identifier: CC-BY-NC-SA-4.0
import io
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

DEPOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEPOT / 'hub/app'))
import ingest
import serveur
from dossiers_portables import rapport_sur

PAQUET = DEPOT / 'hub/exemples/DEMO_SLO_001.json'
NUMERO = 'DEMO_SLO_001'


class DossierOrdinaire(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='monolithe-dossier-test-')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        ingest.arborescence(self.base)
        cx, _ = ingest.ouvrir(self.base / 'hub.sqlite')
        ingest.migrer(cx, DEPOT / 'hub/app/migrations', bavard=False)
        # Autre dossier entièrement fictif : sentinelle des tests, jamais un patient.
        doc = {'schema_version':'0.3.0','module':'administratif','module_version':'2.1.0',
               'dossier':'TEMOIN_TEST','operateur':'TEST','issue':{'terme_sa':28,'sexe':'F'},
               'identite':{'nom_mere':'SENTINELLE FICTIVE'}}
        ingest.ingerer(cx, self.base, json.dumps(doc).encode(), 'TEMOIN_TEST_administratif.json')
        cx.commit(); cx.close()
        self.client = serveur.creer_app(self.base, DEPOT).test_client()
        self.temoin = self.client.get('/api/dossiers/TEMOIN_TEST').json

    def importer(self, data=None):
        r = self.client.post('/api/deposer', data={'fichiers':(io.BytesIO(data or PAQUET.read_bytes()),'DEMO_SLO_001.json')})
        self.assertEqual(r.status_code, 200)
        return self.client.post('/api/ingerer').json

    def test_sources_conservees_et_paquet_reproductible(self):
        root=DEPOT/'hub/exemples/DEMO_SLO_001'
        provenance=json.loads((root/'provenance.json').read_text())
        for nom, sha in provenance['fichiers_conserves_sha256'].items():
            self.assertEqual(hashlib.sha256((root/nom).read_bytes()).hexdigest(),sha)
        resultat=subprocess.run([sys.executable,str(DEPOT/'hub/outils/preparer_dossier_slo.py')],capture_output=True,text=True)
        self.assertEqual(resultat.returncode,0,resultat.stderr)
        self.assertEqual(json.loads(PAQUET.read_text())['dossier'],NUMERO)

    def test_import_habituel_complet_idempotent_et_modifications_conservees(self):
        self.assertEqual(self.client.get('/api/dossiers/DEMO_SLO_001').status_code, 404)
        self.assertEqual(self.importer()['ingerees'], 1)
        dossier = self.client.get('/api/dossiers/DEMO_SLO_001').json
        self.assertEqual(len(dossier['saisies']), 8)
        self.assertEqual(dossier['remarques'], 'FICTIF – TEST – Smith-Lemli-Opitz')
        self.assertEqual(self.client.get('/api/dossiers/TEMOIN_TEST').json, self.temoin)
        bio = self.client.get('/api/saisie/DEMO_SLO_001/biometrie_clinique').json
        bio['mesures']['pied'] = 30.7
        self.assertEqual(self.client.post('/api/saisie',json=bio).status_code, 200)
        self.assertEqual(self.importer()['doublons'], 1)
        # Nouvelle application et nouvelle connexion, comme après un arrêt/redémarrage.
        autre = serveur.creer_app(self.base, DEPOT).test_client()
        self.assertEqual(autre.get('/api/saisie/DEMO_SLO_001/biometrie_clinique').json['mesures']['pied'], 30.7)
        self.assertEqual(len(autre.get('/api/dossiers/DEMO_SLO_001').json['saisies']), 8)
        self.assertEqual(len(autre.get('/api/dossiers/DEMO_SLO_001/cr').json), 2)

    def test_cr_corrige_historise_exporte_et_reimporte(self):
        self.importer()
        liste = self.client.get('/api/dossiers/DEMO_SLO_001/cr').json
        r = next(x for x in liste if x['gabarit']=='complet')
        avant = self.client.get('/api/cr/'+str(r['id'])).json
        self.assertIn('Smith-Lemli-Opitz', avant['texte'])
        texte = avant['texte'] + '<p>Correction fictive conservée après redémarrage.</p>'
        modifie = self.client.put('/api/cr/'+str(r['id']),json={'texte':texte,'operateur':'Codex'}).json
        self.assertNotEqual(modifie['id'],r['id'])
        self.assertEqual(self.client.get('/api/cr/'+str(r['id'])).json, avant)
        autre = serveur.creer_app(self.base, DEPOT).test_client()
        self.assertIn('Correction fictive',autre.get('/api/cr/'+str(modifie['id'])).json['texte'])
        export = autre.get('/api/dossiers/DEMO_SLO_001/export.json')
        self.assertEqual(export.status_code, 200)
        paquet = export.json
        self.assertEqual(len(paquet['saisies']),8)
        self.assertEqual(len(paquet['comptes_rendus']),3)
        self.assertTrue(any('Correction fictive' in r['texte'] for r in paquet['comptes_rendus']))
        # Suppression volontaire du seul dossier testé puis réimport explicite de son export.
        self.assertEqual(autre.delete('/api/dossiers/DEMO_SLO_001',json={'confirmation':NUMERO}).status_code,200)
        self.assertEqual(self.importer(export.data)['ingerees'],1)
        self.assertIn('Correction fictive',self.client.get('/api/dossiers/DEMO_SLO_001/export.json').text)

    def test_suppression_confirmee_sans_effet_sur_autres_dossiers_ni_recreation(self):
        self.importer()
        self.assertEqual(self.client.delete('/api/dossiers/DEMO_SLO_001',json={}).status_code,400)
        self.assertEqual(self.client.get('/api/dossiers/DEMO_SLO_001').status_code,200)
        self.assertEqual(self.client.delete('/api/dossiers/DEMO_SLO_001',json={'confirmation':NUMERO}).status_code,200)
        autre = serveur.creer_app(self.base, DEPOT).test_client()
        self.assertEqual(autre.get('/api/dossiers/DEMO_SLO_001').status_code,404)
        self.assertEqual(autre.get('/api/dossiers/TEMOIN_TEST').json,self.temoin)
        self.assertTrue(list((self.base/'archive'/NUMERO).rglob('*.json')))

    def test_import_invalide_atomique_et_html_sans_contenu_actif(self):
        paquet=json.loads(PAQUET.read_text())
        paquet['saisies'][1]['dossier']='AUTRE_TEST'
        self.assertEqual(self.importer(json.dumps(paquet).encode())['rejets'],1)
        self.assertEqual(self.client.get('/api/dossiers/DEMO_SLO_001').status_code,404)
        html=rapport_sur('<p onclick="bad()">texte<script>bad()</script><img src=x onerror="bad()"><span style="background:url(https://x);font-size:11pt">ok</span></p>','html')
        self.assertNotIn('bad()',html); self.assertNotIn('url(',html);self.assertNotIn('<img',html)
        self.assertIn('font-size:11pt',html)
        self.assertEqual(self.client.get('/api/dossiers/TEMOIN_TEST').json,self.temoin)

    def test_parcours_navigateur_toutes_rubriques_et_cr(self):
        from werkzeug.serving import make_server
        app=serveur.creer_app(self.base,DEPOT)
        http=make_server('127.0.0.1',0,app,threaded=True)
        thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        try:
            r=subprocess.run(['node',str(DEPOT/'tests/dossier_ordinaire_browser.cjs'),
                              f'http://127.0.0.1:{http.server_port}',str(PAQUET)],capture_output=True,text=True,timeout=180)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            print(r.stdout)
        finally:
            http.shutdown();http.server_close();thread.join(timeout=5)


if __name__=='__main__':
    unittest.main()
