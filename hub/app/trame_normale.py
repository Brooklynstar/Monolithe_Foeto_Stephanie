# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Brouillon Google Forms et constatations explicitement validées pour l’examen externe."""
import json
import re


def lire(cx):
    row = cx.execute('SELECT document FROM trame_normale WHERE id=1').fetchone()
    return json.loads(row[0]) if row else {'revision': 0, 'blocs': []}


def importer(source):
    if not isinstance(source, dict) or not isinstance(source.get('items'), list):
        raise ValueError('Un export JSON forms.get contenant items est attendu.')
    info = source.get('info') or {}
    blocs = [{'id': 'initial', 'titre': info.get('title') or 'Formulaire', 'items': []}]
    ids = set()
    embranchements = False
    for item in source['items']:
        identifiant = item.get('itemId') if isinstance(item, dict) else None
        if not isinstance(identifiant, str) or not identifiant or identifiant in ids:
            raise ValueError('Chaque item doit porter un itemId unique.')
        ids.add(identifiant)
        if 'pageBreakItem' in item:
            blocs.append(dict(id=identifiant, titre=item.get('title') or 'Section', items=[], source=item))
            continue
        question = (item.get('questionItem') or {}).get('question') or {}
        options = (question.get('choiceQuestion') or {}).get('options') or []
        embranchements |= any(o.get('goToSectionId') or o.get('goToAction') for o in options)
        blocs[-1]['items'].append(dict(id=identifiant, titre=item.get('title') or '',
                                      numero_pdf=item.get('numero_pdf'),
                                      choix=[o.get('value', '') for o in options],
                                      cible='', phrase='', source=item))
    return {'titre': info.get('title'), 'embranchements': embranchements, 'blocs': blocs,
            'source_pdf': source.get('source_pdf')}


def actifs(trame):
    return {i['id']: i for b in trame['blocs'] for i in b['items'] if i['cible'] and i['phrase']}


def sauvegarder(cx, corps):
    if not isinstance(corps, dict):
        raise ValueError('Objet JSON attendu.')
    courant = lire(cx)
    if corps.get('revision') != courant['revision']:
        raise ValueError('La trame a changé. Rouvrir la configuration avant de continuer.')
    if 'source' in corps:
        if courant['blocs']:
            raise ValueError('Une trame existe déjà. L’import initial ne peut pas la remplacer.')
        doc = importer(corps['source'])
    else:
        modifications = corps.get('items')
        if not isinstance(modifications, dict):
            raise ValueError('Configuration des items attendue.')
        doc = courant
        for bloc in doc['blocs']:
            bloc['items'] = [i for i in bloc['items'] if i['id'] in modifications]
            for i in bloc['items']:
                m = modifications[i['id']]
                cible, phrase = m.get('cible', ''), m.get('phrase', '')
                if not isinstance(cible, str) or not isinstance(phrase, str):
                    raise ValueError('Champ Monolithe et phrase médicale attendus.')
                if cible and not re.fullmatch(r'[a-z0-9_]+', cible):
                    raise ValueError('Identifiant Monolithe invalide.')
                if cible and doc.get('embranchements'):
                    raise ValueError('Les embranchements sont conservés dans le brouillon. Leur exécution doit être raccordée avant activation.')
                i.update(cible=cible, phrase=phrase.strip())
        doc['blocs'] = [b for b in doc['blocs'] if b['id'] in corps.get('blocs', [])]
    doc['cibles'] = sorted(set(doc.get('cibles', [])) | {i['cible'] for i in actifs(doc).values()})
    doc['revision'] = courant['revision'] + 1
    cx.execute('INSERT INTO trame_normale VALUES (1, ?) ON CONFLICT(id) DO UPDATE SET document=excluded.document',
               (json.dumps(doc, ensure_ascii=False),))
    return doc


# Le numéro relie chaque constatation au tri du PDF, même lorsque plusieurs
# phrases de la question portent sur des structures anatomiques distinctes.
EXAMEN_EXTERNE = (
    (103, 'teguments', 'peau', 'La peau est sans anomalie.', ()),
    (104, 'crane', 'visage', 'Le visage présente un aspect général harmonieux.', ()),
    (104, 'fontanelles', 'fontanelles', 'Les fontanelles et les sutures sont d’aspect normal.', ()),
    (104, 'cheveux', 'cheveux', 'L’implantation des cheveux est normale.', ()),
    (104, 'yeux', 'yeux', 'Les yeux sont symétriques, sans hyper ni hypotélorisme.', ()),
    (104, 'nez', 'racine', 'La racine du nez est normale.', ('racine', 'ensellure', 'arête', 'aplasie')),
    (104, 'nez', 'narines', 'Les narines sont normales.', ('narine', 'aile', 'aplasie')),
    (104, 'nez', 'choanes', 'Les choanes sont perméables.', ('choane', 'aplasie')),
    (104, 'bouche', 'philtrum', 'Le philtrum est normal.', ('philtrum',)),
    (104, 'bouche', 'fente', 'Il n’est pas observé de fente labio-palatine.', ('fente', 'palais')),
    (104, 'bouche', 'luette', 'La luette est normale.', ('luette',)),
    (104, 'bouche', 'retrognathisme', 'Il n’est pas observé de rétrognathisme.', ('rétrognath',)),
    (104, 'oreilles', 'implantation', 'Les oreilles sont normalement implantées et ourlées.', ()),
    (104, 'oreilles', 'conduits', 'Les conduits auditifs externes sont perméables.', ('conduit', 'anotie', 'atrésie')),
    (114, 'thorax', 'mamelons', 'Les mamelons sont normalement positionnés.', ('mamelon',)),
    (114, 'cordon', 'insertion', 'L’implantation fœtale du cordon est en position normale.', ('insertion',)),
    (114, 'abdomen', 'paroi', 'Il n’est pas mis en évidence de défaut de fermeture de la paroi abdominale.', ('omphalocèle', 'laparoschisis', 'paroi')),
    (114, 'dos', 'fermeture', 'Il n’est pas mis en évidence de défaut de fermeture du tube neural.', ('spina', 'tube neural', 'myéloméningocèle')),
    (115, 'abdomen', 'abdomen', 'L’abdomen est d’aspect normal.', ()),
    (116, 'oge', 'masculin', 'Les organes génitaux externes sont de type masculin, bien différenciés.', ()),
    (116, 'oge', 'feminin', 'Les organes génitaux externes sont de type féminin, bien différenciés.', ()),
    (117, 'anus', 'perinee', 'Le périnée est normal, sans malposition anale.', ()),
    (117, 'anus', 'anus', 'L’anus est perméable et le rectum renferme du méconium.', ()),
    (118, 'membres_sup', 'segments', 'Les membres supérieurs sont harmonieux, comportant trois segments.', ()),
    (118, 'mains', 'doigts', 'Les mains comportent chacune cinq doigts, sans syndactylie ni clinodactylie.', ('doigt', 'dactyl', 'pouce')),
    (118, 'ongles', 'ongles', 'Les doigts portent des ongles.', ()),
    (118, 'mains', 'plis', 'Deux plis palmaires sont présents au niveau de chaque paume.', ('pli',)),
    (119, 'mains', 'mains', 'Les mains et les doigts sont d’aspect normal.', ()),
    (120, 'membres_inf', 'segments', 'Les membres inférieurs comportent trois segments sans malposition.', ()),
    (120, 'membres_inf', 'rotules', 'Les rotules sont palpées.', ('rotule',)),
    (120, 'pieds_morpho', 'orteils', 'Les pieds comportent cinq orteils, sans syndactylie.', ('orteil', 'dactyl')),
    (121, 'pieds_morpho', 'pieds', 'Les pieds et les orteils sont d’aspect normal.', ()),
)
# Le tri enregistré dans le Hub prévaut sur ces questions distribuées avec le module.
QUESTIONS_EXTERNE = {n for n, *_ in EXAMEN_EXTERNE}


def constatations_externes(trame):
    est_pdf = bool(trame.get('source_pdf'))
    if trame['revision'] and not est_pdf:
        return actifs(trame)
    numeros = {i.get('numero_pdf') for bloc in trame['blocs'] for i in bloc['items']} if est_pdf else QUESTIONS_EXTERNE
    options = {}
    for n, cible, cle, phrase, incompatibles in EXAMEN_EXTERNE:
        if n in numeros:
            identifiant = f'pdf-q{n}-{cle}'
            options[identifiant] = dict(id=identifiant, cible=cible, phrase=phrase, incompatibles=incompatibles)
            if n == 116:
                options[identifiant]['groupe'] = 'type_oge'
    personnalises = actifs(trame)
    for i in personnalises.values():
        options = {k: v for k, v in options.items()
                   if not (k.startswith(f"pdf-q{i.get('numero_pdf')}-") and v['cible'] == i['cible'])}
    options.update(personnalises)
    return options


# Les choix composés sont divisés aux endroits où un constat peut être
# infirmé indépendamment, notamment pour les valves et les vaisseaux du cœur.
AUTOPSIE = {
    135: ('ouverture', (
        ('serosites', 'À l’ouverture, il existe des épanchements sérohématiques dans l’ensemble des séreuses, en relation avec la macération.', ()),
        ('organes', 'Les organes examinés sont en place sans anomalie de forme ni de position.', ()),
        ('situs', 'Les situs sont respectés.', ('situs',)),
    )),
    136: ('thorax', (
        ('thyroide', 'La thyroïde est d’aspect normal.', ()),
    )),
    137: ('thorax', (
        ('thymus', 'Le thymus est en place et d’aspect normal.', ('thymus_aspect',)),
    )),
    138: ('thorax', (
        ('oesophage', 'L’œsophage est perméable sans fistule ni atrésie.', ('voies_aer',)),
    )),
    139: ('thorax', (
        ('larynx', 'On ne met pas en évidence de lésion laryngée.', ('voies_aer',)),
        ('prelevement', 'Le larynx et la thyroïde sont prélevés.', ()),
        ('trachee', 'La trachée est perméable.', ('voies_aer',)),
    )),
    140: ('poumons', (
        ('lobation', 'Les poumons sont bien lobulés.', ('poumon_d_aspect', 'poumon_g_aspect')),
        ('hypoplasie', 'Le rapport poids pulmonaire total / poids fœtal est normal : pas d’hypoplasie pulmonaire.',
         ('poumon_d_aspect', 'poumon_g_aspect')),
    )),
    141: ('coeur', (
        ('apex', 'L’apex est orienté à gauche.', ('pointe',)),
        ('sillon', 'Le sillon du septum interventriculaire est bien marqué.', ('septum_iv',)),
        ('auricules', 'Les auricules sont conformes.', ()),
        ('caves', 'Les veines caves sont présentes au niveau de l’oreillette droite.', ()),
        ('veines', 'Les veines pulmonaires sont présentes au niveau de l’oreillette gauche.', ('rvp_d', 'rvp_g')),
        ('oreillettes', 'Les deux oreillettes sont conformes.', ('quatre_cav',)),
        ('foramen', 'Le foramen ovale est perméable.', ('foramen_ovale',)),
        ('mitrale', 'La valve mitrale est sans anomalie.', ('valves',)),
        ('tricuspide', 'La valve tricuspide est sans anomalie.', ('valves',)),
        ('ventricules', 'Les deux ventricules sont conformes.', ('quatre_cav',)),
        ('civ', 'Il n’est pas observé de communication interventriculaire.', ('septum_iv',)),
        ('vaisseaux', 'Les deux gros vaisseaux de la base sont en place et de calibre équivalent.', ('gros_vx',)),
        ('artere', 'L’artère pulmonaire fait suite au ventricule droit.', ('gros_vx',)),
        ('valve_pulmonaire', 'La valve pulmonaire est sans anomalie.', ('valves',)),
        ('bifurcation', 'La bifurcation pulmonaire est normale.', ()),
        ('aorte', 'L’aorte fait suite au ventricule gauche.', ('gros_vx',)),
        ('valve_aortique', 'La valve aortique est sans anomalie.', ('valves',)),
        ('tsa', 'Les troncs supra-aortiques sont en place.', ('tsa',)),
        ('crosse', 'La crosse aortique est à gauche.', ('crosse', 'tsa')),
        ('descendante', 'L’aorte descendante est à gauche.', ('crosse',)),
        ('canal', 'Le canal artériel est perméable.', ('canal_art',)),
    )),
    142: ('digestif', (
        ('foie', 'Le foie est en place avec la vésicule biliaire.', ('foie_aspect', 'vb')),
        ('arantius', 'L’Arantius est perméable.', ()),
        ('rate', 'La rate est en place.', ('rate_aspect',)),
        ('pancreas', 'Le pancréas est présent dans le cadre duodénal, de longueur normale.', ('pancreas_aspect',)),
        ('estomac', 'L’estomac est en place, de volume habituel pour le terme.', ('estomac',)),
        ('intestins', 'Les intestins sont en place sans malrotation, ni fistule ni atrésie.', ('tube_dig',)),
    )),
}

# Une anomalie de valve ne doit pas écarter le texte sur les trois autres.
MOTS_AUTOPSIE = {
    'mitrale': ('mitral',), 'tricuspide': ('tricusp', 'ebstein'),
    'valve_pulmonaire': ('pulmonaire',), 'valve_aortique': ('aort',),
    'oesophage': ('œsophag', 'oesophag', 'fistule'), 'larynx': ('laryng',),
    'trachee': ('traché', 'trache'), 'lobation': ('lobation', 'lobul'),
    'hypoplasie': ('hypoplasi',),
    'oreillettes': ('oreillet',), 'crosse': ('arc aortique droit', 'crosse droite'),
    'descendante': ('descendante',),
}


def constatations_autopsie(trame):
    options = {}
    for bloc in trame['blocs']:
        for item in bloc['items']:
            n = item.get('numero_pdf')
            if n not in AUTOPSIE:
                continue
            etape, choix = AUTOPSIE[n]
            if item.get('phrase'):
                options[item['id']] = dict(id=item['id'], etape=etape, phrase=item['phrase'],
                                           cibles=[item['cible']] if item.get('cible') else [], mots=[])
                continue
            for cle, phrase, cibles in choix:
                identifiant = f'pdf-q{n}-{cle}'
                options[identifiant] = dict(id=identifiant, etape=etape, phrase=phrase,
                                           cibles=cibles, mots=MOTS_AUTOPSIE.get(cle, ()),
                                           manuel=cle in {'prelevement', 'serosites'})
    return options


def incompatible(option, anomalies, precision, anomalie_attestee):
    if not anomalie_attestee:
        return False
    mots = option.get('incompatibles') or ()
    if not mots or precision or not anomalies:
        return True
    return any(mot.casefold() in libelle.casefold() for mot in mots for libelle in anomalies)
