# SPDX-License-Identifier: CC-BY-NC-SA-4.0
import ast,hashlib,json,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def bloc(s,nom):
 m=re.search(r'\b(?:var|const)\s+'+re.escape(nom)+r'\s*=\s*([\[{])',s)
 if not m:raise ValueError(nom)
 debut=m.start(1);prof=0;quote=None;escape=False
 for i in range(debut,len(s)):
  c=s[i]
  if quote:
   if escape:escape=False
   elif c=='\\':escape=True
   elif c==quote:quote=None
  elif c in '\"\'':quote=c
  elif c in '[{':prof+=1
  elif c in ']}':
   prof-=1
   if prof==0:return s[debut:i+1]
 raise ValueError(nom)

class ReferencesInchangees(unittest.TestCase):
    def test_tables_et_autres_modules_inchanges(self):
        refs=json.loads((ROOT/'tests/references_main.json').read_text())
        for rel,tables in refs['tables'].items():
            texte=(ROOT/rel).read_text()
            for nom,sha in tables.items():
                self.assertEqual(hashlib.sha256(bloc(texte,nom).encode()).hexdigest(),sha,(rel,nom))
        for rel,sha in refs['fichiers'].items():
            self.assertEqual(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),sha,rel)

        source=(ROOT/'hub/app/cr_lumi.py').read_text()
        for n in ast.parse(source).body:
            if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in refs['python_data']:
                valeur=ast.literal_eval(n.value)
                self.assertEqual(hashlib.sha256(json.dumps(valeur,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),refs['python_data'][n.targets[0].id])
        source=(ROOT/'hub/app/serveur.py').read_text()
        fonction=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='main')
        self.assertEqual(hashlib.sha256(ast.get_source_segment(source,fonction).encode()).hexdigest(),refs['python_fonctions']['main'])
