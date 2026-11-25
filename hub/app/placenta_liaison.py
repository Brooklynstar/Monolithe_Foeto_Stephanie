# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Mesures communes aux deux trames : versions historiques et sauvegarde atomique."""
import copy
import datetime as dt
import json
import math
import re
from pathlib import Path

import ingest
import percentiles_placenta as pp
import placenta_redaction

PARTAGES = {'macro_01': ('paree', 'masse'), 'macro_03': ('galette', 'grand_axe'),
            'macro_04': ('galette', 'petit_axe'), 'macro_05': ('galette', 'epaisseur')}
DEFINITION = json.loads((Path(__file__).resolve().parent / 'placenta_formulaire.json').read_text(encoding='utf-8'))
LIBELLES = {c['id']: c['label'] for s in DEFINITION for c in s['champs']}


class Conflit(ingest.Refus):
    pass


def nombre(v):
    if isinstance(v, bool) or v is None:
        return None
    t = str(v).strip().replace(',', '.')
    if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)', t):
        return None
    n = float(t)
    return n if math.isfinite(n) else None


def champs(doc):
    return {k: v for s in doc.get('sections') or [] for k, v in (s.get('champs') or {}).items()}


def poser(doc, section, cle, valeur):
    bloc = next((s for s in doc.setdefault('sections', []) if s.get('id') == section), None)
    if bloc is None:
        bloc = {'id': section, 'champs': {}}
        doc['sections'].append(bloc)
    bloc.setdefault('champs', {})[cle] = valeur


def courantes(cx, numero):
    return {r['module']: dict(r) for r in cx.execute(
        "SELECT id,module,donnees_json,archive FROM saisies WHERE dossier=? AND courant=1 AND module IN ('administratif','placenta','macro_placenta')", (numero,))}


def contexte(cx, numero):
    lignes = courantes(cx, numero)
    docs = {k: json.loads(v['donnees_json']) for k, v in lignes.items()}
    macro, placenta = docs.get('macro_placenta', {}), docs.get('placenta', {})
    m, p = champs(macro), champs(placenta)
    valeurs = {cle: m[nom] for cle, (_, nom) in PARTAGES.items() if m.get(nom) is not None}
    divergences = [{'id': cle, 'label': LIBELLES[cle], 'placenta': p[cle], 'macro_placenta': valeurs[cle]}
                   for cle in valeurs if p.get(cle) not in (None, '') and nombre(p[cle]) != nombre(valeurs[cle])]
    issue = docs.get('administratif', {}).get('issue') or {}
    return {'versions': {k: lignes[k]['id'] if k in lignes else None for k in ('administratif', 'placenta', 'macro_placenta')},
            'valeurs': valeurs, 'divergences': divergences,
            'terme_sa': issue.get('terme_sa'),
            'conditions_masse': pp.conditions_document(macro) if macro else 'non_documentees'}


def resultat(cx, numero, doc):
    r = cx.execute("SELECT donnees_json FROM saisies WHERE dossier=? AND module='administratif' AND courant=1", (numero,)).fetchone()
    issue = (json.loads(r[0]).get('issue') or {}) if r else {}
    sa = issue.get('terme_sa')
    if sa is None:
        sa = nombre(doc.get('terme_sa'))
    return pp.calculer(sa, nombre(champs(doc).get('macro_01')), doc.get('conditions_masse', 'non_documentees'))


def original(racine, ligne):
    # Reprendre l'archive pour préserver aussi les clichés et leurs métadonnées.
    fichier = racine / ligne['archive']
    doc = json.loads(ligne['donnees_json'])
    if fichier.exists():
        return json.loads(fichier.read_text(encoding='utf-8-sig'))
    if doc.get('photos'):
        raise ingest.Refus('Archive Macro placenta introuvable : sauvegarde interrompue pour préserver les clichés.')
    return doc


def enregistrer(cx, racine, document):
    """Appelé dans une seule transaction ; ne crée jamais de Macro placenta vide."""
    doc = copy.deepcopy(document)
    numero, module = doc['dossier'], doc['module']
    avant = courantes(cx, numero)
    attendu = doc.pop('liaison_versions', None)
    if attendu is not None and attendu != contexte(cx, numero)['versions']:
        raise Conflit('Le dossier a changé dans un autre onglet. Relire depuis le hub avant d’enregistrer ; aucune valeur n’a été remplacée.')
    autres = []
    if module == 'placenta':
        doc['resultats_placentaires'] = resultat(cx, numero, doc)
        if doc.get('percentile_automatique') is True:
            poser(doc, 'macroscopie', 'macro_02', doc['resultats_placentaires']['position_percentile'] or '')
        if 'macro_placenta' in avant:
            macro = original(racine, avant['macro_placenta'])
            modifie = False
            actuels = champs(macro)
            for cle, (section, nom) in PARTAGES.items():
                v = nombre(champs(doc).get(cle))
                # Une réponse vide ou non numérique ne supprime pas une mesure existante.
                if v is not None and v != nombre(actuels.get(nom)):
                    poser(macro, section, nom, v)
                    modifie = True
            if doc.get('conditions_masse') and doc['conditions_masse'] != pp.conditions_document(macro):
                macro['conditions_masse'] = doc['conditions_masse']
                modifie = True
            if modifie:
                macro['resultats_placentaires'] = pp.document(macro, doc['resultats_placentaires']['terme_sa'])
                autres.append(macro)
    elif module == 'macro_placenta' and 'placenta' in avant:
        placenta = original(racine, avant['placenta'])
        ancien = copy.deepcopy(placenta)
        m = champs(doc)
        for cle, (_, nom) in PARTAGES.items():
            if nombre(m.get(nom)) is not None:
                poser(placenta, 'macroscopie', cle, str(m[nom]))
        placenta['conditions_masse'] = pp.conditions_document(doc)
        placenta['resultats_placentaires'] = resultat(cx, numero, placenta)
        if placenta.get('percentile_automatique') is True:
            poser(placenta, 'macroscopie', 'macro_02', placenta['resultats_placentaires']['position_percentile'] or '')
        if placenta != ancien:
            autres.append(placenta)
    for autre in autres:
        autre['operateur'] = doc.get('operateur')
        autre['exported_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
        autre.pop('liaison_versions', None)
        b = json.dumps(autre, ensure_ascii=False).encode()
        ingest.ingerer(cx, racine, b, f"{numero}_{autre['module']}.json", provenance='poste')
    brut = json.dumps(doc, ensure_ascii=False).encode()
    etat, message, sid = ingest.ingerer(cx, racine, brut, f'{numero}_{module}.json', provenance='poste')
    if autres:
        message += ' — mesures communes mises à jour dans les deux modules'
    return etat, message, sid


OPTIONS = {c['id']: c['choix'] for s in DEFINITION for c in s['champs'] if c['choix']}


def compte_rendu(cx, numero, doc):
    if not doc:
        return None
    valeurs = champs(doc)
    position = resultat(cx, numero, doc)['position_percentile']
    conditions = doc.get('conditions_masse')
    return {'sections': [
        {'titre': 'Macroscopie', 'lignes': placenta_redaction.macroscopie(
            valeurs, position, nombre, paree=conditions == 'fraiche_paree')},
        {'titre': 'Microscopie', 'lignes': placenta_redaction.microscopie(valeurs, OPTIONS)},
        {'titre': 'Conclusion', 'lignes': placenta_redaction.conclusion(valeurs)},
    ]}
