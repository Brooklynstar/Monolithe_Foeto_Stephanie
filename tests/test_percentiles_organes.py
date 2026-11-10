# SPDX-License-Identifier: CC-BY-NC-SA-4.0
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'hub/app'))
import biometrie,cr,ingest,serveur,percentiles,percentiles_organes


def cas():
    refs=biometrie.References();out=[]
    for sa in range(11,45):
        for g in range(4):
            masses={k:20+i*7.5 for i,k in enumerate(refs.autopsie['champs'])}
            out.append({'sa':sa,'grade':g,'masses':masses,'attendus':biometrie.calculer(refs,sa,g,masses)})
    return out


def cas_neuro():
    tables=json.loads((ROOT/'hub/references/neuropath_masses.json').read_text())
    out=[]
    for sa in range(7,44):
        for champ,nom in [('masse_enc','REF_ME'),('masse_cerv','REF_MI')]:
            ref=next((r for bande,r in tables[nom].items() if int(bande.split('-')[0])<=sa<=int(bande.split('-')[-1])),None)
            valeurs=[0,ref['m'],ref['m']+ref['s']*.1249] if ref else [0,1,2]
            for valeur in valeurs:
                z=(valeur-ref['m'])/ref['s'] if ref else None
                out.append({'sa':sa,'champ':champ,'valeur':valeur,'z_brut':z,'percentile':50*math.erfc(-z/math.sqrt(2)) if z is not None else None})
    return out


class PercentilesOrganes(unittest.TestCase):
    def test_oracle_tables_et_percentiles_non_arrondis(self):
        refs=biometrie.References();a=refs.autopsie
        for c in cas():
            sa,g=c['sa'],c['grade']
            gc=next((v for k,v in a['GC'].items() if int(k.split('-')[0])<=sa<=int(k.split('-')[-1])),{})
            ma=next((r for r in a['MA'] if r['s']==sa),{})
            mb=a['MB'].get(str(sa),{}) if 12<=sa<=20 else {}
            for champ,masse in c['masses'].items():
                cles=a['champs'][champ]
                for src,t in [('gc',gc),('ma',ma),('mb',mb)]:
                    k=cles.get(src)
                    if src=='ma' and cles.get('mg'):
                        suffixe=('01' if g<=1 else '2' if g==2 else '3') if cles['mg']==1 else ('01' if g<=1 else '23')
                        k=k+'_'+suffixe
                    r=t.get(k,{})
                    ligne=c['attendus'][champ]
                    if r.get('m') is not None and r.get('sd',0)>0:
                        z=(masse-r['m'])/r['sd'];p=50*math.erfc(-z/math.sqrt(2))
                        self.assertEqual(ligne['z_brut_'+src],z)
                        self.assertEqual(ligne['percentile_'+src],p)
                    else:self.assertIsNone(ligne['percentile_'+src])
        x=biometrie.calculer(refs,20,None,{'foie_masse':20})['foie_masse']
        self.assertIsNone(x['percentile_ma'])
        self.assertIsNotNone(x['percentile_gc'])
        self.assertTrue(all(v is None for k,v in biometrie.calculer(refs,20.5,0,{'foie_masse':20})['foie_masse'].items() if k.startswith('percentile_')))

    def test_z_et_interpretations_historiques_inchanges(self):
        refs=biometrie.References()
        result=[]
        for sa in range(12,44):
            for g in range(4):
                d=biometrie.calculer(refs,sa,g,{k:20+i*7.5 for i,k in enumerate(refs.autopsie['champs'])})
                result.append({k:{a:b for a,b in v.items() if not a.startswith(('z_brut_','percentile_'))} for k,v in d.items()})
        self.assertEqual(hashlib.sha256(json.dumps(result,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'e24e322170e243cf3fe1afa30fecd78e5ac022c489f000c8719a373606589627')

    def test_neuropath_masses_seules_zero_et_sans_tables(self):
        doc={'etapes':[{'champs':[{'id':'masse_enc','label':'Encéphale','valeur':0,'unite':'g'},
                                {'id':'masse_cerv','label':'Étage infratentoriel','valeur':2.19,'unite':'g'},
                                {'id':'ratio_ce','valeur':4,'zscore':{'z':.4}}]}]}
        mod,rows=percentiles_organes.neuropath(doc,19)
        self.assertEqual(rows[1]['percentile'],50)
        self.assertEqual(mod['etapes'][0]['champs'][2],doc['etapes'][0]['champs'][2])
        self.assertNotIn('zscore',doc['etapes'][0]['champs'][0])
        self.assertIsNotNone(rows[0]['percentile'])
        doc['etapes'][0]['champs'][0]['zscore']={'z':9,'attendu_m':99}
        _,rows=percentiles_organes.neuropath(doc,50)
        self.assertIsNone(rows[0]['z'])
        self.assertEqual(doc['etapes'][0]['champs'][0]['zscore']['z'],9)
        self.assertTrue(all(r['percentile'] is None for r in rows))
        html=percentiles_organes.table_organes([{'label':'Test','valeur':0,'z_gc':0,'z_brut_gc':0,'percentile_gc':50}])
        import cr_lumi
        self.assertIn('+0,00 DS',cr_lumi._table_bio_int({'coeur':{'valeur':0,'ds':0}}))
        self.assertIn('P50,00',html);self.assertNotIn('Percentile MA',html);self.assertIn('11pt',html)

    def test_math_javascript_python_2001_points(self):
        code="const fs=require('fs'),vm=require('vm'),c={};vm.createContext(c);vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),c);console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(z=>c.Percentiles.calculer(z))));"
        zs=[i/100 for i in range(-1000,1001)]
        ps=json.loads(subprocess.check_output(['node','-e',code,str(ROOT/'hub/app/web/percentiles.js')],input=json.dumps(zs).encode()))
        for z,p in zip(zs,ps):self.assertAlmostEqual(p,percentiles.percentile(z),delta=2e-12)

    def test_parcours_navigateur_json_cr_anciens_dossiers_et_domaines(self):
        from werkzeug.serving import make_server
        with tempfile.TemporaryDirectory(prefix='percentiles-organes-') as tmp:
            base=Path(tmp);ingest.arborescence(base);cx,_=ingest.ouvrir(base/'hub.sqlite');ingest.migrer(cx,ROOT/'hub/app/migrations',bavard=False)
            cx.close()
            cases=base/'cas.json';cases.write_text(json.dumps({'autopsie':cas(),'neuropath':cas_neuro()}))
            http=make_server('127.0.0.1',0,serveur.creer_app(base,ROOT),threaded=True)
            thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
            try:
                r=subprocess.run(['node',str(ROOT/'tests/organes_browser.cjs'),str(cases),f'http://127.0.0.1:{http.server_port}'],capture_output=True,text=True,timeout=180)
                self.assertEqual(r.returncode,0,r.stdout+r.stderr)
                print(r.stdout)
            finally:http.shutdown();http.server_close();thread.join(timeout=5)

    def test_blocs_synchronises_et_pack(self):
        subprocess.run([sys.executable,str(ROOT/'hub/outils/integrer_percentiles_organes.py'),'--verifier'],check=True)
        for nom in ('autopsie.html','neuropath.html'):
            self.assertEqual((ROOT/'Macro'/nom).read_bytes(),(ROOT/'pack_telephone'/nom).read_bytes())


if __name__=='__main__':unittest.main()
