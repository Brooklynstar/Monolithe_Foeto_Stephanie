# SPDX-License-Identifier: CC-BY-NC-SA-4.0
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
import percentiles_placenta as pp
import ingest,serveur,cr_lumi


def cas():
    refs=json.loads(pp.REFERENCES.read_text())['Redline'];out=[]
    for sa in range(11,45):
        r=refs.get(str(sa),{'P10':100,'P50':150,'P90':200})
        valeurs=[None,0,100.1249,r['P10']-.01,r['P10'],r['P10']+.01,r['P50'],r['P90'],r['P90']+.01]
        for masse in valeurs:
            for cond in ('fraiche_paree','fixe','non_documentees'):
                out.append({'sa':sa,'masse':masse,'conditions':cond,'attendu':pp.calculer(sa,masse,cond)})
    return out


class PercentilesPlacenta(unittest.TestCase):
    def test_seuils_publies_sans_loi_normale(self):
        for sa,r in cr_lumi.DONNEES_PLACENTA.items():
            if r['source']!='Redline':
                self.assertIsNone(pp.calculer(sa,r['P50'],'fraiche_paree')['position_percentile']);continue
            for cle in ('P10','P50','P90'):
                resultat=pp.calculer(sa,r[cle],'fraiche_paree')
                self.assertEqual(resultat['position_percentile'],cle)
                self.assertEqual(resultat['z_brut'],(r[cle]-r['moyenne'])/r['sd'])
                self.assertIsNone(resultat['percentile_exact'])
            self.assertEqual(pp.calculer(sa,r['P10']-.01,'fraiche_paree')['position_percentile'],'< P10')
            self.assertEqual(pp.calculer(sa,r['P10']+.01,'fraiche_paree')['position_percentile'],'P10–P50')
        # P50 empirique ne coïncide pas avec la moyenne : ne pas transformer ce Z en P.
        r=pp.calculer(28,214,'fraiche_paree')
        self.assertEqual(r['position_percentile'],'P50');self.assertNotEqual(r['z_brut'],0)

    def test_limites_zero_et_conditions(self):
        for sa in (None,20.5,True,math.nan,50):
            self.assertIsNone(pp.calculer(sa,400,'fraiche_paree')['position_percentile'])
        for masse in (None,True,-1,math.nan,math.inf):
            self.assertIsNone(pp.calculer(28,masse,'fraiche_paree')['position_percentile'])
        for cond in ('fixe','non_documentees'):
            self.assertIsNone(pp.calculer(28,400,cond)['position_percentile'])
        r=pp.calculer(28,0,'fraiche_paree');self.assertEqual(r['position_percentile'],'< P10')
        self.assertIn('0 g',pp.tableau(r));self.assertNotIn('Limite</th>',pp.tableau(r))
        r=pp.calculer(28,400,'fixe');self.assertNotIn('Z-score</span>',pp.tableau(r))

    def test_copies_tables_identiques_et_pack(self):
        refs=json.loads(pp.REFERENCES.read_text())['Redline']
        self.assertEqual(refs,{str(k):v for k,v in cr_lumi.DONNEES_PLACENTA.items()})
        subprocess.run([sys.executable,str(ROOT/'hub/outils/integrer_percentiles_placenta.py'),'--verifier'],check=True)
        self.assertEqual((ROOT/'Macro/macro_placenta.html').read_bytes(),(ROOT/'pack_telephone/macro_placenta.html').read_bytes())

    def test_parcours_python_js_exports_anciens_dossiers_cr_et_hub(self):
        from werkzeug.serving import make_server
        with tempfile.TemporaryDirectory(prefix='percentiles-placenta-') as tmp:
            base=Path(tmp);ingest.arborescence(base);cx,_=ingest.ouvrir(base/'hub.sqlite');ingest.migrer(cx,ROOT/'hub/app/migrations',bavard=False);cx.close()
            fichier=base/'cas.json';fichier.write_text(json.dumps(cas()))
            http=make_server('127.0.0.1',0,serveur.creer_app(base,ROOT),threaded=True)
            thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
            try:
                r=subprocess.run(['node',str(ROOT/'tests/placenta_browser.cjs'),str(fichier),f'http://127.0.0.1:{http.server_port}'],capture_output=True,text=True,timeout=180)
                self.assertEqual(r.returncode,0,r.stdout+r.stderr);print(r.stdout)
            finally:http.shutdown();http.server_close();thread.join(timeout=5)


if __name__=='__main__':unittest.main()
