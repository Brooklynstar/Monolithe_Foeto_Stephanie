#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-NC-SA-4.0
from pathlib import Path
import json
import sys
RACINE=Path(__file__).resolve().parents[2]
source=RACINE/'hub/app/web/percentiles_placenta.js'
refs=json.loads((RACINE/'hub/references/placenta_percentiles.json').read_text(encoding='utf-8'))
s=source.read_text(encoding='utf-8')
a,rest=s.split('/* BEGIN REFERENCES */',1);_,b=rest.split('/* END REFERENCES */',1)
s=a+'/* BEGIN REFERENCES */\n'+json.dumps(refs,ensure_ascii=False,separators=(',',':'))+'\n/* END REFERENCES */'+b
if '--verifier' in sys.argv:
    if s!=source.read_text(encoding='utf-8'):raise SystemExit('Références JS périmées')
else:source.write_text(s,encoding='utf-8')
bloc='<!-- BEGIN percentiles_placenta.js -->\n<script>\n'+s.rstrip()+'\n</script>\n<!-- END percentiles_placenta.js -->'
for rel in ('Macro/macro_placenta.html','hub/calculateur-unifie.html'):
    p=RACINE/rel;texte=p.read_text(encoding='utf-8')
    debut='<!-- BEGIN percentiles_placenta.js -->';fin='<!-- END percentiles_placenta.js -->'
    if debut in texte:
        a,r=texte.split(debut,1);_,b=r.split(fin,1);nouveau=a+bloc+b
    else:nouveau=texte.replace('<script>',bloc+'\n<script>',1)
    if '--verifier' in sys.argv:
        if nouveau!=texte:raise SystemExit('Bloc périmé : '+rel)
    else:p.write_text(nouveau,encoding='utf-8')
