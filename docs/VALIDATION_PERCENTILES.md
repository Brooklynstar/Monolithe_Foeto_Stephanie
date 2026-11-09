# Percentiles des biométries externes — Issue n°1

Implémentation issue de `port_5006` (`00b51a4`), sur
`percentiles_biometries`, sans reprise de la branche `stephanie`.

## Parcours couvert

La saisie biométrique v1.4.0 affiche les Z-scores et percentiles par référence.
Elle conserve le schéma JSON `0.1.0`, les mesures, les unités, les libellés et
les anciens `ecarts` arrondis. Deux champs s'ajoutent :

```json
{
  "ecarts_non_arrondis": {"bip": {"MB": 0.1249}},
  "percentiles": {"bip": {"MB": 54.9698640814085}}
}
```

Les nombres ci-dessus illustrent le cas test BIP à 16 SA. Les dernières
décimales peuvent varier à la précision machine. Le percentile est calculé
sur le Z **non arrondi**, selon `100 × Φ(Z)`. Seul l'affichage est arrondi à
deux décimales, avec `P < 0,01` et `P > 99,99` aux extrêmes.

La même fonction JavaScript alimente le formulaire et le calculateur unifié.
Sa source est `hub/app/web/percentiles.js`. Elle est intégrée dans les HTML
pour conserver leur autonomie. Après modification de cette source :

```sh
python3 hub/outils/integrer_percentiles.py
python3 pack_telephone.py
```

Le hub recalcule les percentiles à partir des mesures et des références
existantes. Les résultats alimentent le compte rendu complet, la synthèse,
les propositions biométriques et les aides de gabarit `table_biometries_externes()`
et `_ds()`. Le complet et les aides de compatibilité utilisent le même tableau.
Les nouveaux JSON relus ou archivés conservent leurs percentiles ; les
archives historiques restent intactes. Relire puis réexporter un ancien JSON
depuis le formulaire ajoute les résultats actualisés.

Le terme administratif reste prioritaire. En son absence, les biométries
externes utilisent le terme de leur saisie, identifié dans le compte rendu.
Ce repli ne change pas le calcul des masses d'organes.

## Mesures et validité

Toutes les mesures référencées de la trame sont couvertes : masse fœtale,
pied, BIP, diamètre FO, main, VT, VC, PC/POF, PT et PA. Les autres champs sont
conservés sans résultat inventé. `PC` reste la clé du périmètre crânien,
également désigné POF ; `FO`/`FOD` est un **diamètre**, distinct du POF.

- Guihard-Costa : classes de 13 à 42 SA.
- Maroun et Graem : lignes de 12 à 43 SA.
- Müller-Brochut : lignes de 12 à 20 SA.
- Une référence absente, un écart-type nul/invalide ou un terme non entier ne
  produit pas de percentile ; pas d'extrapolation ni d'interpolation nouvelle.
- Les jours de terme restent enregistrés, sans modifier la règle existante
  de consultation des tables par semaine entière.

Les valeurs des tables restent identiques à `port_5006`. Le calculateur
unifié réutilise aussi sa référence CFL existante pour la mesure VT, avec
conversion cm/mm. Les masses d'organes, la radiologie et les autres modules
ne reçoivent pas de calcul de percentile supplémentaire.

## Tests automatisés

Avec les dépendances Python du hub installées, Node.js, Playwright et Chromium :

```sh
hub/app/.venv/bin/python -m unittest discover -s tests -v
hub/app/.venv/bin/python hub/outils/verifier_cr.py
python3 hub/outils/integrer_percentiles.py --verifier
```

`MONOLITHE_CHROMIUM` permet d'indiquer l'exécutable Chromium à Playwright.
`MONOLITHE_TEST_OUTPUT` permet de conserver les JSON téléchargés, les comptes
rendus réellement produits, les captures et `resultats.json` dans un dossier
de travail. Les bases SQLite des tests sont toujours temporaires.
Une dépendance de test absente fait échouer le test concerné ; le parcours
navigateur n'est pas ignoré silencieusement.

Résultats obtenus le 9 novembre 2026 sous Linux, Python 3.12 et Chromium :

| Vérification | Résultat |
|---|---:|
| Suite `unittest` (dont lancement sur 5006) | 16 tests réussis, aucun ignoré |
| Comparaison numérique Python/JavaScript | 2 001 Z entre −10 et +10, écart absolu ≤ 2 × 10⁻¹² point de percentile |
| Domaines, unités, références | 11 à 44 SA, sans terme, terme fractionnaire, référence absente, SD invalide |
| Dossiers saisis/exportés/importés dans le hub | 8, avec plusieurs biométries chacun, dont un sans administratif |
| Percentiles contrôlés dans les tableaux de saisie | 70 |
| Percentiles contrôlés dans les JSON téléchargés | 80, y compris une réexportation historique |
| Percentiles contrôlés dans les CR complets et synthèses | 140, avec relecture des CR enregistrés |
| Percentiles contrôlés dans le calculateur unifié | 70, valeurs numériques et texte préparé pour copie |
| Calculs des masses d'organes comparés à `port_5006` | 128 cas identiques, 32 termes × 4 grades |
| Vérificateur existant des comptes rendus | 76 vérifications réussies |

Exemples effectivement retrouvés dans les fichiers et rendus des tests :

| Mesure à 16 SA | GC | MA | MB |
|---|---:|---:|---:|
| BIP 34,4498 mm | — | — | P54,97 |
| PC/POF 121,763 mm | P66,09 | P43,17 | P59,13 |

Les anciens dossiers sont testés sans `percentiles`, sans `ecarts_non_arrondis`,
sans libellés ni unités ajoutées récemment. Leurs mesures sont conservées,
leurs références disponibles sont recalculées, leurs archives restent
inchangées. Les valeurs préenregistrées périmées ne remplacent pas le calcul
serveur. Sans tables ni Z exact, un ancien Z arrondi reste affichable mais
ne sert pas à inventer un percentile.

Bancs d'essai des formulaires : biométrie 61/61, copie téléphone 61/61,
examen clinique 96/96, autopsie 131/131, neuropathologie 119/119,
macro placenta 95/95 et radiologie 47/47. Les tables et le paquet téléphone
sont aussi contrôlés par empreintes et comparaison de contenu.

## Limites et constats antérieurs

Le Chromium géré bloque les URL `file://` (`ERR_BLOCKED_BY_ADMINISTRATOR`).
Les HTML autonomes ont été servis **sans modification**, ni injection du hub,
sur une boucle locale ; le test vérifie l'absence de requête extérieure.
Le mode servi par le hub est également testé avec relecture effective du dossier.
L'ouverture directe par double-clic sur les appareils utilisateurs reste à
vérifier, ainsi que Safari et Firefox. Les gabarits personnalisés externes
non présents dans ce dépôt ne peuvent pas être testés ; les aides de
compatibilité disponibles dans le dépôt sont couvertes.

L'audit existant `hub/outils/verifier_tables.py` signale **105 divergences**
avant **et** après cette modification : 47 sur les masses d'organes
Müller-Brochut, répétées dans la copie téléphone, et 11 dans l'ancien fichier
`archives/biometries.html`. Les tables du formulaire biométrique courant
concordent avec celles du calculateur unifié. Ces divergences préexistantes
hors périmètre n'ont pas été corrigées et ne constituent pas une nouvelle
validation scientifique des références.

<!-- SPDX-License-Identifier: CC-BY-NC-SA-4.0 -->
