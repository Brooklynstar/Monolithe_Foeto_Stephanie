# SPDX-License-Identifier: CC-BY-NC-SA-4.0
import json
import math
from pathlib import Path
from copy import deepcopy
from percentiles import ecart_exact, percentile, pt, zt, table


def detail(ligne):
    bouts=[]
    for src in ('gc','ma','mb'):
        z=ligne.get('z_brut_'+src)
        if z is None:z=ligne.get('z_'+src)
        if z is None and src=='gc' and 'z_gc' not in ligne:z=ligne.get('ds')
        if z is not None:
            bouts.append(src.upper()+' '+zt(z)+((' · '+pt(ligne['percentile_'+src])) if ligne.get('percentile_'+src) is not None else ''))
    return ' ; '.join(bouts)


def table_organes(lignes):
    titres=['Mesure','Valeur']
    for src in ('GC','MA','MB'):titres += ['Z-score '+src,'Percentile '+src]
    rows=[]
    for l in lignes:
        row=[(l.get('label') or l.get('id') or '')+(' ⚠' if l.get('alerte') else ''),l.get('detail') or str(l.get('valeur'))+' g']
        for src in ('gc','ma','mb'):
            z=l.get('z_brut_'+src)
            if z is None:z=l.get('z_'+src)
            if z is None and src=='gc' and 'z_gc' not in l:z=l.get('ds')
            row += [zt(z) if z is not None else None,pt(l['percentile_'+src]) if l.get('percentile_'+src) is not None else None]
        rows.append(row)
    return table(titres,rows)


def neuropath(neu, sa, racine=None):
    neu=deepcopy(neu)
    chemins=([Path(racine)/'references/neuropath_masses.json'] if racine else [])+[Path(__file__).resolve().parent.parent/'references/neuropath_masses.json']
    tables=next((json.loads(p.read_text(encoding='utf-8')) for p in chemins if p.is_file()),{})
    rows=[]
    try:terme=float(sa)
    except (TypeError,ValueError):terme=math.nan
    for e in neu.get('etapes') or []:
        for c in e.get('champs') or []:
            ref={'masse_enc':'REF_ME','masse_cerv':'REF_MI'}.get(c.get('id'))
            if not ref or c.get('valeur') is None:continue
            r=None
            if math.isfinite(terme) and terme.is_integer():
                for bande,v in tables.get(ref,{}).items():
                    b=[int(x) for x in bande.split('-')]
                    if b[0]<=terme<=b[-1]:r=v;break
            zz=ecart_exact(c['valeur'],r['m'],r['s']) if r else None
            ancien=c.get('zscore') or {}
            # Ne jamais reconstruire un percentile à partir du Z historique arrondi.
            c['zscore']={**ancien,'z_archive':ancien.get('z'),
                         'z':round(zz,2) if zz is not None else None,
                         'z_brut':zz,'percentile':percentile(zz),
                         'attendu_m':r['m'] if r else None,'attendu_sd':r['s'] if r else None,
                         'reference':ref[-2:],'source':'Guihard-Costa 2002 / Maroun 2017',
                         'motif':None if r else 'Référence de masse indisponible à ce terme.'}
            rows.append({'id':c['id'],'label':c.get('label') or c['id'],'valeur':c['valeur'],'unite':c.get('unite') or 'g',**c['zscore']})
    return neu,rows


def table_neuro(lignes):
    return table(['Mesure','Valeur','Attendu (moy. ± ET)','Z-score','Percentile','Référence','Limite'],[
        [l['label'],str(l['valeur'])+' '+l['unite'],
         str(l['attendu_m'])+' ± '+str(l.get('attendu_sd')) if l.get('attendu_m') is not None else None,
         zt(l.get('z_brut') if l.get('z_brut') is not None else l.get('z')),
         pt(l['percentile']) if l.get('percentile') is not None else None,l.get('source') or l.get('reference'),l.get('motif')]
        for l in lignes])
