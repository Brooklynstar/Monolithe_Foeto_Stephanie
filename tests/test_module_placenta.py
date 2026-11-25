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
from verifier_placenta import schema_releve

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
                        self.assertEqual(rendu,json.loads(json.dumps(schema_releve())))
                        self.assertEqual(page.locator('fieldset').count(),32)
                        self.assertEqual(page.locator('label.chip input').count(),154)
                        self.assertEqual(page.locator('[required]').count(),0)
                        print('OK dossier exact, reprise des quatre mesures et terme administratif ; 32 champs/154 constatations ; limite 19 SA')
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
                                      ('label.chip','button.chip',['fontFamily','fontSize','backgroundColor','borderColor','borderRadius','padding','minHeight','letterSpacing','textTransform'])]
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
                            if template == 'complet':
                                self.assertRegex(texte, r'exfolié\.</p>\s*<p[^>]*>Les membranes')
                            else:
                                self.assertRegex(texte, r'exfolié\.\nLes membranes')
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
                            'micro_03': [9, 11], 'micro_09': [10], 'conclusion_01': [26],
                        }.items():
                            page.locator('#g_' + champ + ' .effacer').click()
                            for index in elements:
                                page.locator(f'#{champ}_{index}').check()
                        save()
                        ouvrir()
                        self.assertEqual(page.locator('#macro_16').input_value(), '-16.7')
                        self.assertIn('Épaisseur négative', page.locator('#alerteEpaisseur').inner_text())
                        page.goto(URL+'/?dossier=DEMO_SLO_001')
                        page.locator('[data-o=cr]').click()
                        page.locator('#crGabarit option[value=placenta]').wait_for(state='attached')
                        page.locator('#crGabarit').select_option('placenta')
                        page.get_by_role('button', name='Produire un brouillon').click()
                        page.locator('#crPre').wait_for()
                        affiche = page.locator('#crPre').inner_text().strip()
                        self.assertNotIn('\n\n', affiche)
                        self.assertNotIn('FORMULAIRE STRUCTURÉ', affiche.upper())
                        self.assertNotRegex(affiche, r'[-−]16[,.]7')
                        for ligne in (
                            'PLACENTA\nMacroscopie',
                            'La galette placentaire, de forme ronde, pèse 90 g, sans les membranes ni le cordon, et mesure 9 × 8 cm sur 1,2 cm d’épaisseur.',
                            'Le cordon, d’insertion paracentrale, comporte trois vaisseaux.',
                            'À la coupe, on observe deux infarctus représentant 2 % de la surface de la galette placentaire et mesurant de 0,2 à 1 cm de grand axe.',
                            'On observe aussi une thrombose sous-choriale de 1 cm de grand axe.',
                            'Microscopie\nL’amnios est cubique.',
                            'chorioamniotite aiguë avec réponse inflammatoire maternelle (RIM) de stade 2',
                            'vasculite ombilicale avec réponse inflammatoire fœtale (RIF) de stade 2',
                            'de grade 1, légère à modérée',
                            'Conclusion\nIntervillite chronique d’étiologie indéterminée II (10–50 %)',
                            'À relire : la microscopie indique un grade 1 pour l’intervillite chronique, alors que la conclusion indique II.',
                        ):
                            self.assertIn(ligne, affiche)
                        page.locator('#crGabarit').select_option('complet')
                        with page.expect_response(lambda r: r.request.method == 'POST' and r.url.endswith('/cr')):
                            page.get_by_role('button', name='Produire un brouillon').click()
                        complet = page.locator('#crPre').inner_text()
                        self.assertIn('Le cordon, d’insertion paracentrale, comporte trois vaisseaux.', complet)
                        self.assertNotIn('22 cm', complet)
                        self.assertIn('La plaque choriale présente des kystes.', complet)
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
                        ouvrir('TEST-PCT-028');page.locator('#macro_01').fill('214');page.locator('#conditions_masse').select_option('fraiche_paree')
                        self.assertEqual(page.evaluate('calculer().position_percentile'),'P50')
                        save();pos=get('/api/saisie/TEST-PCT-028/placenta')
                        self.assertEqual(pos['resultats_placentaires']['position_percentile'],'P50')
                        rapport = context.request.post(URL+'/api/dossiers/TEST-PCT-028/cr',data={'gabarit':'placenta'})
                        self.assertIn('pèse 214 g (P50, Redline)', rapport.json()['texte'])
                        self.assertIsNone(pos['resultats_placentaires']['percentile_exact'])
                        m2=get('/api/saisie/TEST-PCT-028/macro_placenta')
                        self.assertEqual(next(s for s in m2['sections'] if s['id']=='paree')['champs']['masse'],214)
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
                        print('OK 28 SA/214 g=P50 ; synchronisation inverse P90 ; autres données préservées ; écriture concurrente bloquée (409)')
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
