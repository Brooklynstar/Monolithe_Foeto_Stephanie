# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Rédaction à partir des seules constatations consignées dans le formulaire."""
import re
from percentiles import zt


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
    return [ligne for _, lignes in macroscopie_sections(valeurs, position, nombre, paree=paree, modele_word=False)
            for ligne in lignes]


def macroscopie_sections(valeurs, position, nombre, *, paree=False, z_brut=None, modele_word=True):
    def valeur_mesuree(cle):
        n = nombre(valeurs.get(cle))
        return format(n, '.15g').replace('.', ',') if n is not None and n >= 0 else ''

    def mesure(i):
        return valeur_mesuree(f'macro_{i:02}')

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

    def ajouter_remarque(cle, label):
        if v := valeurs.get(cle):
            lignes.append(phrase(f'{label} : {v}'))

    sections = []
    lignes = []
    poids, longueur, largeur, epaisseur = (mesure(i) for i in (1, 3, 4, 5))
    elements = []
    if poids:
        poids = f'pèse {poids} g'
        if position:
            comparaison = f'{position}, {zt(z_brut)}' if z_brut is not None else position
            poids += f' ({comparaison} selon Redline)'
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
    completude = choix_bruts(valeurs.get('releve_completude'))
    etat_galette = [v.lower() for v in completude if v in ('Complète', 'Déchirée')]
    description = liste(etat_galette + (['de forme ' + liste(formes_saisies)] if formes_saisies else []))
    if elements:
        sujet = 'La galette placentaire' if formes_saisies or paree else 'Le placenta'
        if description:
            sujet = f'La galette placentaire, {description},'
        liaison = ', et ' if paree and len(elements) == 2 else ' et '
        lignes.append(phrase(sujet + ' ' + liaison.join(elements)))
    elif description:
        lignes.append(phrase('La galette placentaire est ' + description))
    if avec_lobe:
        lignes.append('La galette placentaire présente un lobe accessoire.')
    if prelevements := [v.lower() for v in completude if v not in ('Complète', 'Déchirée')]:
        lignes.append(phrase('Prélèvement de la galette : ' + liste(prelevements)))
    sections.append(('Galette placentaire', lignes))

    lignes = []
    insertion_membranes = valeurs.get('releve_membranes_insertion')
    aspect_membranes = {'Normal': 'd’aspect normal', 'Opaques': 'opaques', 'Beiges': 'beiges'}.get(
        valeurs.get('releve_membranes_aspect'))
    if insertion_membranes:
        pct = nombre(valeurs.get('releve_membranes_marginee_pct'))
        suite = (f' sur {format(pct, ".15g").replace(".", ",")} % de la circonférence'
                 if pct is not None and 0 <= pct <= 100 and insertion_membranes in ('Marginée', 'Circumvallée') else '')
        insertion_membranes = 'd’insertion ' + insertion_membranes.lower() + suite
    if constat_membranes := ', '.join(filter(None, (aspect_membranes, insertion_membranes))):
        lignes.append(phrase('Les membranes sont ' + constat_membranes))
    ajouter_remarque('releve_remarques_membranes', 'Membranes')
    sections.append(('Membranes', lignes))

    lignes = []
    insertion = ['circumvallée' if v.casefold() == 'circumvalee' else v.casefold()
                 for v in choix(7) if v.casefold() != 'autre']
    cordon = choix(8)
    trois_vaisseaux = any(COMPOSITION_TROIS_VAISSEAUX.fullmatch(v) for v in cordon)
    descriptions = {'artère ombilicale unique': 'présente une artère ombilicale unique',
                    'Thrombose vasculaire': 'présente une thrombose vasculaire'}
    if not modele_word:
        descriptions['hyperspiralé'] = 'est hyperspiralé'
    constats = []
    longueur_cordon = nombre(valeurs.get('releve_cordon_longueur'))
    if longueur_cordon is not None and longueur_cordon >= 0:
        constats.append(f'mesure {format(longueur_cordon, ".15g").replace(".", ",")} cm')
    if trois_vaisseaux:
        constats.append('comporte trois vaisseaux')
    constats.extend(descriptions.get(v, f'est décrit comme suit : {v}') for v in cordon
                    if (v != 'hyperspiralé' or not modele_word) and not COMPOSITION_TROIS_VAISSEAUX.fullmatch(v))
    if constats:
        sujet = 'Le cordon' + (', d’insertion ' + liste(insertion) + ',' if insertion else '')
        lignes.append(phrase(sujet + ' ' + (', '.join(constats) if modele_word else liste(constats))))
    elif insertion:
        lignes.append(phrase('L’insertion du cordon est ' + liste(insertion)))
    spiralisation = {'Normo': 'normalement spiralé', 'Hyper': 'hyperspiralé', 'Hypo': 'hypospiralé'}.get(
        valeurs.get('releve_cordon_spiralisation'))
    if modele_word and 'hyperspiralé' in cordon and spiralisation != 'hyperspiralé':
        lignes.append('Le cordon est hyperspiralé.')
    articles = {'Palmure amniotique': 'une palmure amniotique', 'Striction': 'une striction',
                'Nœud vrai': 'un nœud vrai', 'Circulaire': 'une circulaire',
                'Grêle': 'un aspect grêle', 'Hématome': 'un hématome'}
    particularites = liste([articles.get(v, v.lower()) for v in choix_bruts(valeurs.get('releve_cordon_particularites'))])
    sujet = 'Il' if lignes else 'Le cordon'
    if spiralisation:
        lignes.append(phrase(f'{sujet} est {spiralisation}' + (f', comportant {particularites}' if particularites else '')))
    elif particularites:
        lignes.append(phrase(f'{sujet} présente {particularites}'))
    ajouter_remarque('releve_remarques_cordon', 'Cordon')
    sections.append(('Cordon', lignes))

    lignes = []
    plaque = {'Amnios noueux': 'un amnios noueux', 'Métaplasie malpighienne': 'une métaplasie malpighienne',
              'Kystes': 'des kystes'}
    observations = choix(9)
    aspects = {'Opaque', 'Verdâtre', 'Hémorragique'}
    lesions_choriales = [v for v in observations if v not in aspects | {'Normale'}]
    if lesions_choriales:
        lignes.append(phrase('La plaque choriale présente ' + liste([
            plaque.get(v, 'des nodules' if v == 'Nodule(s)' else v) for v in lesions_choriales
        ])))
    if caracteristiques := [v.lower() for v in observations if v in aspects]:
        lignes.append(phrase('La plaque choriale est ' + liste(caracteristiques)))
    elif observations == ['Normale']:
        lignes.append('La plaque choriale est d’aspect normal.')
    ajouter_remarque('releve_remarques_choriale', 'Plaque choriale')
    sections.append(('Plaque choriale', lignes))

    lignes = []
    basale = choix_bruts(valeurs.get('releve_etat_basale'))
    if anomalies_basales := [v for v in basale if v != 'Normale']:
        lignes.append(phrase('Constatations de la plaque basale : ' + liste([v.lower() for v in anomalies_basales])))
    elif basale == ['Normale']:
        lignes.append('La plaque basale est d’aspect normal.')
    ajouter_remarque('releve_remarques_basale', 'Plaque basale')
    sections.append(('Plaque basale', lignes))

    lignes = []
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
    n, taille, epaisseur = valeur_mesuree('releve_hematome_nombre'), mesure(17), mesure(18)
    if n == '0':
        lignes.append('Il n’est pas observé d’hématome décidual basal.')
    elif n or taille or epaisseur:
        lesion = f'{n} hématomes déciduaux basaux' if n and n != '1' else 'un hématome décidual basal'
        lignes.append(phrase('On observe ' + lesion + dimensions(taille, epaisseur)))
    n, taille = mesure(19), mesure(20)
    presence = []
    if n == '0':
        lignes.append('Il n’est pas observé de kyste trophoblastique.')
    elif n or taille:
        lesion = f'{n} kystes trophoblastiques' if n and n != '1' else 'un kyste trophoblastique'
        axe = f' de {taille} cm de grand axe' if taille else ''
        if modele_word:
            presence.append(('de ' if n and n != '1' else 'd’') + lesion + axe)
        else:
            lignes.append(phrase('On observe ' + lesion + axe))
    n = valeur_mesuree('releve_thrombose_intervilleuse_nombre')
    taille = valeur_mesuree('releve_thrombose_intervilleuse_taille')
    if n == '0':
        lignes.append('Il n’est pas observé de thrombose intervilleuse.')
    elif n or taille:
        multiple = n and n != '1'
        lesion = f'de {n} thromboses intervilleuses' if multiple else 'd’une thrombose intervilleuse'
        dimension = f' de {taille} cm de grand axe' + (' maximal' if multiple else '') if taille else ''
        presence.append(lesion + dimension)
    if presence:
        lignes.append(phrase('Présence ' + liste(presence)))
    ajouter_remarque('macro_21', 'Thrombose intervilleuse')
    sections.append(('Tranches de section', lignes))

    lignes = []
    nidf = valeurs.get('releve_nidf')
    if nidf == 'Non':
        lignes.append('Absence de NIDF.')
    elif nidf == 'Oui':
        pct = nombre(valeurs.get('releve_nidf_pct'))
        proportion = f' évaluée à {format(pct, ".15g").replace(".", ",")}%' if pct is not None and 0 <= pct <= 100 else ''
        lignes.append(f'Présence de NIDF{proportion}.')
    sections.append(('NIDF', lignes))

    lignes = []
    ajouter_remarque('releve_remarques_tranches', 'Tranches de section')
    commentaire = valeurs.get('releve_commentaires_macro')
    if isinstance(commentaire, str) and commentaire.strip():
        lignes.append(phrase(f'Commentaires : {commentaire.strip()}'))
    sections.append(('Remarques', lignes))

    lignes = []
    blocs = nombre(valeurs.get('releve_inclusion_blocs'))
    if blocs is not None and blocs > 0 and blocs == int(blocs):
        lignes.append(f'Inclusion partielle en {int(blocs)} bloc{"s" if blocs > 1 else ""}.')
    sections.append(('', lignes))
    return [(titre, contenu) for titre, contenu in sections if contenu]


# Les indices correspondent aux options du relevé et à leurs valeurs persistées.
# Chaque groupe associe ses propres qualificatifs à son ou ses constats possibles.
INFLAMMATION = ((range(1, 4), range(4, 6)),)
GROUPES = {
    'micro_02': INFLAMMATION,
    'micro_03': ((range(8, 11), range(11, 13)),),
    'micro_06': ((range(3), range(3, 5)),),
    'micro_08': (
        ((1,), (30, 2, 3)), ((4,), (5, 6)), ((7,), (*range(8, 15), 31)),
        ((15,), range(16, 23)), ((23,), (24, 25)),
    ),
}


def observations(cle, valeurs, options, nombre):
    bruts = choix_bruts(valeurs.get(cle))
    coches = {i: libelle(v) for i, v in enumerate(options) if v in bruts}
    constats_normaux = []
    if cle == 'micro_08':
        normal_ancien = coches.pop(0, None)
        constats_normaux = [coches.pop(i) for i in (28, 29) if i in coches]
        if normal_ancien:
            constats_normaux = [normal_ancien]
        pct = nombre(valeurs.get('releve_villosites_avasculaires_pct'))
        if pct is not None and 0 <= pct <= 100:
            for i in (14, 31):
                if i in coches:
                    proportion = format(pct, '.15g').replace('.', ',')
                    coches[i] += f' sur environ {proportion} % du parenchyme examiné'
    notes = []
    for lesions, qualificatifs in GROUPES.get(cle, ()):
        parents = [i for i in lesions if i in coches]
        # Les villosités avasculaires restent un constat même sans diagnostic
        # de malperfusion vasculaire fœtale saisi.
        details = [coches.pop(i) for i in qualificatifs
                   if i in coches and (cle != 'micro_08' or i not in (14, 31) or parents)]
        if not details:
            continue
        if len(parents) == 1:
            i = parents[0]
            coches[i] += ' (' + liste(details) + ')'
        else:
            notes.append('précisions à rattacher à la lésion lors de la relecture : ' + liste(details))
    elements = constats_normaux + list(coches.values()) + [libelle(v) for v in bruts if v not in options]
    return elements, notes


def microscopie(valeurs, options, nombre):
    return [ligne for rubrique in microscopie_par_rubrique(valeurs, options, nombre).values()
            for ligne in rubrique]


def microscopie_paragraphes(valeurs, options, nombre):
    rubriques = microscopie_par_rubrique(valeurs, options, nombre)
    groupes = (
        ('micro_02', 'micro_01'), ('micro_03',), ('micro_05', 'micro_06', 'micro_04'),
        ('micro_07',), ('micro_08',), ('micro_09',), ('micro_10',),
    )
    return [paragraphe for groupe in groupes
            if (paragraphe := [ligne for cle in groupe for ligne in rubriques[cle]])]


def microscopie_par_rubrique(valeurs, options, nombre):
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
    commentaires = {
        'micro_08': ('releve_commentaire_villosites', 'Villosités'),
        'micro_09': ('releve_commentaire_intervilleuse', 'Chambre intervilleuse'),
        'micro_10': ('releve_commentaire_lesions', 'Lésions'),
    }
    rubriques = {}
    for cle, sujet in sujets.items():
        lignes = rubriques[cle] = []
        faits, notes = observations(cle, valeurs, options[cle], nombre)
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
        if cle in commentaires:
            champ, rubrique = commentaires[cle]
            commentaire = valeurs.get(champ)
            if isinstance(commentaire, str) and commentaire.strip():
                lignes.append(phrase(f'{rubrique} — commentaire : {commentaire.strip()}'))
    return rubriques


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
