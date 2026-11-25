# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Parcours Chrome des deux configurations BCBA sur une base isolée."""
from html import escape
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from threading import Thread
import unittest

from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'hub/app'), str(ROOT / 'hub/outils')]
from importer_placenta_demo import importer
from serveur import creer_app


class PlacentaGemellaire(unittest.TestCase):
    def test_bcba_navigation_reouverture_et_compte_rendu(self):
        with TemporaryDirectory(prefix='placenta-gemellaire-') as temporaire:
            base = Path(temporaire)
            importer(base)
            serveur = make_server('127.0.0.1', 0, creer_app(base, ROOT))
            thread = Thread(target=serveur.serve_forever, daemon=True)
            thread.start()
            try:
                self.verifier(f'http://127.0.0.1:{serveur.server_port}')
            finally:
                serveur.shutdown()
                thread.join()
                serveur.server_close()

    def verifier(self, url):
        with sync_playwright() as pw:
            executable = os.environ.get('MONOLITHE_CHROMIUM')
            options = {'executable_path': executable} if executable else {}
            browser = pw.chromium.launch(**options)
            page = browser.new_page()
            erreurs = []
            page.on('pageerror', lambda e: erreurs.append(str(e)))
            page.goto(url + '/?dossier=DEMO_SLO_001')
            onglet = page.locator('[data-o=m_placenta] + [data-o=m_placenta_gemellaire]')
            self.assertEqual(onglet.inner_text(), 'Placenta gémellaire')
            onglet.click()
            self.assertIn('/modules/placenta_gemellaire', page.get_by_role('link', name='Le saisir maintenant').get_attribute('href'))

            for configuration, suffixe in [('bcba_separes', 'SEPARES'), ('bcba_fusionnes', 'FUSIONNES')]:
                with self.subTest(configuration=configuration):
                    numero = f'DEMO-JUMEAUX-{suffixe}'
                    fusionnes = configuration == 'bcba_fusionnes'
                    page.goto(f'{url}/modules/placenta_gemellaire?dossier={numero}&operateur=TEST')
                    page.locator('#configuration:enabled').wait_for()
                    selecteur = page.locator('#configuration')
                    self.assertEqual(selecteur.locator('option[value]:not([value=""])').all_text_contents(),
                                     ['BCBA / PP séparés', 'BCBA / PP fusionnés', 'MCBA', 'MCMA'])
                    for future in ('mcba', 'mcma'):
                        selecteur.select_option(future)
                        self.assertEqual(page.locator('section h2').all_text_contents(),
                                         ['Macroscopie', 'Microscopie', 'Conclusion'])
                        self.assertEqual(page.locator('#p1_macro_01').count(), 0)
                    selecteur.select_option(configuration)
                    for i in (1, 2):
                        page.locator(f'#p{i}_macro_01').fill(str(i * 100))
                    page.locator('#p1_micro_01_2').check()
                    page.locator('#p2_micro_01_5').check()
                    if fusionnes:
                        self.assertEqual(page.locator('#macroscopie h3').all_text_contents(),
                                         ['Ensemble placentaire', 'Placenta 1', 'Placenta 2'])
                        for identifiant, v in {'ensemble_poids': '355', 'ensemble_longueur': '26',
                                              'ensemble_largeur': '19', 'ensemble_epaisseur': '2.6',
                                              'ensemble_distance': '8.5', 'p1_pourcentage': '40',
                                              'p2_pourcentage': '60'}.items():
                            page.locator('#' + identifiant).fill(v)
                        for i in (1, 2):
                            membrane = page.locator(f'#p{i}_micro_02_bichoriale')
                            self.assertTrue(membrane.is_checked())
                            self.assertEqual(membrane.locator('..').evaluate('(e) => getComputedStyle(e).color'),
                                             'rgb(14, 107, 98)')
                        page.locator('#p2_micro_02_bichoriale').uncheck()
                    else:
                        self.assertEqual(page.locator('#ensemble_poids').count(), 0)
                        self.assertEqual(page.locator('.bichoriale').count(), 0)

                    conclusion = page.locator('#conclusion')
                    conclusion.get_by_label('hypotrophique', exact=True).check()
                    conclusion.get_by_label('eutrophique', exact=True).check()
                    conclusion.get_by_label('hypotrophique', exact=True).uncheck()
                    conclusion.get_by_label('des lésions de malperfusion vasculaire maternelle', exact=True).check()
                    conclusion.get_by_label('légères', exact=True).check()
                    conclusion.get_by_label('des lésions de villite chronique', exact=True).check()
                    conclusion.get_by_label('de bas grade multifocale', exact=True).check()
                    with page.expect_response(lambda r: r.url.endswith('/api/saisie') and r.request.method == 'POST') as response:
                        page.locator('#hubSave').click()
                    self.assertEqual(response.value.status, 200, response.value.text())
                    page.reload()
                    page.locator('#configuration:enabled').wait_for()
                    self.assertEqual(selecteur.input_value(), configuration)
                    self.assertEqual(page.locator('#p1_macro_01').input_value(), '100')
                    self.assertEqual(page.locator('#p2_macro_01').input_value(), '200')
                    self.assertTrue(page.locator('#p1_micro_01_2').is_checked())
                    self.assertTrue(page.locator('#p2_micro_01_5').is_checked())
                    self.assertFalse(page.locator('#p2_micro_01_2').is_checked())
                    for v in ('eutrophique', 'légères', 'de bas grade multifocale'):
                        self.assertTrue(conclusion.get_by_label(v, exact=True).is_checked())
                    self.assertFalse(conclusion.get_by_label('hypotrophique', exact=True).is_checked())
                    if fusionnes:
                        self.assertTrue(page.locator('#p1_micro_02_bichoriale').is_checked())
                        self.assertFalse(page.locator('#p2_micro_02_bichoriale').is_checked())
                        self.assertEqual(page.locator('#ensemble_distance').input_value(), '8.5')
                        self.assertEqual(page.locator('#p1_pourcentage').input_value(), '40')
                        self.assertEqual(page.locator('#p2_pourcentage').input_value(), '60')

                    page.goto(f'{url}/?dossier={numero}')
                    page.locator('[data-o=cr]').click()
                    page.locator('#crGabarit option[value=placenta_gemellaire]').wait_for(state='attached')
                    page.locator('#crGabarit').select_option('placenta_gemellaire')
                    page.get_by_role('button', name='Produire un brouillon').click()
                    page.locator('#crPre').wait_for()
                    texte = page.locator('#crPre').inner_text()
                    prefixe = 'fusionnés' if fusionnes else 'séparés'
                    self.assertIn(f'Conclusion\nPlacenta gémellaire bichorial biamniotique à placentas {prefixe}.', texte)
                    for ligne in ('Placenta 1\nLe placenta pèse 100 g.', 'Placenta 2\nLe placenta pèse 200 g.',
                                  'Placenta 1\nL’amnios est cubique.', 'Placenta 2\nL’amnios est exfolié.',
                                  'Le placenta est eutrophique.', 'malperfusion vasculaire maternelle (légères).',
                                  'villite chronique (de bas grade multifocale).'):
                        if fusionnes and ligne.startswith('Placenta 1\nL’amnios'):
                            self.assertIn('Placenta 1\nLa membrane est de type bichorial.\nL’amnios est cubique.', texte)
                        else:
                            self.assertIn(ligne, texte)
                    self.assertNotIn('hypotrophique', texte)
                    if fusionnes:
                        for mention in ('355 g', '26 cm', '19 cm', '2,6 cm', '40 %', '60 %', '8,5 cm'):
                            self.assertIn(mention, texte)
                        self.assertEqual(texte.count('La membrane est de type bichorial.'), 1)
                    else:
                        self.assertNotIn('de type bichorial', texte)
                    placenta_simple = page.request.post(f'{url}/api/saisie', data={
                        'module': 'placenta', 'module_version': '1.1.0', 'schema_version': '0.1.0',
                        'dossier': numero, 'operateur': 'TEST',
                        'sections': [{'id': 'macroscopie', 'champs': {'macro_01': 999}}],
                    })
                    self.assertTrue(placenta_simple.ok, placenta_simple.text())
                    complet = page.request.post(f'{url}/api/dossiers/{numero}/cr', data={'gabarit': 'complet'})
                    self.assertTrue(complet.ok)
                    texte_complet = complet.json()['texte']
                    self.assertIn('>Placenta</h2>', texte_complet)
                    self.assertNotIn('999 g', texte_complet)
                    for attendu in (f'Placenta gémellaire bichorial biamniotique à placentas {prefixe}.',
                                    'Le placenta pèse 100 g.', 'Le placenta pèse 200 g.', 'Le placenta est eutrophique.'):
                        self.assertIn(escape(attendu), texte_complet)
            self.assertEqual(erreurs, [])
            browser.close()
