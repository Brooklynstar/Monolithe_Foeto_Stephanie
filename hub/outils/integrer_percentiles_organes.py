#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-NC-SA-4.0
from pathlib import Path
import sys
RACINE=Path(__file__).resolve().parents[2]
SOURCE=RACINE/'hub/app/web/percentiles.js'
DEBUT='<!-- BEGIN percentiles.js -->'
FIN='<!-- END percentiles.js -->'
for rel in ('Macro/autopsie.html','Macro/neuropath.html','hub/calculateur-unifie.html','hub/app/dossiers.html'):
    p=RACINE/rel;s=p.read_text(encoding='utf-8')
    bloc=DEBUT+'\n<script>\n'+SOURCE.read_text(encoding='utf-8').rstrip()+'\n</script>\n'+FIN
    if DEBUT in s:
        a,reste=s.split(DEBUT,1);_,b=reste.split(FIN,1);nouveau=a+bloc+b
    else:
        nouveau=s.replace('<script>',bloc+'\n<script>',1)
    if '--verifier' in sys.argv:
        if nouveau!=s:raise SystemExit('Bloc périmé : '+rel)
    else:p.write_text(nouveau,encoding='utf-8')
