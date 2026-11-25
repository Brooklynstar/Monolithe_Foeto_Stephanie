# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Migration des bases des deux branches et non-régression des reprises."""
import json
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / 'hub/app/migrations'
sys.path.insert(0, str(ROOT / 'hub/app'))
import ingest
from serveur import creer_app


class IntegrationBordeaux(unittest.TestCase):
    def test_migrations_fraiche_et_deux_historiques(self):
        for origine in ('neuve', 'bordeaux', 'remi'):
            with self.subTest(origine=origine), TemporaryDirectory() as temporaire:
                base = Path(temporaire)
                cx, _ = ingest.ouvrir(base / 'hub.sqlite')
                with cx:
                    if origine != 'neuve':
                        anciennes = base / 'migrations-anciennes'
                        anciennes.mkdir()
                        for fichier in MIGRATIONS.glob('000[1-7]_*.sql'):
                            shutil.copyfile(fichier, anciennes / fichier.name)
                        if origine == 'bordeaux':
                            for numero in ('0008_conclusions_cliniques.sql', '0009_trame_normale.sql'):
                                shutil.copyfile(MIGRATIONS / numero, anciennes / numero)
                        else:
                            shutil.copyfile(MIGRATIONS / '0010_macro_refaite.sql',
                                            anciennes / '0008_macro_refaite.sql')
                        ingest.migrer(cx, anciennes, bavard=False)
                        cx.execute("INSERT INTO dossiers(numero) VALUES ('TEST-BORDEAUX')")
                        if origine == 'bordeaux':
                            cx.execute("INSERT INTO conclusions_cliniques(dossier, texte) VALUES "
                                       "('TEST-BORDEAUX', 'Conclusion de test.')")
                        else:
                            cx.execute("UPDATE dossiers SET macro_refaite='fixee' "
                                       "WHERE numero='TEST-BORDEAUX'")
                    ingest.migrer(cx, MIGRATIONS, bavard=False)
                    self.assertEqual(ingest.migrer(cx, MIGRATIONS, bavard=False), [])
                    self.assertEqual(cx.execute('PRAGMA quick_check').fetchone()[0], 'ok')
                    self.assertEqual(cx.execute('SELECT COUNT(*) FROM trame_normale').fetchone()[0], 0)
                    self.assertIn('macro_refaite', [c[1] for c in cx.execute('PRAGMA table_info(vue_dossiers)')])
                    if origine == 'bordeaux':
                        self.assertEqual(cx.execute('SELECT texte FROM conclusions_cliniques').fetchone()[0],
                                         'Conclusion de test.')
                    if origine == 'remi':
                        self.assertEqual(cx.execute('SELECT macro_refaite FROM vue_dossiers').fetchone()[0], 'fixee')
                cx.close()

    def test_grilles_placentaires_et_export_plus_ancien(self):
        with TemporaryDirectory() as temporaire:
            base = Path(temporaire)
            ingest.arborescence(base)
            cx, _ = ingest.ouvrir(base / 'hub.sqlite')
            ingest.migrer(cx, MIGRATIONS, bavard=False)
            dossier = 'TEST-BORDEAUX'
            try:
                for module in ingest.MODULES_MICRO_PLACENTA:
                    doc = dict(module=module, module_version='1.0.0', schema_version='0.3.0',
                               dossier=dossier, grille={'libre': 'Contrôle des grilles.'})
                    ingest.ingerer(cx, base, json.dumps(doc).encode(), f'{dossier}_{module}.json')
                    self.assertEqual(ingest.slot(module), 'microscopie')

                def reprendre(exported_at, terme, provenance='telephone'):
                    doc = dict(module='administratif', module_version='2.1.0', schema_version='0.3.0',
                               dossier=dossier, exported_at=exported_at, issue={'terme_sa': terme})
                    return ingest.ingerer(cx, base, json.dumps(doc).encode(),
                                           f'{dossier}_administratif.json', provenance=provenance)

                reprendre('2026-01-01T10:00:00Z', 20)
                _, message, _ = reprendre('2026-01-01T10:30:00+01:00', 19)
                self.assertIn('rangé à l\'historique', message)
                self.assertEqual(cx.execute('SELECT terme_sa FROM vue_dossiers').fetchone()[0], 20)
                reprendre('2026-01-01T09:00:00Z', 21, 'poste')
                self.assertEqual(cx.execute('SELECT terme_sa FROM vue_dossiers').fetchone()[0], 21)
                cx.commit()
                ingest.reindexer(cx, bavard=False)
                self.assertEqual(cx.execute('SELECT terme_sa FROM vue_dossiers').fetchone()[0], 21)
            finally:
                cx.close()
            client = creer_app(base, ROOT).test_client()
            self.assertEqual(client.put(f'/api/dossiers/{dossier}', json={'macro_refaite': 'fixee'}).status_code, 200)
            self.assertEqual(client.get(f'/api/dossiers/{dossier}/export.json').get_json()['macro_refaite'], 'fixee')
            rendu = client.post(f'/api/dossiers/{dossier}/cr', json={'gabarit': 'complet'}).get_json()['texte']
            self.assertNotIn('Contrôle des grilles.', rendu)
