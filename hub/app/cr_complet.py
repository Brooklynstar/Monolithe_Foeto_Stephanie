# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Présentation clinique du compte rendu complet. Les calculs restent dans leurs modules."""
import re

import percentiles
import trame_normale
import placenta_liaison
import placenta_redaction as placenta

REFERENCES = {'gc': ('*', 'Guihard-Costa'), 'ma': ('**', 'Maroun et Graem'),
              'mb': ('***', 'Müller-Brochut')}
NEGATION = re.compile(r"\b(?:pas de|absence de|sans)\s+(?:\w+\s+){0,2}polydactylie\b", re.I)
PLACENTA_COMMENTAIRE = re.compile(r"(?im)^\s*(?:placenta(?: — formulaire structuré)?|examen placentaire)\s*[:\n]")
ARTERIOGRAPHIE = re.compile(r"(?im)^\s*(?:examen artériographique|artériographie)\s*:\s*")


def texte(v):
    return v.strip() if isinstance(v, str) else ''


def phrase(v):
    v = texte(v)
    return (v[:1].upper() + v[1:] + ('' if v[-1:] in '.!?' else '.')) if v else ''


def lignes(*valeurs):
    return list(dict.fromkeys(x for v in valeurs if (x := phrase(v))))


def nombre(v):
    return str(v).replace('.', ',') if v is not None else ''


def commentaire_champ(c):
    commentaire = texte(c.get('commentaire'))
    if commentaire and commentaire != texte(c.get('note')):
        return phrase(f"{c['label']} : {commentaire}")
    return ''


def champ(c):
    return ' '.join(filter(None, (constat_champ(c), commentaire_champ(c))))


def constat_champ(c):
    valeur = c.get('valeur')
    label = re.sub(r' — précisions$', '', c.get('label') or '')
    if c.get('id') == 'congelation' and valeur == 'oui' and c.get('prelevements'):
        return phrase('Prélèvements congelés : ' + ', '.join(c['prelevements']).lower())
    if c.get('id') == 'anasarque' and valeur in ('oui', 'non'):
        return 'Présence d’un anasarque.' if valeur == 'oui' else 'Absence d’anasarque.'
    if c.get('type') == 'chips':
        valeurs = c.get('valeurs') or []
        normaux = set(c.get('normaux') or [])
        if c.get('id') == 'diaphragme':
            normaux.add('Normal')
        if normaux and any(v not in normaux for v in valeurs):
            globaux = {'normal', 'normale', 'solitus', 'perméable', 'perméables', 'concordants'}
            valeurs = [v for v in valeurs if v not in normaux or v.casefold() not in globaux]
        valeur = ', '.join(valeurs)
    elif c.get('type') == 'axe':
        details = ', '.join([*(c.get('termes') or []), *filter(None, [c.get('autre')])])
        note = texte(c.get('note'))
        if details or note:
            return phrase(' '.join(filter(None, [f'{label} : {details}' if details else '', note])))
        if c.get('etat') == 'normal':
            return phrase(f'{label} : aspect habituel')
        if c.get('etat') == 'anormal':
            return phrase(f'{label} : anomalie signalée')
    if valeur is None or valeur == '':
        return ''
    if c.get('id', '').endswith(('_detail', '_commentaire')) or c.get('id') == 'commentaire':
        return phrase(valeur)
    return phrase(f"{label} : {nombre(valeur) if isinstance(valeur, (int, float)) else valeur}"
                  + (f" {c['unite']}" if c.get('unite') else ''))


def bloc(titre, lignes_=(), sous=(), mesures=()):
    constats, sous_blocs, mesures = list(filter(None, lignes_)), list(filter(None, sous)), list(mesures)
    if constats or sous_blocs or mesures:
        lignes_mesures, renvois = tableau_mesures(mesures)
        return {'titre': titre, 'lignes': constats, 'sous': sous_blocs,
                'mesures': lignes_mesures, 'references_mesures': renvois}
    return None


def texte_clinique(ctx):
    issue, atcd, obs, grossesse = ((ctx['admin'].get(k) or {}) for k in ('issue', 'atcd_mat', 'atcd_obs', 'grossesse'))
    type_issue = {'IMG': 'Interruption médicale de grossesse', 'MFIU': 'Mort fœtale', 'MF': 'Mort fœtale',
                  'FCS': 'Avortement spontané', 'FCT': 'Fausse couche tardive'}.get(
                      issue.get('type_issue'), issue.get('type_issue'))
    sa, jours = ctx['terme']['sa'], ctx['terme'].get('j')
    terme = f'{sa} SA' if sa is not None else ''
    if terme and jours:
        terme += f' + {jours} ' + ('jour' if jours in (1, '1') else 'jours')
    groupe = ' '.join(filter(None, [atcd.get('groupe_sanguin'), atcd.get('rhesus')]))
    groupe = ' — '.join(filter(None, (groupe, texte(atcd.get('groupe_sanguin_detail')))))
    saisie_consanguinite = atcd.get('consanguinite')
    libelle_consanguinite = {'true': 'Oui', 'false': 'Non', 'UNK': 'Inconnue'}.get(
        str(saisie_consanguinite).lower() if isinstance(saisie_consanguinite, bool) else texte(saisie_consanguinite),
        texte(saisie_consanguinite))
    consanguinite = ' — '.join(filter(None, (libelle_consanguinite,
                                          texte(atcd.get('consanguinite_detail')))))
    fcs = obs.get('fcs')
    fcs = ' — '.join(filter(None, (str(fcs) if fcs in ('1', '2', 1, 2) else '',
                                 texte(obs.get('fcs_detail')))))
    ddg = grossesse.get('ddg') or {}
    gestite = ' '.join(f'{initiale}{obs[cle]}' for initiale, cle in [('G', 'gestite'), ('P', 'parite')]
                      if obs.get(cle) is not None)
    date = '/'.join(map(str, [ddg[k] for k in ('jour', 'mois', 'annee') if ddg.get(k)]))
    return lignes(
        (type_issue + (f' à {terme}' if terme else '')) if type_issue else '',
        f'Date de début de grossesse : {date}' if date else '',
        gestite, f'Groupe sanguin : {groupe}' if groupe else '',
        f"Consanguinité : {consanguinite}" if consanguinite else '',
        f"Antécédents FCS : {fcs}" if fcs else '',
        f"Traitement : {atcd['traitements']}" if atcd.get('traitements') else '',
        atcd.get('atcd_medicaux'), issue.get('indication'), grossesse.get('histoire_clinique'),
        grossesse.get('contexte_clinique'),
        *(item.get('texte') for item in grossesse.get('chronologie') or []),
    )


def prenatal(ctx):
    donnees, grossesse = ctx['prenatal'], ctx['grossesse']
    resultats = []

    def date_echo(date):
        if isinstance(date, dict):
            return '/'.join(str(date[k]).zfill(4 if k == 'annee' else 2)
                            for k in ('jour', 'mois', 'annee') if date.get(k) is not None)
        return '' if date == 'err' else texte(date)

    for n, libelle in (('t1', 'T1'), ('t2', 'T2'), ('t3', 'T3'), ('sup1', 'complémentaire')):
        prefixe = f'echo_{n}'
        sa, jours = (donnees.get(f'{prefixe}_{k}') for k in ('sa', 'jours'))
        terme = f'{sa} SA' if sa not in (None, '') else ''
        if jours not in (None, ''):
            terme += f' + {jours} j' if terme else f'{jours} j'
        contexte = ', '.join(filter(None, (' · '.join(filter(None, (
            date_echo(donnees.get(f'{prefixe}_date')), terme,
        ))), texte(donnees.get(f'{prefixe}_medecin')))))

        mesures = []
        for label in ('LCC', 'BIP', 'LF', 'DAT', 'CN'):
            cle = label.lower()
            valeur = donnees.get(f'{prefixe}_{cle}')
            if n == 't1' and cle in ('lcc', 'cn') and valeur in (None, ''):
                valeur = grossesse.get(cle)
            if valeur not in (None, ''):
                mesures.append(f'{label} {nombre(valeur)} mm')
        ddg = date_echo(donnees.get(f'{prefixe}_ddg'))
        liquide = {'NORMAL': 'Quantité de liquide amniotique normale',
                   'HYDRAMNIOS': 'Hydramnios', 'OLIGOAMNIOS': 'Oligoamnios'}.get(donnees.get(f'{prefixe}_liquide'))
        statut = texte(donnees.get(prefixe))
        conclusion = {'NORMALE': 'Échographie normale', 'ANOMALIE': 'Présence d’anomalie(s)',
                      'ANORMALE': 'Présence d’anomalie(s)', 'NON_FAITE': 'Échographie non réalisée',
                      'GROSSESSE_MONO_EVOLUTIVE': 'Grossesse intra-utérine monofœtale normalement évolutive'}.get(statut, statut)
        details = lignes(f'DDG estimée au {ddg}' if ddg else '', ', '.join(mesures),
                         liquide or "", donnees.get(f'{prefixe}_liquide_commentaire'), conclusion,
                         donnees.get(f'{prefixe}_commentaire'), donnees.get(f'{prefixe}_details'))
        if contexte or details:
            titre = f'Écho {libelle} ({contexte})' if contexte else f'Échographie {libelle}'
            resultats.append(phrase(f"{titre} : {' '.join(details)}" if details else titre))

    if risque := grossesse.get('risque_t21'):
        resultats.append(phrase(f'Risque combiné T21 : {risque}'))
    marqueurs = [f'{label} {nombre(grossesse[cle])} MoM'
                 for cle, label in [('pappa', 'PAPP-A'), ('bhcg', 'β-hCG')]
                 if grossesse.get(cle) not in (None, '')]
    if marqueurs:
        resultats.append(phrase('Marqueurs sériques : ' + ', '.join(marqueurs)))
    return resultats + lignes(donnees.get('autres_examens'))


def mesure(parametre, v, unite='', refs=(), attendu=None):
    if v is None or v == '':
        return None
    valeur = ' '.join(filter(None, (nombre(v) if isinstance(v, (int, float)) else v, unite)))
    return parametre, valeur, refs, nombre(attendu) if attendu is not None else ''


def tableau_mesures(mesures):
    refs_presentes = dict.fromkeys(ref for _, _, refs, _ in mesures
                                  for ref, pct, z in refs if pct is not None or z is not None)
    renvois = {ref: REFERENCES[ref] for ref in REFERENCES if ref in refs_presentes}
    autres = [ref for ref in refs_presentes if ref not in REFERENCES]
    renvois.update({ref: ('†' * index, ref) for index, ref in enumerate(autres, 1)})
    resultats = []
    for label, valeur, refs, attendu in mesures:
        p, ds = [], []
        for ref, pct, z in refs:
            if pct is not None:
                p.append((percentiles.pt(pct), renvois[ref][0]))
            if z is not None:
                ds.append((percentiles.zt(z).removesuffix(' DS'), renvois[ref][0]))
        resultats.append((label, valeur, p, ds, attendu))
    return resultats, list(renvois.values())


def z_mesures(lignes_):
    rows = []
    for l in lignes_:
        refs = [(src, l.get('percentile_' + src), l.get('z_brut_' + src)
                 if l.get('z_brut_' + src) is not None else l.get('z_' + src))
                for src in REFERENCES]
        row = mesure(l.get('label') or l.get('id'), l.get('detail') or l.get('valeur'),
                     l.get('unite') or '', refs, l.get('terme_attendu'))
        if row:
            rows.append(row)
    return rows


def radio(ctx, remarques):
    rad = ctx['radio']
    sq, bm = rad.get('squelette') or {}, rad.get('biometries') or {}
    mat = rad.get('maturation_osseuse') or {}
    rows = [mesure('BIP osseux', bm.get('bip_osseux_mm'), 'mm'),
            mesure('Périmètre crânien radiographique', bm.get('pc_radio_mm'), 'mm')]
    for nom, o in (bm.get('os_longs') or {}).items():
        if o.get('moyenne') is not None:
            v = f"{nombre(o['moyenne'])} mm"
            if o.get('droite') is not None and o.get('gauche') is not None:
                v += f" (D {nombre(o['droite'])} / G {nombre(o['gauche'])} mm)"
            rows.append(mesure({'Femur': 'Fémur', 'Humerus': 'Humérus'}.get(nom, nom), v,
                               refs=[('Chitty', o.get('percentile_chitty'), o.get('zscore_chitty'))],
                               attendu=o.get('terme_attendu')))
        else:
            for cle, cote in [('droite', 'D'), ('gauche', 'G')]:
                rows.append(mesure(f'{nom} ({cote})', o.get(cle), 'mm'))
    cotes = sq.get('cotes') or {}
    constats = lignes(sq.get('aspect_general'), sq.get('thorax_forme'), remarques,
                      *(f'Côtes : {cotes[cle]} à {cle}' for cle in ('droite', 'gauche') if cotes.get(cle) is not None))
    for cle in ('vertebres', 'aspect_os'):
        doc = sq.get(cle) or {}
        constats.extend(lignes(*(doc.get('aspects') or []), doc.get('remarques')))
    if isinstance(mat, list):
        visibles = [p['label'] for p in mat if p.get('status') == 'present' and p.get('label')]
        absents = [p['label'] for p in mat if p.get('status') == 'absent' and p.get('label')]
    else:
        visibles, absents = mat.get('points_visibles') or [], []
    rows.insert(0, mesure('Points d’ossification visibles', ', '.join(visibles)))
    if absents:
        constats.append(phrase('Points d’ossification notés absents : ' + ', '.join(absents)))
    sc = rad.get('scores_staturaux') or {}
    for nom in ('hadlock', 'adalian'):
        if sc.get(nom + '_sa') is not None:
            constats.append(phrase(f'Âge statural selon {nom.capitalize()} : {nombre(sc[nom + "_sa"])} SA'))
    return bloc('Examen radiographique', constats, mesures=list(filter(None, rows)))


def externe(ctx):
    groupes = []
    for e in ctx['clinique']['etages']:
        constats = []
        for i in e.get('items') or []:
            etat, label, prec = i.get('etat'), i.get('label'), texte(i.get('precisions'))
            anomalies = [a.get('label') if isinstance(a, dict) else a for a in i.get('anomalies') or []]
            anomalies = list(filter(None, anomalies))
            atteste = etat == 'anormal' or bool(anomalies)
            trame = ctx['items_normaux']
            selection = i.get('normal_items') or []
            if isinstance(selection, list):
                constats.extend(lignes(*(o['phrase'] for k, o in trame.items()
                                         if k in selection and o['cible'] == i.get('id') and
                                         not trame_normale.incompatible(o, anomalies, prec, atteste))))
            if atteste:
                detail = ', '.join(anomalies)
                constats.extend(lignes(f'{label} : {detail}' if detail else
                                       ('' if prec else f'{label} : anomalie signalée'), prec))
            elif etat == 'normal' and 'normal_items' not in i:
                constats.extend(lignes(f'{label} : sans anomalie décrite', prec))
            else:
                constats.extend(lignes(prec))
            commentaire = texte(i.get('commentaire'))
            if commentaire and commentaire != prec:
                constats.extend(lignes(f'{label} : {commentaire}'))
        groupes.append(bloc((e.get('titre') or '').replace(' & ', ' et '), constats))
    section = bloc('Examen externe', sous=groupes, mesures=z_mesures(ctx['biometrie']['lignes']))
    if section:
        section['biometrie'] = True
    return section


def trame(etapes, normaux=()):
    champs_par_id = {c['id']: c for e in etapes for c in e['champs']}

    def compatible(option):
        for cible in option['cibles']:
            c = champs_par_id.get(cible, {})
            if c.get('type') == 'bool' and c.get('valeur') == 'non':
                return False
            anomalies = set(c.get('valeurs') or ()) - set(c.get('normaux') or ())
            mots = option['mots']
            if any(not mots or any(m in v.casefold() for m in mots) for v in anomalies):
                return False
        return True

    selections = [o for o in normaux if compatible(o)]
    resultats = []
    for e in etapes:
        options = [o for o in selections if o['etape'] == e['id']]
        couvertes = {cible for o in options for cible in o['cibles']}
        constats, mesures = [o['phrase'] for o in options], []
        for c in e['champs']:
            if c.get('id') in couvertes and c.get('normaux'):
                c = dict(c, valeurs=[v for v in c['valeurs'] if v not in c['normaux']], normaux=[])
            if c.get('id') in couvertes and c.get('type') == 'bool' and c.get('valeur') == 'oui':
                c = dict(c, valeur=None)
            if c.get('type') in ('masse', 'masse2'):
                constats.append(commentaire_champ(c))
                continue
            if c.get('type') in ('number', 'num') or c.get('unite'):
                ligne = mesure(c.get('label'), c.get('valeur'), c.get('unite') or '',
                               attendu=c.get('terme_attendu'))
                if ligne:
                    mesures.append(ligne)
                if c.get('presence') == 'non':
                    constats.append(phrase(f"Absence d’{c['label'].lower()}"))
                elif c.get('presence') == 'oui' and not ligne:
                    constats.append(phrase(f"Présence d’un {c['label'].lower()}"))
                constats.append(commentaire_champ(c))
            else:
                constats.append(champ(c))
        resultats.append(bloc(e.get('titre'), lignes(*constats), mesures=mesures))
    return resultats


def grille(g):
    # Seuls les constats de signes sont repris. Les moteurs et codes restent dans la relecture.
    texte_cr = g.get('compte_rendu') or ''
    signes = re.search(r'(?m)^SIGNES\s*\n((?:  .+\n?)+)', texte_cr)
    resultats = []
    if signes:
        for l in signes[1].splitlines():
            if ' — ' in l:
                label, etat = l.strip().rsplit(' — ', 1)
                rendu = {'NORMAL': 'aspect habituel', 'ABSENT': 'absent'}.get(etat)
                resultats.append(phrase(f'{label} : {rendu}' if rendu else label))
    return bloc(g['organe'].capitalize(), lignes(*resultats, g.get('libre')))


def alertes(ctx, donnees_placenta):
    avis = [str(v) for v in ctx['coherence']]
    if ctx['terme']['discordant']:
        valeur = [f'{m} : {v} SA' for m, v in ctx['terme']['vu_par'].items()]
        avis.append(f"Termes discordants à relire (administratif : {ctx['terme']['texte']}) : " + ', '.join(valeur))
    for z in ctx['z_divergences']:
        avis.append(f"{z['champ']} ({z['reference']}) : {z['serveur']} DS dans le Hub, {z['module']} DS à la saisie.")
    rad = ctx['radio']
    negation = any(NEGATION.search(texte(v)) for v in ((rad.get('squelette') or {}).get('aspect_general'), rad.get('remarques')))
    polydactylie = negation and any(h.get('code') == 'HP:0001161' for h in rad.get('hpo') or [])
    if polydactylie:
        avis.append('Radiographie : le texte exclut la polydactylie, malgré le code HPO HP:0001161 associé à la saisie.')
    p = placenta_liaison.champs(donnees_placenta) if not ctx.get('placenta_gemellaire') else {}
    if (ep := placenta_liaison.nombre(p.get('macro_16'))) is not None and ep < 0:
        avis.append(f"Placenta — Thrombose sous-choriale : épaisseur négative ({nombre(ep)} cm), écartée du compte rendu.")
    for ligne in placenta.conclusion(p):
        if ligne.startswith('À relire :'):
            avis.append(ligne.removeprefix('À relire : '))
    for e in ctx['neuropath']['etapes']:
        for c in e['champs']:
            v = texte(c.get('valeur'))
            if c.get('id') == 'commentaire' and PLACENTA_COMMENTAIRE.search(v):
                avis.append(f"Bloc placentaire à déplacer depuis Neuropathologie → {e['titre']} → {c['label']}.")
            if c.get('id') == 'prelev_detail' and 'placenta' in v.lower() and re.search(r'\b(cœur|poumons|foie|reins|gonades)\b', v, re.I):
                avis.append(f"Liste multi-organes recopiée dans Neuropathologie → {e['titre']} → {c['label']}. Vérifier le champ.")
    return avis, polydactylie


def placenta_bloc(ctx):
    gemellaire = ctx.get('placenta_gemellaire')
    if gemellaire:
        placentas = [
            bloc(f'Placenta {i}', sous=[
                bloc('Macroscopie', plac['macroscopie']),
                bloc('Microscopie', plac['microscopie']),
            ])
            for i, plac in enumerate(gemellaire['placentas'], 1)
        ]
        return bloc('Placenta', sous=[
            bloc('Ensemble placentaire', [*gemellaire['ensemble'], gemellaire.get('distance')]),
            *placentas, bloc('Conclusion placentaire', gemellaire['conclusion']),
        ])
    sections = {s['titre']: s['lignes'] for s in (ctx['placenta_formulaire'] or {}).get('sections', [])}
    return bloc('Placenta', sous=[
        bloc('Macroscopie', sections.get('Macroscopie', [])),
        bloc('Microscopie', sections.get('Microscopie', [])),
        bloc('Conclusion placentaire', [
            l for l in sections.get('Conclusion', []) if not l.startswith('À relire :')
        ]),
    ])


def composition(ctx):
    micro = [s for s in ctx['micro']['sections'] if s['champs']]
    neuro_micro = [bloc(s['titre'], lignes(*(champ(c) for c in s['champs']))) for s in micro
                   if s['organe'] in ('cerveau', 'snc') or s['titre'] == 'Système nerveux central']
    vis_micro = [bloc(s['titre'], lignes(*(champ(c) for c in s['champs']))) for s in micro
                 if not (s['organe'] in ('cerveau', 'snc') or s['titre'] == 'Système nerveux central')]
    for g in ctx['grilles_foetales']:
        vis_micro.append(grille(g))
    ne = ctx['neuropath']['etapes']
    zn = []
    for e in ne:
        for c in e['champs']:
            if c.get('type') not in ('number', 'num') and not c.get('unite') and not c.get('zscore'):
                continue
            z = c.get('zscore') or {}
            ref = z.get('source') or z.get('reference')
            row = mesure(c.get('label'), c.get('valeur'), c.get('unite') or '',
                         [(ref, z.get('percentile'), z.get('z_brut') if z.get('z_brut') is not None else z.get('z'))] if ref else [],
                         z.get('terme_attendu'))
            if row:
                zn.append(row)
    blocs_neuro = []
    for e in ne:
        cs = [c for c in e['champs'] if not (c.get('type') in ('number', 'num') or c.get('unite') or c.get('zscore')) and
              not (c.get('id') == 'commentaire' and PLACENTA_COMMENTAIRE.search(texte(c.get('valeur')))) and
              not (c.get('id') == 'prelev_detail' and 'placenta' in texte(c.get('valeur')).lower() and
                   re.search(r'\b(cœur|poumons|foie|reins|gonades)\b', texte(c.get('valeur')), re.I))]
        blocs_neuro.append(bloc(e['titre'], lignes(*(champ(c) for c in cs))))
    vis_macro = [e for e in ctx['autopsie']['etapes'] if e.get('id') != 'neuro']
    neuro_autopsie = [e for e in ctx['autopsie']['etapes'] if e.get('id') == 'neuro']
    rad = ctx['radio']
    arterio = rad.get('arteriographie') or rad.get('arteriographique')
    if isinstance(arterio, dict):
        arterio = arterio.get('compte_rendu') or arterio.get('description') or arterio.get('remarques')
    remarques_radio = texte(rad.get('remarques'))
    if not arterio and (titre := ARTERIOGRAPHIE.search(remarques_radio)):
        remarques_radio, arterio = remarques_radio[:titre.start()], remarques_radio[titre.end():]
    conclusion = ctx['conclusion_clinique']
    return [b for b in (
        bloc('Renseignements cliniques', texte_clinique(ctx)),
        bloc('Examens prénataux', prenatal(ctx)),
        radio(ctx, remarques_radio), bloc('Examen artériographique', lignes(arterio)), externe(ctx),
        bloc('Examen viscéral', sous=[
            bloc('Macroscopie', sous=[
                bloc('Poids des organes', mesures=z_mesures(ctx['autopsie']['masses'])),
                *trame(vis_macro, ctx.get('normaux_autopsie', ())),
            ]),
            bloc('Microscopie', sous=vis_micro),
        ]),
        bloc('Examen de l’encéphale', sous=[bloc('Macroscopie', sous=[*trame(neuro_autopsie), *blocs_neuro], mesures=zn),
                                           bloc('Microscopie', sous=neuro_micro)]),
        placenta_bloc(ctx), bloc('Conclusion', [conclusion]) if conclusion else
        {'titre': 'Conclusion', 'lignes': [], 'sous': [], 'mesures': []},
    ) if b]
