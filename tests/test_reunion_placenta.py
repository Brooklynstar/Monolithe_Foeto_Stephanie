# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Fusion : dossier SLO exact, deux modules placenta, vrai serveur sur 5005."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'hub/outils'))
from verifier_placenta import schema_placenta, verifier_preservation_releve

PORT = int(os.environ.get('MONOLITHE_TEST_PORT', '5005'))
URL = f'http://127.0.0.1:{PORT}'


class ReunionPlacenta(unittest.TestCase):
    def test_import_exact_deux_modules_persistance_et_percentiles(self):
        fixture = ROOT / 'hub/exemples/DEMO_SLO_001.json'
        original = fixture.read_bytes()
        source = json.loads(original)
        with tempfile.TemporaryDirectory(prefix='reunion-placenta-') as td:
            base = Path(td) / 'hub'
            with (Path(td) / 'serveur.log').open('w+') as log:
                def start():
                    proc = subprocess.Popen(
                        [sys.executable, '-u', str(ROOT / 'hub/app/serveur.py'),
                         '--base', str(base), '--port', str(PORT)],
                        cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                    for _ in range(150):
                        if proc.poll() is not None:
                            break
                        try:
                            with urlopen(URL + '/api/etat', timeout=.3) as r:
                                if json.load(r)['racine'] == str(base.resolve()):
                                    return proc
                        except OSError:
                            pass
                        time.sleep(.05)
                    if proc.poll() is None:
                        proc.terminate()
                        proc.wait(timeout=5)
                    log.seek(0)
                    self.fail(f'Serveur {PORT} indisponible : ' + log.read())

                def stop(proc):
                    if proc.poll() is None:
                        proc.terminate()
                        proc.wait(timeout=5)

                proc = start()
                try:
                    with sync_playwright() as pw:
                        executable = os.environ.get('MONOLITHE_CHROMIUM')
                        browser = pw.chromium.launch(**({'executable_path': executable} if executable else {}))
                        context = browser.new_context()
                        page = context.new_page()
                        errors = []
                        page.on('pageerror', lambda e: errors.append(str(e)))
                        page.goto(URL)
                        page.locator('[data-page=ingestion]').click()
                        with page.expect_response(lambda r: r.url.endswith('/api/ingerer')) as response:
                            page.locator('#pickDepot').set_input_files(str(fixture))
                        self.assertEqual(response.value.status, 200)
                        self.assertEqual(response.value.json()['ingerees'], 1)
                        dossier = context.request.get(URL + '/api/dossiers/DEMO_SLO_001').json()
                        self.assertEqual(len(dossier['saisies']), 8)
                        cr_initial = context.request.get(URL + '/api/dossiers/DEMO_SLO_001/cr').json()
                        self.assertEqual(len(cr_initial), 2)
                        self.assertEqual((dossier['terme_sa'], dossier['type_issue']), (19, 'IMG'))
                        before = {s['module']: context.request.get(URL + '/api/saisie/DEMO_SLO_001/' + s['module']).json() for s in source['saisies']}
                        self.assertEqual(before, {s['module']: s for s in source['saisies']})
                        print('OK import du fichier exact : huit modules et deux CR historiques')
                        page.goto(URL + '/?dossier=DEMO_SLO_001')
                        page.locator('[data-o=m_placenta]').wait_for()
                        self.assertEqual(page.locator('[data-o=m_placenta]').inner_text().strip(), 'Placenta')
                        self.assertEqual(page.locator('[data-o=m_macro_placenta]').count(), 1)
                        page.locator('#operateur').fill('TEST')
                        page.locator('[data-o=m_placenta]').click()
                        link = page.get_by_role('link', name='Le saisir maintenant')
                        page.goto(URL + link.get_attribute('href'))
                        page.wait_for_function('numeroCharge === "DEMO_SLO_001" && !charge')
                        self.assertEqual(page.locator('#sections section h2').evaluate_all('(hs)=>hs.map(h=>[...h.childNodes].filter(n=>n.nodeType===Node.TEXT_NODE).map(n=>n.textContent).join("").trim())'), ['Macroscopie', 'Microscopie', 'Conclusion'])
                        rendu = page.evaluate('SECTIONS.map(s=>[s.titre,s.champs.map(c=>[c.label,c.type,c.choix])])')
                        verifier_preservation_releve()
                        self.assertEqual(rendu, schema_placenta())
                        self.assertEqual(page.locator('fieldset').count(), sum(len(champs) for _, champs in schema_placenta()))
                        self.assertEqual(page.locator('label.chip input').count(), sum(len(options) for _, champs in schema_placenta() for _, _, options in champs))
                        page.locator('#macro_01').fill('90')
                        page.locator('#macro_08_4').check()
                        page.locator('#macro_08_autre').fill('Essai de fusion — fictif')
                        page.locator('#micro_01_0').check()
                        page.locator('#micro_02_0').check()
                        page.locator('#conclusion_01_1').check()
                        with page.expect_response(lambda r: r.url.endswith('/api/saisie') and r.request.method == 'POST') as response:
                            page.locator('#hubSave').click()
                        self.assertEqual(response.value.status, 200, response.value.text())
                        saved = context.request.get(URL + '/api/saisie/DEMO_SLO_001/placenta').json()
                        print('OK deux onglets accessibles ; trame étendue conforme ; trois sections enregistrées')
                        # Fermeture du navigateur et arrêt du vrai processus : relire uniquement depuis SQLite.
                        context.close()
                        browser.close()
                        stop(proc)
                        proc = start()
                        browser = pw.chromium.launch(**({'executable_path': executable} if executable else {}))
                        context = browser.new_context()
                        page = context.new_page()
                        page.on('pageerror', lambda e: errors.append(str(e)))
                        page.goto(URL + '/?dossier=DEMO_SLO_001')
                        page.locator('[data-o=m_placenta]').click()
                        page.goto(URL + page.get_by_role('link', name='Rouvrir ce module').get_attribute('href'))
                        page.wait_for_function('numeroCharge === "DEMO_SLO_001" && !charge')
                        self.assertEqual(page.locator('#macro_01').input_value(), '90')
                        self.assertEqual(page.locator('#macro_08_autre').input_value(), 'Essai de fusion — fictif')
                        self.assertTrue(page.locator('#micro_01_0').is_checked())
                        self.assertTrue(page.locator('#micro_02_0').is_checked())
                        self.assertTrue(page.locator('#conclusion_01_1').is_checked())
                        self.assertEqual(context.request.get(URL + '/api/saisie/DEMO_SLO_001/placenta').json(), saved)
                        self.assertEqual(context.request.get(URL + '/api/dossiers/DEMO_SLO_001/cr').json(), cr_initial)
                        for module, doc in before.items():
                            self.assertEqual(context.request.get(URL + '/api/saisie/DEMO_SLO_001/' + module).json(), doc, module)
                        print('OK après redémarrage sur 5005 : trois sections et huit saisies préexistantes identiques')
                        page.goto(URL + '/?dossier=DEMO_SLO_001')
                        page.locator('#operateur').fill('TEST')
                        page.locator('[data-o=m_macro_placenta]').click()
                        page.goto(URL + page.get_by_role('link', name='Rouvrir ce module').get_attribute('href'))
                        page.wait_for_function('document.getElementById("f_masse").value === "90"')
                        self.assertEqual(page.locator('#f_terme_sa').input_value(), '19')
                        self.assertEqual(page.locator('#f_grand_axe').input_value(), '9')
                        self.assertEqual(page.locator('#f_cordon_longueur').input_value(), '22')
                        self.assertIn('22–42 SA', page.locator('#resultatsPercentilesPlacenta').inner_text())
                        result = context.request.get(URL + '/api/dossiers/DEMO_SLO_001/percentiles-placenta').json()['resultats']
                        self.assertIsNone(result['position_percentile'])
                        self.assertIsNone(result['percentile_exact'])
                        print('OK Macro placenta SLO : 90 g, 19 SA, axes et cordon retrouvés ; hors plage Redline signalé')
                        # Cas positif distinct : le terme et les données SLO restent inchangés.
                        page.goto(URL + '/modules/macro_placenta?dossier=TEST-PCT-028&operateur=TEST')
                        page.wait_for_function('dossier === "TEST-PCT-028"')
                        page.get_by_role('button', name='Activer la saisie').click()
                        page.locator('#f_terme_sa').fill('28')
                        page.locator('#f_masse').fill('214')
                        page.locator('#conditions_masse').select_option('fraiche_paree')
                        page.wait_for_function('document.getElementById("resultatsPercentilesPlacenta").textContent.includes("P50")')
                        result = page.evaluate('PlacentaPercentiles.calculer(28,214,"fraiche_paree")')
                        self.assertEqual(result['position_percentile'], 'P50')
                        self.assertIsNone(result['percentile_exact'])
                        self.assertAlmostEqual(result['z_brut'], (214 - 223) / 66)
                        with page.expect_response(lambda r: r.url.endswith('/api/saisie') and r.request.method == 'POST') as response:
                            page.locator('#hubSave').click()
                        self.assertEqual(response.value.status, 200)
                        backend = context.request.get(URL + '/api/dossiers/TEST-PCT-028/percentiles-placenta').json()['resultats']
                        self.assertEqual(backend, result)
                        page.locator('#conditions_masse').select_option('fixe')
                        self.assertNotIn('Position percentile', page.locator('#resultatsPercentilesPlacenta').inner_text())
                        self.assertEqual(context.request.get(URL + '/api/saisie/DEMO_SLO_001/macro_placenta').json(), before['macro_placenta'])
                        self.assertEqual(fixture.read_bytes(), original)
                        self.assertEqual(errors, [])
                        print('OK calcul navigateur/API : 28 SA, 214 g = P50 ; poids fixé exclu ; SLO et fichier source inchangés ; aucune erreur JS')
                        browser.close()
                finally:
                    stop(proc)


if __name__ == '__main__':
    unittest.main()
