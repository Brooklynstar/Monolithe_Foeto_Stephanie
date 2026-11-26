# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Autonomie, présentation Monolithe et intégration placentaire sur 5005.
Dépendances de test : flask, pillow, playwright ; MONOLITHE_CHROMIUM facultatif.
"""
import copy
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
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'hub/app'),str(ROOT/'hub/outils')]
import ingest
import percentiles_placenta as pp
from importer_placenta_demo import importer
from verifier_placenta import schema_placenta, verifier_preservation_releve

PORT = os.environ.get('MONOLITHE_TEST_PORT', '5005')
URL = 'http://127.0.0.1:' + PORT


class ModulePlacenta(unittest.TestCase):
    def test_branche_autonome_interface_synchronisation_et_redemarrage(self):
        with tempfile.TemporaryDirectory(prefix='module-placenta-v110-') as tmp:
            base=Path(tmp)/'hub';base.mkdir();importer(base)
            fixture=(ROOT/'hub/exemples/DEMO_SLO_001.json').read_bytes()
            with (Path(tmp)/'serveur.log').open('w+') as log:
                def start():
                    p=subprocess.Popen([sys.executable,'-u',str(ROOT/'hub/app/serveur.py'),'--base',str(base),'--port',PORT],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
                    for _ in range(150):
                        if p.poll() is not None:break
                        try:
                            with urlopen(URL+'/api/etat',timeout=.3) as r:
                                if Path(json.load(r)['racine']).resolve() == base.resolve():return p
                        except OSError:pass
                        time.sleep(.05)
                    if p.poll() is None:p.terminate();p.wait(timeout=5)
                    log.seek(0);self.fail(log.read())
                def stop(p):
                    if p.poll() is None:p.terminate();p.wait(timeout=5)
                proc=start()
                try:
                    with sync_playwright() as pw:
                        opts={'headless':True}
                        executable=os.environ.get('MONOLITHE_CHROMIUM')
                        if executable:opts['executable_path']=executable
                        browser=pw.chromium.launch(**opts)
                        context=browser.new_context(viewport={'width':1100,'height':950})
                        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                        def get(path):
                            r=context.request.get(URL+path);self.assertEqual(r.status,200,r.text());return r.json()
                        def post(doc):
                            return context.request.post(URL+'/api/saisie',data=doc)
                        def ouvrir(n='DEMO_SLO_001'):
                            page.goto(URL+'/modules/placenta?dossier='+n+'&operateur=TEST')
                            page.wait_for_function('numeroCharge === "'+n+'" && !charge')
                        avant={d['module']:get('/api/saisie/DEMO_SLO_001/'+d['module']) for d in json.loads(fixture)['saisies']}
                        cr_avant=get('/api/dossiers/DEMO_SLO_001/cr')
                        self.assertEqual(len(cr_avant),2)
                        page.goto(URL+'/?dossier=DEMO_SLO_001')
                        page.locator('[data-o=m_placenta]').wait_for()
                        self.assertEqual(page.locator('[data-o=m_macro_placenta]').count(),1)
                        ouvrir()
                        self.assertEqual(page.locator('#macro_01').input_value(),'90')
                        self.assertEqual(page.locator('#macro_03').input_value(),'9')
                        self.assertEqual(page.locator('#macro_04').input_value(),'8')
                        self.assertEqual(page.locator('#macro_05').input_value(),'1.2')
                        self.assertEqual(page.locator('#terme_sa').input_value(),'19')
                        self.assertTrue(page.locator('#terme_sa').get_attribute('readonly') is not None)
                        self.assertIn('22–42 SA',page.locator('#resultatsPercentilesPlacenta').inner_text())
                        rendu=page.evaluate('SECTIONS.map(s=>[s.titre,s.champs.map(c=>[c.label,c.type,c.choix])])')
                        verifier_preservation_releve()
                        self.assertEqual(rendu, schema_placenta())
                        self.assertEqual(page.locator('fieldset').count(), sum(len(champs) for _, champs in rendu))
                        self.assertEqual(page.locator('label.chip input').count(),
                                         sum(len(options) for _, champs in rendu for _, _, options in champs))
                        self.assertEqual(page.locator('[required]').count(),0)
                        print('OK dossier exact, reprise des quatre mesures et terme administratif ; trame étendue ; limite 19 SA')
                        # Compare les styles réellement calculés et les quatre thèmes, pas une simple copie de CSS.
                        macro=context.new_page();macro.goto(URL+'/modules/macro_placenta?dossier=DEMO_SLO_001&operateur=TEST')
                        macro.wait_for_function('document.getElementById("f_masse").value === "90"')
                        self.assertTrue(macro.locator('#f_masse').is_disabled())
                        self.assertTrue(macro.locator('#hubSave').is_disabled())
                        self.assertTrue(macro.locator('#btnWipe').is_disabled())
                        macro.get_by_role('button', name='Activer la saisie').click()
                        self.assertTrue(macro.locator('#f_masse').is_enabled())
                        macro.get_by_role('button', name='Repasser en lecture seule').click()
                        self.assertTrue(macro.locator('#f_masse').is_disabled())
                        self.assertEqual(macro.locator('#f_masse').input_value(), '90')
                        macro.get_by_role('button', name='Activer la saisie').click()
                        def styles(p,selector,props):
                            return p.locator(selector).first.evaluate('(e,ps)=>Object.fromEntries(ps.map(p=>[p,getComputedStyle(e)[p]]))',props)
                        comparaisons=[('body','body',['fontFamily','fontSize','lineHeight','backgroundColor','color']),
                                      ('.wrap','.wrap',['maxWidth','paddingTop','paddingLeft','paddingRight']),
                                      ('header','header',['borderBottomWidth','paddingBottom','marginBottom']),
                                      ('h1','h1',['fontFamily','fontSize','fontWeight','lineHeight']),
                                      ('section','section',['backgroundColor','borderColor','borderRadius','padding']),
                                      ('#dossier','#dossier',['fontFamily','fontSize','backgroundColor','color','borderRadius','padding']),
                                      ('#macro_01','#f_masse',['fontFamily','fontSize','backgroundColor','borderColor','borderRadius','padding']),
                                      ('#g_macro_06 label.chip','button.chip',['fontFamily','fontSize','backgroundColor','borderColor','borderRadius','padding','minHeight','letterSpacing','textTransform'])]
                        page.locator('#macro_06_0').check();macro.locator('button.chip').first.click()
                        comparaisons.append(('label.chip.on','button.chip[aria-pressed=true]',['backgroundColor','color','fontWeight','borderColor']))
                        for theme in ('clair','sombre','w98','cli'):
                            for p in (page,macro):p.evaluate('(t)=>{document.body.className=t==="clair"?"":"theme-"+t;}',theme)
                            for a,b,props in comparaisons:self.assertEqual(styles(page,a,props),styles(macro,b,props),(theme,a,b))
                        page.get_by_role('button',name='Effacer : Forme',exact=True).click();macro.locator('button.chip').first.click()
                        for p in (page,macro):p.evaluate('document.body.className=""')
                        sortie=Path(os.environ.get('MONOLITHE_CAPTURE_DIR',tmp));sortie.mkdir(parents=True,exist_ok=True)
                        page.screenshot(path=str(sortie/'placenta-v110.png'))
                        macro.screenshot(path=str(sortie/'macro-reference.png'))
                        page.set_viewport_size({'width':390,'height':844})
                        self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                        for largeur in (390, 1100):
                            page.set_viewport_size({'width': largeur, 'height': 950})
                            for groupe in ('.dimensions-placenta', '.tranches-placenta .ligne-macro'):
                                lignes = page.locator(groupe).evaluate_all(
                                    "rows => rows.map(row => [...row.querySelectorAll('input:not([type=radio])')]"
                                    ".map(input => input.getBoundingClientRect().top))"
                                )
                                self.assertTrue(all(len(set(ligne)) == 1 for ligne in lignes), lignes)
                        self.assertEqual(page.locator('.bloc-macro > h3').all_text_contents(), [
                            'Galette placentaire', 'Membranes', 'Cordon', 'Plaque choriale', 'Plaque basale', 'Tranches de section',
                        ])
                        titres = page.locator('.tranches-placenta h4, #l_releve_nidf')
                        self.assertEqual(titres.all_text_contents(), [
                            'Infarctus', 'Thrombose sous-choriale',
                            'Hématome décidual basal', 'Kyste trophoblastique', 'Thrombose intervilleuse', 'NIDF',
                        ])
                        self.assertTrue(page.locator('#g_macro_21').is_hidden())
                        for parent, detail in ((1, 30), (4, 5), (7, 31), (15, 16), (23, 24)):
                            retrait = page.locator(f'#micro_08_{detail}').evaluate(
                                '(e, parent) => e.closest(".micro-retrait")?.previousElementSibling'
                                '.querySelector("input")?.id === parent', f'micro_08_{parent}')
                            self.assertTrue(retrait, (parent, detail))
                        self.assertEqual(page.locator('#g_micro_09 h4').all_text_contents(), [
                            'Calcifications', 'Infiltrat inflammatoire chronique',
                        ])
                        plaque = page.locator('#micro-plaque-choriale')
                        self.assertEqual(plaque.locator('h3').text_content(), 'Plaque choriale')
                        self.assertEqual(plaque.locator('fieldset > legend').all_text_contents(),
                                         ['Vaisseaux', 'Amnios', 'Inflammation'])
                        page.evaluate("""() => {
                            const ancien = collecter();
                            ancien.sections.find(s => s.id === 'macroscopie').champs.macro_21 =
                                'Description historique fictive';
                            const micro = SECTIONS.find(s => s.id === 'microscopie').champs.find(c => c.id === 'micro_08');
                            ancien.sections.find(s => s.id === 'microscopie').champs.micro_08 =
                                [micro.choix[0], micro.choix[1], micro.choix[2], micro.choix[14]];
                            appliquer(ancien);
                        }""")
                        self.assertTrue(page.locator('#g_macro_21').is_visible())
                        self.assertEqual(page.locator('#macro_21').input_value(), 'Description historique fictive')
                        self.assertEqual(page.evaluate(
                            "collecter().sections.find(s => s.id === 'macroscopie').champs.macro_21"
                        ), 'Description historique fictive')
                        for i in (2, 28, 29, 31):
                            self.assertTrue(page.locator(f'#micro_08_{i}').is_checked())
                        self.assertFalse(page.locator('#micro_08_30').is_checked())
                        page.locator('#micro_08_30').check()
                        self.assertFalse(page.locator('#micro_08_2').is_checked())
                        ouvrir()
                        page.set_viewport_size({'width':1100,'height':950})
                        print('OK styles calculés identiques : corps, largeur, en-tête, titre, cartes, champs et choix ; 4 thèmes ; mobile sans débordement')
                        macro.close()
                        # Vérifier toutes les frontières de la référence, sans modèle nouveau.
                        refs=json.loads(pp.REFERENCES.read_text())['Redline'];cas=[]
                        for sa in range(11,45):
                            r=refs.get(str(sa),{'P10':100,'P50':150,'P90':200})
                            for masse in (None,0,100.1249,r['P10']-.01,r['P10'],r['P10']+.01,r['P50'],r['P90'],r['P90']+.01):
                                for condition in ('fraiche_paree','fixe','non_documentees'):
                                    cas.append([sa,masse,condition])
                        js=page.evaluate('(cs)=>cs.map(c=>PlacentaPercentiles.calculer(...c))',cas)
                        self.assertEqual(js,[pp.calculer(*c) for c in cas])
                        print('OK 918 cas du moteur existant : Python et JavaScript identiques')
                        page.locator('#micro_01_0').check();page.locator('#micro_02_0').check();page.locator('#conclusion_01_1').check()
                        page.locator('#macro_08_4').check();page.locator('#macro_08_autre').fill('Essai autonome — fictif')
                        page.locator('#macro_08_2').check()
                        page.locator('#macro_08_3').check()
                        page.locator('#macro_08_3').uncheck()
                        self.assertTrue(page.locator('#macro_08_2').is_checked())
                        self.assertTrue(page.locator('#macro_08_4').is_checked())
                        page.locator('#micro_01_5').check()
                        page.locator('#micro_02_1').check()
                        page.locator('#macro_15').fill('2,4')
                        page.locator('#macro_16').fill('0.6')
                        self.assertGreaterEqual(page.locator('#g_micro_02').bounding_box()['y']
                                                - page.locator('#g_micro_01').bounding_box()['y']
                                                - page.locator('#g_micro_01').bounding_box()['height'], 16)
                        self.assertGreaterEqual(page.locator('#g_micro_03').bounding_box()['y']
                                                - page.locator('#g_micro_02').bounding_box()['y']
                                                - page.locator('#g_micro_02').bounding_box()['height'], 16)
                        def save():
                            with page.expect_response(lambda r:r.url.endswith('/api/saisie') and r.request.method=='POST') as response:page.locator('#hubSave').click()
                            self.assertEqual(response.value.status,200,response.value.text())
                            page.wait_for_function('document.querySelector("#hubSave").disabled === false')
                            # Le rafraîchissement des versions doit être terminé avant une deuxième saisie.
                            page.wait_for_function('(sid)=>liaison && liaison.versions.placenta === sid',arg=response.value.json()['saisie_id'])
                        save()
                        saved=get('/api/saisie/DEMO_SLO_001/placenta')
                        self.assertEqual(saved['resultats_placentaires'],get('/api/dossiers/DEMO_SLO_001/percentiles-placenta-formulaire')['resultats'])
                        for module,doc in avant.items():self.assertEqual(get('/api/saisie/DEMO_SLO_001/'+module),doc,module)
                        browser.close();stop(proc);proc=start()
                        browser=pw.chromium.launch(**opts);context=browser.new_context();page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
                        ouvrir()
                        self.assertEqual(page.locator('#macro_08_autre').input_value(),'Essai autonome — fictif')
                        self.assertTrue(page.locator('#micro_01_0').is_checked());self.assertTrue(page.locator('#conclusion_01_1').is_checked())
                        for field in ('macro_08_2', 'macro_08_4', 'micro_01_5', 'micro_02_1'):
                            self.assertTrue(page.locator('#' + field).is_checked(), field)
                        self.assertFalse(page.locator('#macro_08_3').is_checked())
                        self.assertEqual(page.locator('#macro_15').input_value(), '2,4')
                        self.assertEqual(page.locator('#macro_16').input_value(), '0.6')
                        for template in ('complet','synthese','placenta'):
                            r=context.request.post(URL+'/api/dossiers/DEMO_SLO_001/cr',data={'gabarit':template})
                            self.assertEqual(r.status,200,r.text())
                            texte = r.json()['texte']
                            for mention in ('hyperspiralé', 'Essai autonome', 'aplati', 'exfolié',
                                            'de 2,4 cm de grand axe sur 0,6 cm d’épaisseur',
                                            'Le placenta est eutrophique.'):
                                self.assertIn(mention, texte)
                            self.assertRegex(texte, r'Les membranes[^\n<]* L’amnios est [^\n<]*exfolié\.')
                        self.assertEqual(get('/api/saisie/DEMO_SLO_001/placenta'),saved)
                        for module,doc in avant.items():self.assertEqual(get('/api/saisie/DEMO_SLO_001/'+module),doc,module)
                        self.assertEqual(get('/api/dossiers/DEMO_SLO_001/cr')[-2:],cr_avant)
                        print('OK après fermeture et redémarrage du serveur : trois sections, résultats, huit saisies et CR historiques préservés ; CR actuels intègrent le formulaire')
                        for champ, valeur in dict(macro_10='2', macro_11='2', macro_12='0.2',
                                                  macro_13='1', macro_15='1', macro_16='-16.7').items():
                            page.locator('#' + champ).fill(valeur)
                        self.assertIn('Épaisseur négative', page.locator('#alerteEpaisseur').inner_text())
                        for champ, elements in {
                            'macro_06': [0], 'macro_07': [1], 'macro_08': [0], 'macro_09': [2], 'micro_01': [2], 'micro_02': [2, 4],
                            'micro_03': [9, 11], 'micro_04': [2], 'micro_05': [1], 'micro_06': [1, 3],
                            'micro_07': [0], 'micro_09': [10], 'micro_10': [1, 4], 'conclusion_01': [26],
                        }.items():
                            page.locator('#g_' + champ + ' .effacer').click()
                            for index in elements:
                                page.locator(f'#{champ}_{index}').check()
                        page.locator('#releve_cordon_longueur').fill('23.5')
                        page.locator('#releve_cordon_spiralisation_1').check()
                        page.locator('#releve_cordon_particularites_0').check()
                        page.locator('#releve_cordon_particularites_2').check()
                        page.locator('#releve_completude_0').check()
                        page.locator('#releve_membranes_insertion_2').check()
                        page.locator('#releve_membranes_marginee_pct').fill('30')
                        page.locator('#releve_membranes_aspect_0').check()
                        page.locator('#releve_etat_basale_3').check()
                        page.locator('#releve_hematome_nombre').fill('2')
                        page.locator('#macro_17').fill('0.8')
                        page.locator('#releve_thrombose_intervilleuse_nombre').fill('3')
                        page.locator('#releve_thrombose_intervilleuse_taille').fill('1.5')
                        page.locator('#macro_19').fill('1')
                        page.locator('#macro_20').fill('0.8')
                        pct_nidf = page.locator('#releve_nidf_pct')
                        self.assertTrue(pct_nidf.is_disabled())
                        page.locator('#releve_nidf_1').check()
                        pct_nidf.fill('101')
                        self.assertFalse(pct_nidf.evaluate('(e) => e.checkValidity()'))
                        pct_nidf.fill('12.5')
                        page.locator('#releve_nidf_0').check()
                        self.assertTrue(pct_nidf.is_disabled())
                        sans_nidf = page.evaluate("collecter().sections.find(s => s.id === 'macroscopie').champs")
                        self.assertEqual(sans_nidf['releve_nidf'], 'Non')
                        self.assertIsNone(sans_nidf['releve_nidf_pct'])
                        page.locator('#releve_nidf_1').check()
                        page.locator('#releve_commentaires_macro').fill('Commentaire macroscopique fictif.')
                        page.locator('#g_micro_08 .effacer').click()
                        pct_avasc = page.locator('#releve_villosites_avasculaires_pct')
                        self.assertTrue(pct_avasc.is_disabled())
                        for i in (1, 7, 29, 30, 31):
                            page.locator(f'#micro_08_{i}').check()
                        self.assertFalse(page.locator('#micro_08_28').is_checked())
                        pct_avasc.fill('101')
                        self.assertFalse(pct_avasc.evaluate('(e) => e.checkValidity()'))
                        pct_avasc.fill('13.5')
                        commentaires_micro = {
                            'releve_commentaire_villosites': 'Commentaire villositaire fictif.',
                            'releve_commentaire_intervilleuse': 'Commentaire intervilleux fictif.',
                            'releve_commentaire_lesions': 'Commentaire des lésions fictif.',
                        }
                        for champ, commentaire in commentaires_micro.items():
                            page.locator('#' + champ).fill(commentaire)
                        blocs = page.locator('#releve_inclusion_blocs')
                        blocs.fill('2.5')
                        self.assertFalse(blocs.evaluate('(e) => e.checkValidity()'))
                        blocs.fill('3')
                        save()
                        ouvrir()
                        self.assertEqual(page.locator('#releve_cordon_longueur').input_value(), '23.5')
                        doc = get('/api/saisie/DEMO_SLO_001/placenta?cliches=1')
                        valeurs = next(s['champs'] for s in doc['sections'] if s['id'] == 'macroscopie')
                        micro = next(s['champs'] for s in doc['sections'] if s['id'] == 'microscopie')
                        self.assertEqual(micro['releve_villosites_avasculaires_pct'], 13.5)
                        self.assertEqual(pct_avasc.input_value(), '13.5')
                        self.assertTrue(page.locator('#micro_08_31').is_checked())
                        for champ, commentaire in commentaires_micro.items():
                            self.assertEqual(micro[champ], commentaire)
                            self.assertEqual(page.locator('#' + champ).input_value(), commentaire)
                        export = get('/api/dossiers/DEMO_SLO_001/export.json')
                        self.assertEqual(next(s for s in export['saisies'] if s['module'] == 'placenta'), doc)
                        self.assertEqual(valeurs['releve_cordon_longueur'], 23.5)
                        self.assertEqual(valeurs['releve_membranes_marginee_pct'], 30)
                        self.assertEqual(valeurs['releve_nidf'], 'Oui')
                        self.assertEqual(valeurs['releve_nidf_pct'], 12.5)
                        self.assertEqual(valeurs['releve_commentaires_macro'], 'Commentaire macroscopique fictif.')
                        self.assertEqual(valeurs['releve_inclusion_blocs'], 3)
                        self.assertEqual(valeurs['releve_hematome_nombre'], 2)
                        self.assertEqual(valeurs['releve_thrombose_intervilleuse_nombre'], 3)
                        self.assertEqual(valeurs['releve_thrombose_intervilleuse_taille'], 1.5)
                        self.assertEqual(page.locator('#releve_hematome_nombre').input_value(), '2')
                        self.assertEqual(page.locator('#releve_thrombose_intervilleuse_nombre').input_value(), '3')
                        self.assertEqual(page.locator('#releve_thrombose_intervilleuse_taille').input_value(), '1.5')
                        self.assertTrue(page.locator('#releve_nidf_1').is_checked())
                        self.assertEqual(pct_nidf.input_value(), '12.5')
                        self.assertEqual(blocs.input_value(), '3')
                        self.assertEqual(page.locator('#releve_commentaires_macro').input_value(),
                                         'Commentaire macroscopique fictif.')
                        self.assertTrue(page.locator('#releve_membranes_insertion_2').is_checked())
                        self.assertTrue(page.locator('#releve_etat_basale_3').is_checked())
                        self.assertEqual(page.locator('#macro_16').input_value(), '-16.7')
                        self.assertIn('Épaisseur négative', page.locator('#alerteEpaisseur').inner_text())
                        page.goto(URL+'/?dossier=DEMO_SLO_001')
                        page.locator('[data-o=cr]').click()
                        page.locator('#crGabarit option[value=placenta]').wait_for(state='attached')
                        page.locator('#crGabarit').select_option('placenta')
                        page.get_by_role('button', name='Produire un brouillon').click()
                        page.locator('#crPre').wait_for()
                        affiche = page.locator('#crPre').inner_text().strip()
                        self.assertNotIn('\n\n', affiche.split('Conclusion', 1)[1])
                        affiche = '\n'.join(ligne for ligne in affiche.splitlines() if ligne.strip())
                        self.assertNotIn('FORMULAIRE STRUCTURÉ', affiche.upper())
                        self.assertNotRegex(affiche, r'[-−]16[,.]7')
                        for ligne in (
                            'Placenta\nMacroscopie',
                            'La galette placentaire, complète et de forme ronde, pèse 90 g, sans les membranes ni le cordon, et mesure 9 × 8 cm sur 1,2 cm d’épaisseur.',
                            'Le cordon, d’insertion paracentrale, mesure 23,5 cm, comporte trois vaisseaux. Il est hyperspiralé, comportant une palmure amniotique et un nœud vrai.',
                            'Les membranes sont d’aspect normal, d’insertion circumvallée sur 30 % de la circonférence.',
                            'Constatations de la plaque basale : calcifications.',
                            'À la coupe, on observe deux infarctus représentant 2 % de la surface de la galette placentaire et mesurant de 0,2 à 1 cm de grand axe.',
                            'On observe aussi une thrombose sous-choriale de 1 cm de grand axe.',
                            'On observe 2 hématomes déciduaux basaux de 0,8 cm de grand axe.',
                            'Présence d’un kyste trophoblastique de 0,8 cm de grand axe et de 3 thromboses intervilleuses de 1,5 cm de grand axe maximal.',
                            'Présence de NIDF évaluée à 12,5%.',
                            'Commentaires : Commentaire macroscopique fictif.',
                            'Inclusion partielle en 3 blocs.',
                            'Microscopie\nLes membranes présentent',
                            'L’amnios est cubique.',
                            'maturation en accord avec le terme',
                            'focales (moins de 20 % des villosités)',
                            'villosités avasculaires sur environ 13,5 % du parenchyme examiné',
                            'Villosités — commentaire : Commentaire villositaire fictif.',
                            'Chambre intervilleuse — commentaire : Commentaire intervilleux fictif.',
                            'Lésions — commentaire : Commentaire des lésions fictif.',
                            'chorioamniotite aiguë avec réponse inflammatoire maternelle (RIM) de stade 2',
                            'vasculite ombilicale avec réponse inflammatoire fœtale (RIF) de stade 2',
                            'de grade 1, légère à modérée',
                            'Conclusion\nIntervillite chronique d’étiologie indéterminée II (10–50 %)',
                            'À relire : la microscopie indique un grade 1 pour l’intervillite chronique, alors que la conclusion indique II.',
                        ):
                            self.assertIn(ligne, affiche)
                        macro = page.locator('#crPre section').filter(has=page.get_by_role('heading', name='Macroscopie', exact=True))
                        self.assertEqual(macro.locator('h3').evaluate("(e) => getComputedStyle(e).textDecorationLine"), 'underline')
                        style_macro = macro.evaluate("(e) => [getComputedStyle(e).fontFamily, getComputedStyle(e).textAlign]")
                        self.assertEqual(style_macro, ['Calibri, Arial, sans-serif', 'justify'])
                        paragraphes = macro.locator('p').all_text_contents()
                        self.assertEqual(len(paragraphes), 9)
                        for paragraphe, debut in zip(paragraphes, [
                            'La galette placentaire', 'Les membranes', 'Le cordon', 'La plaque choriale',
                            'Constatations de la plaque basale', 'À la coupe', 'Présence de NIDF',
                            'Commentaires', 'Inclusion partielle',
                        ]):
                            self.assertTrue(paragraphe.startswith(debut), paragraphe)
                        microscopie = page.locator('#crPre section').filter(
                            has=page.get_by_role('heading', name='Microscopie', exact=True))
                        self.assertEqual(microscopie.locator('h3').evaluate(
                            '(e) => getComputedStyle(e).textDecorationLine'), 'underline')
                        self.assertEqual(microscopie.evaluate(
                            '(e) => [getComputedStyle(e).fontFamily, getComputedStyle(e).textAlign]'),
                            ['Calibri, Arial, sans-serif', 'justify'])
                        micro_paragraphes = microscopie.locator('p').all_text_contents()
                        debuts_micro = [
                            'Les membranes', 'Au niveau du cordon', 'Au niveau de la plaque choriale',
                            'L’examen de la plaque basale', 'Les villosités', 'Dans la chambre intervilleuse',
                            'L’examen microscopique',
                        ]
                        self.assertEqual(len(micro_paragraphes), len(debuts_micro))
                        for paragraphe, debut in zip(micro_paragraphes, debuts_micro):
                            self.assertTrue(paragraphe.startswith(debut), paragraphe)
                        self.assertTrue(micro_paragraphes[0].endswith('L’amnios est cubique.'))
                        choriale = micro_paragraphes[2]
                        self.assertLess(choriale.index('thrombose'), choriale.index('chorioamniotite'))
                        self.assertLess(choriale.index('chorioamniotite'), choriale.index('L’amnios'))
                        page.locator('#crGabarit').select_option('complet')
                        with page.expect_response(lambda r: r.request.method == 'POST' and r.url.endswith('/cr')):
                            page.get_by_role('button', name='Produire un brouillon').click()
                        complet = page.locator('#crPre').inner_text()
                        self.assertIn('Le cordon, d’insertion paracentrale, mesure 23,5 cm, comporte trois vaisseaux.', complet)
                        self.assertNotIn('22 cm', complet)
                        self.assertIn('La plaque choriale présente des kystes.', complet)
                        self.assertIn(choriale, complet)
                        self.assertNotIn('Longueur du cordon', complet)
                        self.assertNotIn('sans lésion focale', complet)
                        ouvrir()
                        page.locator('#macro_16').fill('0.3')
                        save()
                        page.goto(URL+'/?dossier=DEMO_SLO_001')
                        page.locator('[data-o=cr]').click()
                        page.locator('#crGabarit').select_option('complet')
                        with page.expect_response(lambda r: r.request.method == 'POST' and r.url.endswith('/cr')):
                            page.get_by_role('button', name='Produire un brouillon').click()
                        self.assertIn('une thrombose sous-choriale de 1 cm de grand axe sur 0,3 cm d’épaisseur.',
                                      page.locator('#crPre').inner_text())
                        print('OK rédaction affichée dans Chrome, épaisseur négative écartée et discordance de grade signalée')
                        # Nouveau cas positif ; ne jamais changer le terme du SLO.
                        admin={'module':'administratif','schema_version':'0.3.0','module_version':'2.1.0','dossier':'TEST-PCT-028','operateur':'TEST','issue':{'terme_sa':28}}
                        self.assertEqual(post(admin).status,200)
                        m=copy.deepcopy(avant['macro_placenta']);m['dossier']='TEST-PCT-028';m['conditions_masse']='fraiche_paree'
                        for s in m['sections']:
                            if 'terme_sa' in s['champs']:s['champs']['terme_sa']=28
                        self.assertEqual(post(m).status,200)
                        ouvrir('TEST-PCT-028');page.locator('#macro_01').fill('180');page.locator('#conditions_masse').select_option('fraiche_paree')
                        self.assertEqual(page.evaluate('calculer().position_percentile'),'P10–P50')
                        self.assertEqual(page.locator('#macro_02').input_value(), 'P31,6 estimé')
                        self.assertEqual(page.locator('#ecartPoidsPlacenta').inner_text(), '−0,65')
                        self.assertIn('10.1017/9781316848616.039', page.locator('.reference-placenta').inner_text())
                        save();pos=get('/api/saisie/TEST-PCT-028/placenta')
                        self.assertEqual(pos['resultats_placentaires']['percentile_numerique'],31.6)
                        self.assertTrue(pos['resultats_placentaires']['percentile_interpole'])
                        self.assertEqual(next(s for s in pos['sections'] if s['id']=='macroscopie')['champs']['macro_02'],
                                         'P31,6 estimé')
                        ouvrir('TEST-PCT-028')
                        self.assertEqual(page.locator('#macro_02').input_value(), 'P31,6 estimé')
                        paquet = get('/api/dossiers/TEST-PCT-028/export.json')
                        exporte = next(s for s in paquet['saisies'] if s['module'] == 'placenta')
                        self.assertEqual(exporte['resultats_placentaires'], pos['resultats_placentaires'])
                        for gabarit in ('placenta', 'complet', 'synthese'):
                            rapport = context.request.post(URL+'/api/dossiers/TEST-PCT-028/cr',data={'gabarit':gabarit})
                            self.assertIn('pèse 180 g (P31,6 estimé, −0,65 DS selon Redline)', rapport.json()['texte'])
                            self.assertNotIn('10.1017/9781316848616.039', rapport.json()['texte'])
                        self.assertIsNone(pos['resultats_placentaires']['percentile_exact'])
                        m2=get('/api/saisie/TEST-PCT-028/macro_placenta')
                        self.assertEqual(next(s for s in m2['sections'] if s['id']=='paree')['champs']['masse'],180)
                        self.assertEqual(next(s for s in m2['sections'] if s['id']=='cordon'),next(s for s in m['sections'] if s['id']=='cordon'))
                        # Reverse update must retain all microscopic/conclusion data.
                        for s in m2['sections']:
                            if s['id']=='paree':s['champs']['masse']=321
                        self.assertEqual(post(m2).status,200)
                        p90=get('/api/saisie/TEST-PCT-028/placenta')
                        self.assertEqual(p90['resultats_placentaires']['position_percentile'],'P90')
                        self.assertEqual(p90['sections'][1:],pos['sections'][1:])
                        # Stale page must not silently overwrite a later save.
                        page.locator('#macro_01').fill('140')
                        with page.expect_response(lambda r:r.url.endswith('/api/saisie') and r.request.method=='POST') as response:page.locator('#hubSave').click()
                        self.assertEqual(response.value.status,409,response.value.text())
                        self.assertEqual(get('/api/saisie/TEST-PCT-028/placenta'),p90)
                        print('OK 28 SA/180 g = P31,6 estimé ; synchronisation inverse P90 ; autres données préservées ; écriture concurrente bloquée (409)')
                        ouvrir('TEST-PCT-028')
                        for condition in ('fixe','non_documentees'):
                            page.locator('#conditions_masse').select_option(condition)
                            self.assertIsNone(page.evaluate('calculer().position_percentile'))
                            save()
                            self.assertEqual(get('/api/saisie/TEST-PCT-028/placenta')['resultats_placentaires'],get('/api/dossiers/TEST-PCT-028/percentiles-placenta-formulaire')['resultats'])
                        # Malicious/frozen result is recomputed server-side.
                        doc=get('/api/saisie/TEST-PCT-028/placenta');doc['resultats_placentaires']={'position_percentile':'P99 inventé'}
                        self.assertEqual(post(doc).status,200)
                        self.assertIsNone(get('/api/saisie/TEST-PCT-028/placenta')['resultats_placentaires']['position_percentile'])
                        self.assertEqual(get('/api/saisie/DEMO_SLO_001/macro_placenta'),avant['macro_placenta'])
                        self.assertEqual((ROOT/'hub/exemples/DEMO_SLO_001.json').read_bytes(),fixture)
                        self.assertEqual(errors,[])
                        print('OK exclusions, recalcul serveur des résultats falsifiés, SLO inchangé et aucune erreur JavaScript')
                        browser.close()
                    cx,_=ingest.ouvrir(base/'hub.sqlite');ingest.reindexer(cx);cx.commit();self.assertEqual(cx.execute('PRAGMA integrity_check').fetchone()[0],'ok');cx.close()
                finally:stop(proc)


if __name__=='__main__':unittest.main()
