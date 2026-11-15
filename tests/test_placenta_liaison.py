# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Protection des données lors du partage de mesures entre les trames."""
import base64
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'hub/app'))
import ingest
from serveur import creer_app


class LiaisonPlacenta(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='liaison-placenta-');self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);ingest.arborescence(self.base)
        cx,_=ingest.ouvrir(self.base/'hub.sqlite');ingest.migrer(cx,ROOT/'hub/app/migrations',bavard=False);cx.close()
        self.client=creer_app(self.base,ROOT).test_client()
        self.admin={'module':'administratif','schema_version':'0.3.0','module_version':'2.1.0','dossier':'TEST-LIAISON','issue':{'terme_sa':28}}
        self.assertEqual(self.client.post('/api/saisie',json=self.admin).status_code,200)
        image=io.BytesIO();Image.new('RGB',(3,3),(20,90,80)).save(image,format='PNG');raw=image.getvalue()
        self.macro={'module':'macro_placenta','schema_version':'0.2.0','module_version':'1.1.1','dossier':'TEST-LIAISON','operateur':'TEST','conditions_masse':'fraiche_paree',
                    'sections':[{'id':'paree','champs':{'masse':90}},{'id':'cordon','champs':{'remarques':'Conserver ceci'}}],
                    'photos':[{'key':'etiquette','bytes':len(raw),'data_base64':base64.b64encode(raw).decode()}]}
        self.assertEqual(self.client.post('/api/saisie',json=self.macro).status_code,200)
        self.doc={'module':'placenta','schema_version':'0.1.0','module_version':'1.1.0','dossier':'TEST-LIAISON','operateur':'TEST','conditions_masse':'fraiche_paree',
                  'sections':[{'id':'macroscopie','champs':{'macro_01':'214,0','macro_02':'Transcription historique','champ_futur':'Conserver'}},{'id':'conclusion','champs':{'conclusion_01':'eutrophique'}}]}

    def get(self,module):
        return self.client.get('/api/saisie/TEST-LIAISON/'+module).json

    def versions(self):
        return self.client.get('/api/dossiers/TEST-LIAISON/placenta-liaison').json['versions']

    def test_cliches_inconnus_historique_et_conflit_atomique(self):
        before=self.versions();self.doc['liaison_versions']=before
        self.assertEqual(self.client.post('/api/saisie',json=self.doc).status_code,200)
        macro=self.client.get('/api/saisie/TEST-LIAISON/macro_placenta?cliches=1').json
        self.assertEqual(macro['photos'],self.macro['photos'])
        self.assertEqual(macro['sections'][1],self.macro['sections'][1])
        self.assertEqual(macro['sections'][0]['champs']['masse'],214)
        saved=self.get('placenta')
        self.assertEqual(saved['sections'][0]['champs']['macro_02'],'Transcription historique')
        self.assertEqual(saved['resultats_placentaires']['position_percentile'],'P50')
        # Une tentative utilisant l'ancien instantané ne change aucun module.
        self.doc['sections'][0]['champs']['macro_01']='140'
        r=self.client.post('/api/saisie',json=self.doc)
        self.assertEqual(r.status_code,409,r.text)
        self.assertEqual(self.get('placenta'),saved)
        self.assertEqual(self.client.get('/api/saisie/TEST-LIAISON/macro_placenta?cliches=1').json,macro)
        history=self.client.get('/api/dossiers/TEST-LIAISON').json['historique']
        self.assertTrue(any(d['module']=='macro_placenta' for d in history))

    def test_reprise_inverse_conserve_transcription_et_cle_inconnue(self):
        self.assertEqual(self.client.post('/api/saisie',json=self.doc).status_code,200)
        macro=self.client.get('/api/saisie/TEST-LIAISON/macro_placenta?cliches=1').json
        macro['sections'][0]['champs']['masse']=321
        self.assertEqual(self.client.post('/api/saisie',json=macro).status_code,200)
        saved=self.get('placenta');ch=saved['sections'][0]['champs']
        self.assertEqual(ch['macro_01'],'321');self.assertEqual(ch['macro_02'],'Transcription historique');self.assertEqual(ch['champ_futur'],'Conserver')
        self.assertEqual(saved['sections'][1],self.doc['sections'][1])
        self.assertEqual(saved['resultats_placentaires']['position_percentile'],'P90')

    def test_reponses_libres_non_numeriques_ne_suppriment_pas_mesures(self):
        self.doc['sections'][0]['champs']['macro_01']='non pesé'
        self.assertEqual(self.client.post('/api/saisie',json=self.doc).status_code,200)
        self.assertEqual(self.get('macro_placenta')['sections'][0]['champs']['masse'],90)
        self.assertIsNone(self.get('placenta')['resultats_placentaires']['position_percentile'])
        self.assertEqual(self.get('placenta')['sections'][0]['champs']['macro_01'],'non pesé')


if __name__=='__main__':unittest.main()
