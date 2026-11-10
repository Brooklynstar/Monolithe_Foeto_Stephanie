# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Vrai serveur ordinaire sur 5006, import et redémarrage sur la même base."""
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.request import Request, urlopen

DEPOT=Path(__file__).resolve().parents[1]
URL='http://127.0.0.1:5006'


class IntegrationSLO(unittest.TestCase):
    def test_serveur_5006_import_percentiles_et_persistance_apres_redemarrage(self):
        with socket.socket() as s:
            try:
                s.bind(('127.0.0.1',5006))
            except OSError:
                self.skipTest('port 5006 occupé par un service extérieur')
        with tempfile.TemporaryDirectory(prefix='integration-slo-') as tmp:
            base=Path(tmp)/'hub'
            log=open(Path(tmp)/'serveur.log','w+')
            self.addCleanup(log.close)
            def appel(path, data=None, method=None, content_type='application/json'):
                if isinstance(data,dict): data=json.dumps(data).encode()
                with urlopen(Request(URL+path,data=data,method=method,headers={'Content-Type':content_type}),timeout=5) as r:
                    return json.load(r)
            def demarrer():
                p=subprocess.Popen([sys.executable,'-u',str(DEPOT/'hub/app/serveur.py'),
                                    '--base',str(base),'--depot',str(DEPOT)],stdout=log,stderr=subprocess.STDOUT)
                for _ in range(150):
                    if p.poll() is not None: break
                    try:
                        etat=appel('/api/etat')
                        if etat['racine']==str(base): return p
                    except OSError: pass
                    time.sleep(.05)
                if p.poll() is None: p.terminate();p.wait(timeout=5)
                log.seek(0);self.fail(log.read())
            def arreter(p):
                if p.poll() is None: p.terminate();p.wait(timeout=5)
            def importer():
                brut=(DEPOT/'hub/exemples/DEMO_SLO_001.json').read_bytes()
                b='monolithe-test-boundary'
                corps=(f'--{b}\r\nContent-Disposition: form-data; name="fichiers"; filename="DEMO_SLO_001.json"\r\n'
                       'Content-Type: application/json\r\n\r\n').encode()+brut+f'\r\n--{b}--\r\n'.encode()
                appel('/api/deposer',corps,'POST','multipart/form-data; boundary='+b)
                return appel('/api/ingerer',{},'POST')
            proc=demarrer()
            try:
                self.assertEqual(appel('/api/etat')['dossiers'],0)
                self.assertEqual(importer()['ingerees'],1)
                admin=appel('/api/saisie/DEMO_SLO_001/administratif')
                admin['grossesse']['histoire_clinique']+=' Note fictive persistante de test intégration.'
                appel('/api/saisie',admin,'POST')
                cr=appel('/api/dossiers/DEMO_SLO_001/cr',{'gabarit':'complet','operateur':'Codex'},'POST')
                self.assertIn('P50,00',cr['texte'])
                self.assertIn('Percentile GC',cr['texte'])
                self.assertIn('Note fictive persistante',cr['texte'])
                bio=appel('/api/saisie/DEMO_SLO_001/biometrie_clinique')
                self.assertEqual(bio['percentiles']['pied']['MB'],50)
                arreter(proc)
                proc=demarrer()
                self.assertEqual(appel('/api/etat')['dossiers'],1)
                self.assertIn('Note fictive persistante',json.dumps(appel('/api/saisie/DEMO_SLO_001/administratif'),ensure_ascii=False))
                self.assertEqual(importer()['doublons'],1)
                self.assertIn('Note fictive persistante',json.dumps(appel('/api/saisie/DEMO_SLO_001/administratif'),ensure_ascii=False))
                self.assertEqual(appel('/api/cr/'+str(cr['id']))['texte'],cr['texte'])
            finally:
                arreter(proc)


if __name__=='__main__':
    unittest.main()
