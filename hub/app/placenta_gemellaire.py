# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Compte rendu du module gémellaire, à partir de la configuration active."""
import placenta_liaison
import placenta_redaction as redaction

CONFIGURATIONS = {
    'bcba_separes': 'Placenta gémellaire bichorial biamniotique à placentas séparés.',
    'bcba_fusionnes': 'Placenta gémellaire bichorial biamniotique à placentas fusionnés.',
    'mcba': None,
    'mcma': None,
}


def bloc(doc, cle):
    valeur = doc.get(cle)
    return valeur if isinstance(valeur, dict) else {}


def mesurer(doc, cle, maximum=None):
    valeur = placenta_liaison.nombre(doc.get(cle))
    if valeur is None or valeur < 0 or (maximum is not None and valeur > maximum):
        return ''
    return format(valeur, '.15g').replace('.', ',')


def mesures_ensemble(ensemble):
    poids, longueur, largeur, epaisseur = (
        mesurer(ensemble, cle) for cle in ('poids', 'longueur', 'largeur', 'epaisseur')
    )
    elements = []
    if poids:
        elements.append(f'pèse {poids} g')
    dimensions = [f'{v} cm {suffixe}' for v, suffixe in
                  ((longueur, 'de longueur'), (largeur, 'de largeur'), (epaisseur, 'd’épaisseur')) if v]
    if dimensions:
        elements.append('mesure ' + redaction.liste(dimensions))
    return [redaction.phrase('L’ensemble placentaire ' + redaction.liste(elements))] if elements else []


def phrases_conclusion(valeurs):
    choix = redaction.choix_bruts(valeurs.get('conclusion_01'))
    options = placenta_liaison.OPTIONS['conclusion_01']
    # Rattacher les précisions au diagnostic correspondant s’il a été coché.
    groupes = {
        4: (5, 6, 7),
        8: (9, 10),
        12: (13, 14),
        20: (21, 22, 23, 24),
    }
    resultats = {}
    for parent, indices in groupes.items():
        details = [options[i] for i in indices if options[i] in choix]
        libelle = options[parent]
        if libelle in choix and details:
            phrase = redaction.conclusion({'conclusion_01': libelle})[0].rstrip('.')
            resultats[libelle] = redaction.phrase(phrase + ' (' + redaction.liste(details) + ')')
            choix = [v for v in choix if v not in details]
    lignes = []
    for v in choix:
        if v in resultats:
            lignes.append(resultats[v])
        elif v == options[16]:
            lignes.append('Il n’est pas observé de réponse inflammatoire fœtale.')
        elif v in options[17:20]:
            observation = redaction.libelle(v).removeprefix('avec ')
            lignes.append(redaction.phrase('On observe une ' + observation))
        elif any(v == options[i] for indices in groupes.values() for i in indices):
            lignes.append(redaction.phrase('La qualification retenue est « ' + redaction.libelle(v) + ' »'))
        else:
            lignes.extend(redaction.conclusion({'conclusion_01': v}))
    return lignes


def compte_rendu(doc):
    configuration = doc.get('configuration')
    if not isinstance(configuration, str) or configuration not in CONFIGURATIONS:
        return None
    resultat = {'configuration': configuration, 'ensemble': [], 'placentas': [], 'conclusion': []}
    if CONFIGURATIONS[configuration] is None:
        return resultat

    saisie = bloc(bloc(doc, 'configurations'), configuration)
    fusionnes = configuration == 'bcba_fusionnes'
    if fusionnes:
        ensemble = bloc(saisie, 'ensemble')
        resultat['ensemble'] = mesures_ensemble(ensemble)
        distance = mesurer(ensemble, 'distance')
        if distance:
            resultat['distance'] = f'Les deux insertions des cordons sont distantes de {distance} cm.'
    for cle in ('placenta_1', 'placenta_2'):
        placenta = bloc(saisie, cle)
        valeurs_macro = bloc(placenta, 'macroscopie')
        valeurs_micro = bloc(placenta, 'microscopie')
        macro = redaction.macroscopie(valeurs_macro, '', placenta_liaison.nombre)
        if fusionnes and (pourcentage := mesurer(valeurs_macro, 'pourcentage', maximum=100)):
            macro.append(f'Ce placenta représente {pourcentage} % de la galette placentaire.')
        micro = redaction.microscopie(valeurs_micro, placenta_liaison.OPTIONS)
        if fusionnes and valeurs_micro.get('membrane_bichoriale', True) is True:
            micro.insert(0, 'La membrane est de type bichorial.')
        resultat['placentas'].append({'macroscopie': macro, 'microscopie': micro})
    resultat['conclusion'] = [CONFIGURATIONS[configuration], *phrases_conclusion(bloc(saisie, 'conclusion'))]
    return resultat
