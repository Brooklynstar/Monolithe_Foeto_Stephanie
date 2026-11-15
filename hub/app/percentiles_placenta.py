# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Position parmi les quantiles publiés ; aucun modèle gaussien supposé."""
import json
import math
from pathlib import Path
from percentiles import ecart_exact, zt, table

REFERENCES=Path(__file__).resolve().parent.parent/'references/placenta_percentiles.json'


def conditions_document(doc):
    if doc.get('conditions_masse'):
        return doc['conditions_masse']
    # Le module natif main nomme explicitement sa masse parée sur pièce fraîche.
    return 'fraiche_paree' if any(s.get('id')=='paree' and 'masse' in (s.get('champs') or {}) for s in doc.get('sections') or []) else 'non_documentees'


def calculer(sa, masse, conditions='non_documentees'):
    out={'terme_sa':sa,'masse_g':masse,'conditions_masse':conditions,'reference':'Redline',
         'z_brut':None,'position_percentile':None,'percentile_exact':None,
         'seuils':None,'motif':None,'methode':'position parmi P10, P50, P90 publiés ; pas de loi normale ni interpolation',
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
    return out


def document(doc,sa=None):
    champs={k:v for s in doc.get('sections') or [] for k,v in (s.get('champs') or {}).items()}
    return calculer(sa if sa is not None else champs.get('terme_sa'),champs.get('masse'),conditions_document(doc))


def tableau(r):
    return table(['Mesure','Valeur','Référence','Z-score','Position percentile','Limite'],[
        ['Masse placentaire',str(r['masse_g'])+' g' if r['masse_g'] is not None else None,
         r['reference'],zt(r['z_brut']) if r['z_brut'] is not None else None,r['position_percentile'],r['motif']]])


def texte(r):
    if r['position_percentile'] is None:return r['motif'] or ''
    return 'Masse placentaire : '+str(r['masse_g'])+' g ; Redline '+zt(r['z_brut'])+' ; '+r['position_percentile']+' (position parmi les seuils publiés, percentile exact non déterminable).'
