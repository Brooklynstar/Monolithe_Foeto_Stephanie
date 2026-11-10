# SPDX-License-Identifier: CC-BY-NC-SA-4.0
import json
import math
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest

DEPOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEPOT / 'hub/outils'))
import demonstration_slo as demo


class Demonstration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='demo-slo-test-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name) / 'base'
        demo.preparer(self.base)
        self.client = demo.application(self.base).test_client()

    def test_idempotence_calculs_et_exports_reproductibles(self):
        def comptes():
            with sqlite3.connect(self.base / 'hub.sqlite') as cx:
                return [cx.execute('SELECT count(*) FROM ' + t).fetchone()[0]
                        for t in ('dossiers', 'saisies', 'comptes_rendus')]
        avant = self.client.get('/demonstration/export.json').json
        self.assertEqual(comptes(), [1, 8, 2])
        demo.preparer(self.base)
        self.assertEqual(comptes(), [1, 8, 2])
        self.assertEqual(self.client.get('/demonstration/export.json').json, avant)
        for p in demo.SOURCES.glob('*.json'):
            source = json.loads(p.read_text())
            self.assertTrue(source['fictif'])
            self.assertEqual(source['operateur'], 'Codex')
            self.assertNotIn('percentiles', source)
            self.assertNotIn('ecarts', source)
        bio = next(d for d in avant['saisies'] if d['module'] == 'biometrie_clinique')
        self.assertIsNone(bio['mesures']['dici'])
        signes = set()
        for cle, sources in bio['ecarts_non_arrondis'].items():
            for src, z in sources.items():
                if z is not None:
                    self.assertAlmostEqual(bio['percentiles'][cle][src], 50 * math.erfc(-z/math.sqrt(2)), places=12)
                    signes.add(0 if abs(z) < .01 else (1 if z > 0 else -1))
        self.assertEqual(signes, {-1, 0, 1})
        cx, _ = demo.ingest.ouvrir(self.base / 'hub.sqlite')
        try:
            ctx = demo.cr.contexte(cx, demo.NUMERO, demo.biometrie.References(self.base), demo.ingest.ORDRE_MODULES)
            self.assertEqual(ctx['manquants'], [])
            for ligne in ctx['biometrie']['lignes']:
                for src in ('gc','ma','mb'):
                    self.assertEqual(ligne['percentile_'+src], bio['percentiles'][ligne['cle']][src.upper()])
        finally:
            cx.close()

    def test_reinitialisation_uniquement_de_la_base_fictive(self):
        with sqlite3.connect(self.base / 'hub.sqlite') as cx:
            cx.execute("UPDATE dossiers SET remarques='Essai modifié' WHERE numero=?", (demo.NUMERO,))
        demo.preparer(self.base, reinitialiser=True)
        with sqlite3.connect(self.base / 'hub.sqlite') as cx:
            self.assertEqual(cx.execute('SELECT count(*) FROM dossiers').fetchone()[0], 1)
            self.assertEqual(cx.execute('SELECT count(*) FROM saisies').fetchone()[0], 8)
            self.assertEqual(cx.execute('SELECT count(*) FROM comptes_rendus').fetchone()[0], 2)
            self.assertIn('DÉMONSTRATION', cx.execute('SELECT remarques FROM dossiers').fetchone()[0])

    def test_refus_base_non_marquee_et_base_avec_autre_dossier(self):
        clinique = Path(self.temp.name) / 'clinique'
        clinique.mkdir()
        (clinique / 'hub.sqlite').write_bytes(b'BASE CLINIQUE A NE PAS TOUCHER')
        with self.assertRaises(ValueError):
            demo.preparer(clinique, reinitialiser=True)
        self.assertEqual((clinique / 'hub.sqlite').read_bytes(), b'BASE CLINIQUE A NE PAS TOUCHER')
        self.assertEqual(len(list(clinique.iterdir())), 1)
        with sqlite3.connect(self.base / 'hub.sqlite') as cx:
            cx.execute("INSERT INTO dossiers(numero) VALUES ('DOSSIER_INTERDIT')")
        avant = (self.base / 'hub.sqlite').read_bytes()
        with self.assertRaises(ValueError):
            demo.preparer(self.base)
        self.assertEqual((self.base / 'hub.sqlite').read_bytes(), avant)

    def test_comptes_rendus_generes_et_conclusion_hypothese(self):
        for g in ('complet', 'synthese'):
            r = self.client.post('/api/dossiers/DEMO_SLO_001/cr', json={'gabarit':g,'operateur':'Codex'})
            self.assertEqual(r.status_code, 200)
            texte = r.json['texte']
            for terme in ('CAS ENTIÈREMENT FICTIF', 'Constatations morphologiques', 'évoque un syndrome',
                          'sans permettre de l’affirmer', 'DHCR7', 'P50,00'):
                self.assertIn(terme, texte)
            self.assertNotIn('À rédiger.', texte)
            self.assertNotIn('Modules non parvenus', texte)
        self.assertIn('Exporter le dossier JSON', self.client.get('/').text)

    def test_parcours_navigateur_hub_et_modules(self):
        from werkzeug.serving import make_server
        http = make_server('127.0.0.1', 0, demo.application(self.base), threaded=True)
        thread = threading.Thread(target=http.serve_forever, daemon=True)
        thread.start()
        try:
            r = subprocess.run(['node', str(DEPOT / 'tests/demo_slo_browser.cjs'),
                                f'http://127.0.0.1:{http.server_port}'], capture_output=True, text=True, timeout=90)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            print(r.stdout)
        finally:
            http.shutdown()
            http.server_close()
            thread.join(timeout=5)


if __name__ == '__main__':
    unittest.main()
