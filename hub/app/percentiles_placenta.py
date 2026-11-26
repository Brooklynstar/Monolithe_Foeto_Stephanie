# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Interpolation du rang entre les quantiles publiés, sans loi de distribution."""
import json
import math
from pathlib import Path
from percentiles import ecart_exact, zt, table

REFERENCES=Path(__file__).resolve().parent.parent/'references/placenta_percentiles.json'
BIBLIO_REDLINE = ('Redline RW, Boyd TK, Roberts DJ (dir.). Placental and Gestational Pathology. '
                  'Cambridge University Press, 2017, annexe 3, p. 336. DOI 10.1017/9781316848616.039.')
METHODE = 'Interpolation linéaire entre P10, P50 et P90 ; sans extrapolation ni loi normale.'


def libelle_percentile(resultat):
    p = resultat['percentile_numerique']
    if p is None:
        return resultat['position_percentile']
    libelle = f'P{p:g}'.replace('.', ',')
    return libelle + ' estimé' if resultat['percentile_interpole'] else libelle


def conditions_document(doc):
    if doc.get('conditions_masse'):
        return doc['conditions_masse']
    # Le module natif main nomme explicitement sa masse parée sur pièce fraîche.
    return 'fraiche_paree' if any(s.get('id')=='paree' and 'masse' in (s.get('champs') or {}) for s in doc.get('sections') or []) else 'non_documentees'


def calculer(sa, masse, conditions='non_documentees'):
    out={'terme_sa':sa,'masse_g':masse,'conditions_masse':conditions,'reference':'Redline',
         'z_brut':None,'position_percentile':None,'percentile_exact':None,
         'percentile_numerique':None,'percentile_interpole':None,
         'seuils':None,'motif':None,'methode':METHODE,
         'limite_mb':'Müller-Brochut : moyenne/ET présents dans le calculateur, distribution et protocole non établis ; aucun percentile exact déduit.'}
    if isinstance(sa,bool) or not isinstance(sa,(int,float)) or not math.isfinite(sa) or not float(sa).is_integer():
        out['motif']='Terme entier nécessaire, sans arrondi ni extrapolation.';return out
    if isinstance(masse,bool) or not isinstance(masse,(int,float)) or not math.isfinite(masse) or masse<0:
        out['motif']='Masse manquante ou invalide.';return out
    if conditions!='fraiche_paree':
        out['motif']='Référence non appliquée : préciser un poids frais paré ; poids fixé ou protocole inconnu non comparé.';return out
    refs=json.loads(REFERENCES.read_text(encoding='utf-8'))['Redline']
    ref=refs.get(str(int(sa)))
    if not ref or ref.get('source')!='Redline':
        out['motif']='Pas de quantiles publiés exploités à ce terme (22–42 SA) ; valeurs extrapolées 18–21 exclues.';return out
    out['z_brut']=ecart_exact(masse,ref['moyenne'],ref['sd'])
    out['seuils']={k:ref[k] for k in ('P10','P50','P90')}
    a,b,c=(ref[k] for k in ('P10','P50','P90'))
    out['position_percentile']=('P10' if masse==a else 'P50' if masse==b else 'P90' if masse==c else
                                '< P10' if masse<a else 'P10–P50' if masse<b else 'P50–P90' if masse<c else '> P90')
    if not a < b < c or not a <= masse <= c:
        return out
    bas, haut, p_bas = (a, b, 10) if masse <= b else (b, c, 50)
    p = p_bas + 40 * (masse - bas) / (haut - bas)
    out['percentile_numerique'] = math.floor(p * 10 + 0.5) / 10
    out['percentile_interpole'] = masse not in (a, b, c)
    return out


def document(doc,sa=None):
    champs={k:v for s in doc.get('sections') or [] for k,v in (s.get('champs') or {}).items()}
    return calculer(sa if sa is not None else champs.get('terme_sa'),champs.get('masse'),conditions_document(doc))


def tableau(r):
    return table(['Mesure','Valeur','Référence','Z-score','Percentile','Limite'],[
        ['Masse placentaire',str(r['masse_g'])+' g' if r['masse_g'] is not None else None,
         r['reference'],zt(r['z_brut']) if r['z_brut'] is not None else None,libelle_percentile(r),r['motif']]])


def texte(r):
    if r['position_percentile'] is None:return r['motif'] or ''
    return f"Masse placentaire : {r['masse_g']} g ; Redline {zt(r['z_brut'])} ; {libelle_percentile(r)}."
