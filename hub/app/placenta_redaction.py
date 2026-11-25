# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Rédaction à partir des seules constatations consignées dans le formulaire."""
import re


def phrase(texte):
    return texte.rstrip(' .,;:') + '.'


def majuscule(texte):
    return texte[:1].upper() + texte[1:]


def liste(elements):
    if len(elements) < 2:
        return ''.join(elements)
    return ', '.join(elements[:-1]) + ' et ' + elements[-1]


def libelle(texte):
    # Le relevé de la source contient des parenthèses tronquées. Conserver le
    # constat complet qui les précède, sans reconstituer les critères manquants.
    if texte.count('(') > texte.count(')'):
        texte = texte[:texte.rfind('(')]
    texte = texte.rstrip(' .,;:')
    texte = re.sub(r'(?<=\d)\s*%', ' %', texte)
    texte = re.sub(r':\s*(réponse inflammatoire)', r' avec \1', texte)
    texte = re.sub(r'\((RIM|RIF)\) stade', r'(\1) de stade', texte)
    for ancien, nouveau in (
        ('aigue', 'aiguë'), ('foetalec', 'fœtale '), ('foetale', 'fœtale'),
        ('inflammtoire', 'inflammatoire'), ('cubigue', 'cubique'),
        ('avaculaires', 'avasculaires'), ('esamine', 'examiné'),
        ('choricallantordiens', 'chorioallantoïdiens'),
        ('chorioallantoidiens', 'chorioallantoïdiens'), ('caryorrhexxie', 'caryorrhexie'),
        ('maternal foor infarct', 'maternal floor infarct'),
        ('sur environ % du parenchyme examiné', ''),
        ('villosités de grande taille, anfractueuses, présentant', 'villosités de grande taille et anfractueuses'),
        (' fréquemment retrouvées dans les aneuploïdes ou', ''),
        ('(ex-NIDF)de', '(ex-NIDF) de'), ('( RIF', '(RIF'), ('( infiltrat', '(infiltrat'),
    ):
        texte = texte.replace(ancien, nouveau)
    if texte.startswith('de grade '):
        texte = texte.replace(' - ', ', ', 1)
    return texte.replace("'", "’").strip()


def choix_bruts(valeur):
    if isinstance(valeur, dict):
        texte = valeur.get('texte')
        return [texte if v == 'Autre + texte libre' else v for v in choix_bruts(valeur.get('choix'))]
    options = valeur if isinstance(valeur, list) else [valeur]
    return [v for v in options if isinstance(v, str) and v.strip()]


COMPOSITION_TROIS_VAISSEAUX = re.compile(r'deux artères(?: et)? une veine', re.I)


def macroscopie(valeurs, position, nombre, *, paree=False):
    def mesure(i):
        n = nombre(valeurs.get(f'macro_{i:02}'))
        return format(n, '.15g').replace('.', ',') if n is not None and n >= 0 else ''

    def choix(i):
        return [libelle(v) for v in choix_bruts(valeurs.get(f'macro_{i:02}')) if v]

    def dimensions(taille, epaisseur):
        if taille and epaisseur:
            return f' de {taille} cm de grand axe sur {epaisseur} cm d’épaisseur'
        if taille:
            return f' de {taille} cm de grand axe'
        if epaisseur:
            return f' de {epaisseur} cm d’épaisseur'
        return ''

    lignes = []
    poids, longueur, largeur, epaisseur = (mesure(i) for i in (1, 3, 4, 5))
    elements = []
    if poids:
        poids = f'pèse {poids} g'
        if position:
            poids += f' ({position}, Redline)'
        if paree:
            poids += ", sans les membranes ni le cordon"
        elements.append(poids)
    if longueur and largeur:
        dimension = f'mesure {longueur} × {largeur} cm'
        if epaisseur:
            dimension += f' sur {epaisseur} cm d’épaisseur'
        elements.append(dimension)
    else:
        dimensions_disponibles = [f'{v} cm {unite}' for v, unite in
                                  ((longueur, 'de longueur'), (largeur, 'de largeur'),
                                   (epaisseur, 'd’épaisseur')) if v]
        if dimensions_disponibles:
            elements.append('mesure ' + liste(dimensions_disponibles))
    formes = {'bi-partita': 'bipartite', 'tripartita': 'tripartite'}
    formes_saisies = [formes.get(v.casefold(), v.casefold()) for v in choix(6)]
    avec_lobe = 'lobe accessoire' in formes_saisies
    formes_saisies = [v for v in formes_saisies if v != 'lobe accessoire']
    if elements:
        sujet = 'La galette placentaire' if formes_saisies or paree else 'Le placenta'
        if formes_saisies:
            sujet += ', de forme ' + liste(formes_saisies) + ','
        liaison = ', et ' if paree and len(elements) == 2 else ' et '
        lignes.append(phrase(sujet + ' ' + liaison.join(elements)))
    elif formes_saisies:
        lignes.append(phrase('La galette placentaire est de forme ' + liste(formes_saisies)))
    if avec_lobe:
        lignes.append('La galette placentaire présente un lobe accessoire.')

    insertion = ['circumvallée' if v.casefold() == 'circumvalee' else v.casefold()
                 for v in choix(7) if v.casefold() != 'autre']
    cordon = choix(8)
    trois_vaisseaux = any(COMPOSITION_TROIS_VAISSEAUX.fullmatch(v) for v in cordon)
    descriptions = {'artère ombilicale unique': 'présente une artère ombilicale unique',
                    'hyperspiralé': 'est hyperspiralé',
                    'Thrombose vasculaire': 'présente une thrombose vasculaire'}
    constats = []
    if trois_vaisseaux:
        constats.append('comporte trois vaisseaux')
    constats.extend(descriptions.get(v, f'est décrit comme suit : {v}') for v in cordon
                    if not COMPOSITION_TROIS_VAISSEAUX.fullmatch(v))
    if constats:
        sujet = 'Le cordon' + (', d’insertion ' + liste(insertion) + ',' if insertion else '')
        lignes.append(phrase(sujet + ' ' + liste(constats)))
    elif insertion:
        lignes.append(phrase('L’insertion du cordon est ' + liste(insertion)))
    plaque = {'Amnios noueux': 'un amnios noueux', 'Métaplasie malpighienne': 'une métaplasie malpighienne',
              'Kystes': 'des kystes'}
    if observations := choix(9):
        lignes.append(phrase('La plaque choriale présente ' + liste([plaque.get(v, v) for v in observations])))

    n, surface, minimum, maximum = (mesure(i) for i in range(10, 14))
    if n == '0':
        lignes.append('À la coupe, il n’est pas observé d’infarctus.')
    elif any((n, surface, minimum, maximum)):
        quantite = {'1': 'un', '2': 'deux', '3': 'trois'}.get(n, n or 'des')
        description = f'À la coupe, on observe {quantite} infarctus'
        suite = []
        if surface:
            suite.append(f'représentant {surface} % de la surface de la galette placentaire')
        if minimum and maximum:
            suite.append(f'mesurant de {minimum} à {maximum} cm de grand axe')
        elif minimum or maximum:
            borne = 'au minimum' if minimum else 'au maximum'
            suite.append(f'mesurant {borne} {minimum or maximum} cm de grand axe')
        lignes.append(phrase(description + (' ' + liste(suite) if suite else '')))
    infarctus = n != '0' and any((n, surface, minimum, maximum))
    n, taille, epaisseur = (mesure(i) for i in range(14, 17))
    if n == '0':
        lignes.append('Il n’est pas observé de thrombose sous-choriale.')
    elif any((n, taille, epaisseur)):
        lesion = f'{n} thromboses sous-choriales' if n and n != '1' else 'une thrombose sous-choriale'
        lignes.append(phrase('On observe ' + ('aussi ' if infarctus else '')
                             + lesion + dimensions(taille, epaisseur)))
    taille, epaisseur = mesure(17), mesure(18)
    if taille or epaisseur:
        lignes.append(phrase('On observe un hématome décidual basal' + dimensions(taille, epaisseur)))
    n, taille = mesure(19), mesure(20)
    if n == '0':
        lignes.append('Il n’est pas observé de kyste trophoblastique.')
    elif n or taille:
        lesion = f'{n} kystes trophoblastiques' if n and n != '1' else 'un kyste trophoblastique'
        lignes.append(phrase(f'On observe {lesion}' + (f' de {taille} cm de grand axe' if taille else '')))
    if v := valeurs.get('macro_21'):
        lignes.append(phrase(f'Thrombose intervilleuse : {v}'))
    return lignes


# Les indices correspondent aux options du relevé et à leurs valeurs persistées.
# Chaque groupe associe ses propres qualificatifs à son ou ses constats possibles.
INFLAMMATION = ((range(1, 4), range(4, 6)),)
GROUPES = {
    'micro_02': INFLAMMATION,
    'micro_03': ((range(8, 11), range(11, 13)),),
    'micro_06': ((range(3), range(3, 5)),),
    'micro_08': (
        ((1,), (2, 3)), ((4,), (5, 6)), ((7,), range(8, 15)),
        ((15,), range(16, 23)), ((23,), (24, 25)),
    ),
}


def observations(cle, valeurs, options):
    bruts = choix_bruts(valeurs.get(cle))
    coches = {i: libelle(v) for i, v in enumerate(options) if v in bruts}
    notes = []
    for lesions, qualificatifs in GROUPES.get(cle, ()):
        parents = [i for i in lesions if i in coches]
        details = [coches.pop(i) for i in qualificatifs if i in coches]
        if not details:
            continue
        if len(parents) == 1:
            i = parents[0]
            coches[i] += ' (' + liste(details) + ')'
        else:
            notes.append('précisions à rattacher à la lésion lors de la relecture : ' + liste(details))
    elements = list(coches.values()) + [libelle(v) for v in bruts if v not in options]
    return elements, notes


def microscopie(valeurs, options):
    sujets = {
        'micro_01': 'L’amnios est',
        'micro_02': 'Les membranes présentent les aspects suivants :',
        'micro_03': 'Au niveau du cordon, on observe les éléments suivants :',
        'micro_04': 'L’amnios de la plaque choriale est',
        'micro_05': 'Au niveau de la plaque choriale, l’examen vasculaire retrouve les éléments suivants :',
        'micro_06': 'L’examen de la plaque choriale retrouve les lésions inflammatoires suivantes :',
        'micro_07': 'L’examen de la plaque basale montre les éléments suivants :',
        'micro_08': 'Les villosités présentent les aspects suivants :',
        'micro_09': 'Dans la chambre intervilleuse, on observe les éléments suivants :',
        'micro_10': 'L’examen microscopique retrouve les éléments focaux suivants :',
    }
    lignes = []
    for cle, sujet in sujets.items():
        faits, notes = observations(cle, valeurs, options[cle])
        if faits or notes:
            if len(faits) == 1:
                fait = faits[0]
                if cle in ('micro_02', 'micro_06') and fait.startswith(
                    ('sous-chorionite', 'chorioamniotite')
                ):
                    structure = 'Les membranes' if cle == 'micro_02' else 'La plaque choriale'
                    sujet = f'{structure} présentent' if cle == 'micro_02' else f'{structure} présente'
                    faits = ['une ' + fait]
                elif cle == 'micro_03' and fait.startswith(('phlébite', 'vasculite', 'funiculite')):
                    sujet, faits = 'Au niveau du cordon, on observe', ['une ' + fait]
                elif cle == 'micro_09' and fait.startswith('intervillite chronique'):
                    sujet, faits = 'Dans la chambre intervilleuse, on observe', ['une ' + fait]
            contenu = ' ; '.join(filter(None, (liste(faits), *notes)))
            lignes.append(phrase(f'{sujet} {contenu}'))
    return lignes


def conclusion(valeurs):
    lignes = []
    grades = set()
    for v in choix_bruts(valeurs.get('conclusion_01')):
        texte = libelle(v).replace('5-10 %', '5–10 %').replace('10-50 %', '10–50 %')
        grade = re.search(r'\b(III|II|I)\s*\(', texte) if 'intervillite chronique' in texte else None
        if grade:
            grades.add({'I': 1, 'II': 2, 'III': 3}[grade[1]])
            lignes.append(phrase(majuscule(texte.removeprefix('une '))))
        elif texte in ('hypotrophique', 'eutrophique', 'hypertrophique'):
            lignes.append(phrase('Le placenta est ' + texte))
        elif texte.startswith(('des ', 'une ', 'un ')):
            lignes.append(phrase('L’examen met en évidence ' + texte))
        else:
            lignes.append(phrase(majuscule(texte)))
    grades_micro = {int(g[1]) for v in choix_bruts(valeurs.get('micro_09'))
                    if 'intervillite chronique' in v and (g := re.search(r'\bgrade ([123])\b', v))}
    if grades and grades_micro and grades != grades_micro:
        micro = liste([str(i) for i in sorted(grades_micro)])
        final = liste([{1: 'I', 2: 'II', 3: 'III'}[i] for i in sorted(grades)])
        lignes.append(f'À relire : la microscopie indique un grade {micro} pour l’intervillite '
                      f'chronique, alors que la conclusion indique {final}.')
    return lignes
