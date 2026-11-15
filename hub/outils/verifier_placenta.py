#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-NC-SA-4.0 | Hub Light | Monolithe_Foeto
"""Test navigateur + SQLite isolé. pip install flask pillow playwright
python -m playwright install chromium
python hub/outils/verifier_placenta.py [--chromium /chemin/chromium]
Aucune base locale n'est ouverte : une fixture fictive est créée, puis copiée.
"""
import argparse
import json
import re
import shutil
import sqlite3
import sys
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'hub/app'))
import ingest
from serveur import creer_app


def schema_releve():
    """Parse indépendant du HTML : ordre, types, libellés et choix du relevé."""
    texte = (ROOT / 'docs/placenta_releve.md').read_text(encoding='utf-8')
    sections = []
    macro, micro, conclusion = re.split(r'## (?:19|20)\.[^\n]*\n', texte)
    champs = []
    for line in macro.splitlines():
        if line.startswith('| ') and not line.startswith('| Champ'):
            label, typ, choix = [v.strip() for v in line.strip('|').split('|')]
            champs.append((label, 'texte' if typ == 'Réponse courte' else 'unique', choix.split(' / ') if choix else []))
    sections.append(('Macroscopie', champs))
    for titre, texte in [('Microscopie', micro), ('Conclusion', conclusion)]:
        champs = []
        for line in texte.splitlines():
            if line.startswith('### '):
                champs.append((line[4:], 'unique', []))
            elif line.startswith('- '):
                champs[-1][2].append(line[2:])
        sections.append((titre, champs))
    return sections


def enveloppe(module, schema, **payload):
    return dict(module=module, schema_version=schema, module_version='1.0.0',
                dossier='DEMO_SLO_001', operateur='TEST',
                exported_at='2026-11-15T00:00:00Z', **payload)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--chromium')
    args = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix='monolithe-placenta-') as td:
        source, base = Path(td) / 'source_fictive', Path(td) / 'copie_test'
        ingest.arborescence(source)
        cx, _ = ingest.ouvrir(source / 'hub.sqlite')
        ingest.migrer(cx, ROOT / 'hub/app/migrations', bavard=False)
        admin = enveloppe('administratif', '0.3.0',
                          identite={'nom_mere': 'DEMONSTRATION FICTIVE'},
                          issue={'terme_sa': 19, 'terme_j': 0, 'type_issue': 'IMG',
                                 'indication': 'Smith-Lemli-Opitz'},
                          prenatal={'note_test': 'Donnée préexistante à conserver'})
        ancien = enveloppe('macro_placenta', '0.2.0',
                           sections=[{'id': 'paree', 'champs': {'masse': 110}}])
        initial = enveloppe('placenta', '0.1.0', note_existante='à conserver', sections=[
            {'id': 'macroscopie', 'titre': 'Macroscopie', 'champs': {'macro_02': '10', 'champ_futur': 'conservé'}},
            {'id': 'microscopie', 'titre': 'Microscopie', 'champs': {'micro_01': 'aplati'}},
            {'id': 'conclusion', 'titre': 'Conclusion', 'champs': {'conclusion_01': 'eutrophique'}}])
        for doc in [admin, ancien, initial]:
            ingest.ingerer(cx, source, json.dumps(doc, ensure_ascii=False).encode(),
                           f"{doc['dossier']}_{doc['module']}.json", provenance='poste')
        cx.commit()
        # Copie SQLite cohérente + archives : seule cette copie sera modifiée.
        base.mkdir()
        cible = sqlite3.connect(base / 'hub.sqlite')
        cx.backup(cible)
        cible.close()
        shutil.copytree(source / 'archive', base / 'archive')
        cx.close()
        ingest.arborescence(base)
        app = creer_app(base, ROOT)
        serveur = make_server('127.0.0.1', 5005, app)
        thread = threading.Thread(target=serveur.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as p:
                options = {'headless': True}
                if args.chromium:
                    options['executable_path'] = args.chromium
                    options['args'] = ['--no-sandbox']
                browser = p.chromium.launch(**options)
                context = browser.new_context()
                page = context.new_page()
                erreurs = []
                page.on('pageerror', lambda e: erreurs.append(str(e)))
                url = 'http://127.0.0.1:5005'
                module = context.request.get(url + '/api/modules').json()['placenta']
                assert module['ingerable'] is True
                assert (module['module'], module['schema_version'], module['module_version']) == ('placenta', '0.1.0', '1.0.0')
                page.goto(url + '/?dossier=DEMO_SLO_001')
                page.locator('[data-o="m_placenta"]').wait_for()
                assert page.locator('[data-o="m_placenta"]').inner_text().strip() == 'Placenta'
                page.locator('[data-o="m_placenta"]').click()
                lien = page.get_by_role('link', name='Rouvrir ce module')
                assert '/modules/placenta?dossier=DEMO_SLO_001' in lien.get_attribute('href')
                # Aucune initiale dans l'URL : la saisie doit être relue quand même.
                page.goto(url + lien.get_attribute('href'))
                page.wait_for_function('numeroCharge === "DEMO_SLO_001" && !charge')
                assert page.locator('#operateur').input_value() == 'TEST'
                assert page.locator('#macro_02').input_value() == '10'
                assert page.locator('input[name=micro_01]:checked').input_value() == 'aplati'
                assert page.locator('input[name=conclusion_01]:checked').input_value() == 'eutrophique'
                print('OK navigation dossier et ouverture des trois sections déjà renseignées')
                rendu = page.evaluate('SECTIONS.map(s=>[s.titre,s.champs.map(c=>[c.label,c.type,c.choix])])')
                attendu = json.loads(json.dumps(schema_releve(), ensure_ascii=False))
                assert rendu == attendu, 'Divergence du relevé'
                assert page.locator('fieldset').count() == 32
                assert page.locator('input[type=radio]').count() == 155
                assert page.locator('[required]').count() == 0
                for s, champs in attendu:
                    for label, typ, choix in champs:
                        group = page.get_by_role('group', name=label, exact=True)
                        assert group.count() == 1
                        if typ == 'texte':
                            assert group.locator('input[type=text]').count() == 1
                        else:
                            assert group.locator('input[type=radio]').evaluate_all('(rs)=>rs.map(r=>r.value)') == choix
                            assert group.locator('input[type=radio]:checked').count() <= 1
                print('OK comparaison intégrale : 32 champs, 155 choix, ordre, types, intitulés et facultativité')
                # Un effacement précoce ne doit pas être annulé par une seconde reprise différée.
                page.locator('#macro_02').fill('')
                page.wait_for_timeout(900)
                assert page.locator('#macro_02').input_value() == ''
                page.locator('#macro_02').fill('10')
                print('OK effacement après ouverture sans reprise différée des anciennes valeurs')
                # Vérifier unicité, effacement, option fixe « autre » vs Other natif.
                cordon = page.get_by_role('group', name='Cordon', exact=True)
                cordon.get_by_label('Autre + texte libre', exact=True).check()
                cordon.get_by_role('textbox').fill('Insertion fictive — test libre')
                page.get_by_role('group', name="Cordon d'insertion", exact=True).get_by_label('autre', exact=True).check()
                assert page.get_by_role('group', name="Cordon d'insertion", exact=True).get_by_role('textbox').count() == 0
                amnios = page.get_by_role('group', name='Amnios', exact=True)
                amnios.get_by_label('cubique', exact=True).check()
                amnios.get_by_label('exfolié', exact=True).check()
                assert amnios.locator('input:checked').count() == 1
                amnios.get_by_role('button', name='Effacer : Amnios', exact=True).click()
                assert amnios.locator('input:checked').count() == 0
                amnios.get_by_label('aplati', exact=True).check()
                page.locator('#macro_01').fill('125,5')
                page.locator('#micro_02_0').check()
                page.locator('#conclusion_01_0').check()
                with page.expect_response(lambda r: r.url.endswith('/api/saisie') and r.request.method == 'POST') as r:
                    page.locator('#hubSave').click()
                assert r.value.status == 200, r.value.text()
                sauvegarde = context.request.get(url + '/api/saisie/DEMO_SLO_001/placenta').json()
                assert sauvegarde['sections'][0]['champs']['macro_08'] == {'choix': 'Autre + texte libre', 'texte': 'Insertion fictive — test libre'}
                assert sauvegarde['sections'][0]['champs']['macro_02'] == '10'
                assert sauvegarde['sections'][0]['champs']['champ_futur'] == 'conservé'
                assert sauvegarde['note_existante'] == 'à conserver'
                # Fermer tout le contexte : aucune mémoire navigateur ne peut masquer un défaut de base.
                page.close()
                context.close()
                context = browser.new_context()
                page = context.new_page()
                page.on('pageerror', lambda e: erreurs.append(str(e)))
                page.goto(url + '/?dossier=DEMO_SLO_001')
                page.locator('[data-o="m_placenta"]').click()
                page.goto(url + page.get_by_role('link', name='Rouvrir ce module').get_attribute('href'))
                page.wait_for_function('numeroCharge === "DEMO_SLO_001" && !charge')
                assert page.locator('#macro_01').input_value() == '125,5'
                assert page.locator('#macro_02').input_value() == '10'
                assert page.locator('#macro_08_autre').input_value() == 'Insertion fictive — test libre'
                assert page.locator('#micro_01_0').is_checked()
                assert page.locator('#micro_02_0').is_checked()
                assert page.locator('#conclusion_01_0').is_checked()
                print('OK sauvegarde puis fermeture et réouverture sans stockage navigateur : trois sections et texte Other retrouvés')
                # Les autres modules n'ont subi aucune réécriture.
                assert context.request.get(url + '/api/saisie/DEMO_SLO_001/administratif').json() == admin
                assert context.request.get(url + '/api/saisie/DEMO_SLO_001/macro_placenta').json() == ancien
                dossier = context.request.get(url + '/api/dossiers/DEMO_SLO_001').json()
                assert (dossier['terme_sa'], dossier['type_issue'], dossier['indication']) == (19, 'IMG', 'Smith-Lemli-Opitz')
                assert len([s for s in dossier['historique'] if s['module'] == 'placenta']) == 1
                print('OK administratif, ancien module macro, valeurs antérieures et historique préservés')
                # Autre dossier : aucune valeur du premier ne doit apparaître.
                page.goto(url + '/modules/placenta?dossier=DEMO_AUTRE&operateur=TEST')
                page.wait_for_function('numeroCharge === "DEMO_AUTRE" && !charge')
                assert page.locator('#macro_01').input_value() == ''
                assert page.locator('input[type=radio]:checked').count() == 0
                with page.expect_response(lambda r: r.url.endswith('/api/saisie') and r.request.method == 'POST') as r:
                    page.locator('#hubSave').click()
                assert r.value.status == 200
                print('OK dossier distinct sans contamination et enregistrement de toutes les réponses vides')
                # Échec de lecture : interdire une sauvegarde qui masquerait les données.
                page.route('**/api/saisie/DEMO_SLO_001/placenta*', lambda route: route.fulfill(status=500, body='{}', content_type='application/json'))
                page.goto(url + '/modules/placenta?dossier=DEMO_SLO_001&operateur=TEST')
                page.wait_for_function('document.getElementById("etat").textContent.includes("Lecture impossible")')
                page.locator('#hubSave').click()
                page.wait_for_function('document.getElementById("hubMsg").textContent.includes("Valider le numéro")')
                assert context.request.get(url + '/api/saisie/DEMO_SLO_001/placenta').json() == sauvegarde
                assert not erreurs, erreurs
                print('OK erreur de lecture sans écrasement ; aucune erreur JavaScript')
                browser.close()
            # La réindexation fait partie du contrat de stockage existant.
            cx, _ = ingest.ouvrir(base / 'hub.sqlite')
            ingest.reindexer(cx)
            cx.commit()
            assert cx.execute("SELECT valeur_txt FROM valeurs_plates WHERE module='placenta' AND chemin='sections.0.champs.macro_01'").fetchone()[0] == '125,5'
            assert cx.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
            cx.close()
            original = sqlite3.connect(source / 'hub.sqlite')
            assert original.execute("SELECT count(*) FROM saisies").fetchone()[0] == 3
            original.close()
            print('OK réindexation, intégrité SQLite et base fictive source inchangée')
        finally:
            serveur.shutdown()
            thread.join()


if __name__ == '__main__':
    main()
