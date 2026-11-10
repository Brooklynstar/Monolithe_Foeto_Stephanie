# Percentiles des masses d'organes — bilan du 10 novembre 2026

Branche indépendante `percentiles_masses_organes`, créée directement depuis
`main` a3cc4b914e6b95549ef5939d0fe8b4645dae357e.
Aucune fusion dans main, une branche stable ou test-integration.

## État de validation : réserve sur les transcriptions MB

Le calcul des nouveaux percentiles et la transmission des résultats sont testés.
**La concordance intégrale avec le calculateur unifié ne peut pas être validée :
27 entrées Müller-Brochut étaient déjà différentes dans main.** Aucune valeur
n'a été corrigée, conformément à la demande. Elles concernent :

| Organe | SA concernées |
| --- | --- |
| Thymus | 12, 13, 14, 15, 16, 19, 20 |
| Reins, total | 12 à 19 |
| Rate | 13 à 20 |
| Surrénales | 13, 15, 16, 17 |

Les valeurs de chaque transcription sont consignées dans
[ecarts_transcriptions_masses.json](../hub/references/ecarts_transcriptions_masses.json).
Exemple à 12 SA : thymus, autopsie moyenne 0,07 g / ET 0,05 g ; calculateur
moyenne 0,10 g / ET 0,06 g. Les 136 cas de comparaison donnent 108 écarts de Z,
soit 27 entrées répétées sur quatre grades ; il ne s'agit pas de 108 nouvelles
anomalies. Le calculateur affiche une note lorsque la saisie est concernée.
Les P restent calculés depuis le Z de chaque transcription : **ils peuvent donc
également différer dans ces cas**. L'arbitrage des transcriptions contre la
publication originale reste nécessaire avant validation et intégration.

## Inventaire des mesures dans main

Les masses se trouvent dans **Macro/autopsie.html**, et non dans les constatations
qualitatives d'examen clinique. Les références du Hub sont dans
`hub/references/autopsie.json` ; le calculateur possède ses propres transcriptions.

| Mesure | Guihard-Costa | Maroun/Graem | Müller-Brochut |
| --- | --- | --- | --- |
| Thymus | Oui | Grade 0–1, 2, 3 | Oui |
| Cœur | Oui | Sans stratification de macération | Oui |
| Poumons, total D + G | Oui | Grade 0–1 ou 2–3 | Oui |
| Foie | Oui | Grade 0–1, 2, 3 | Oui |
| Pancréas | Oui | Absent | Absent |
| Rate | Oui | Grade 0–1 ou 2–3 | Oui |
| Surrénales, total D + G | Oui | Grade 0–1 ou 2–3 | Oui |
| Reins, total D + G | Oui | Grade 0–1 ou 2–3 | Oui |
| Cerveau | Absent | Sans stratification de macération | Oui |

Les tables Guihard-Costa couvrent 13–42 SA, Maroun 12–43 SA, Müller-Brochut
12–20 SA, avec les cellules réellement présentes dans chaque table. Toutes ces
masses sont en grammes. Une masse totale n'est pas divisée arbitrairement pour
créer un percentile individuel.

Le calculateur propose en plus les poumons droit/gauche et reins droit/gauche,
avec certaines références MB individuelles déjà présentes dans main. Le P y
utilise le Z individuel existant, uniquement lorsqu'il est calculable.
Les cellules sans moyenne ou sans ET restent sans résultat.

La **neuropathologie** dispose de deux masses distinctes :

- `masse_enc` : **masse de l'encéphale fixé**, référence ME ;
- `masse_cerv` : **masse de l'étage infratentoriel**, référence MI.

Le second champ ne désigne pas automatiquement le cervelet isolé. Les tables
ME/MI couvrent 8–41 SA par bandes ; leurs noms de source sont ceux de main.
Leur copie extraite, sans changement numérique, est dans `neuropath_masses.json`.
Les dimensions cérébrales BC, leurs régressions et le rapport RI sont inchangés :
aucun nouveau percentile n'est ajouté à ces mesures non massiques.
La masse de cerveau de l'autopsie n'est pas substituée à celle de l'encéphale fixé.

La bibliographie de main présente aussi une discordance d'année pour Maroun :
2005 dans le contexte d'autopsie, 2017 dans les métadonnées du Hub. Les libellés
existants sont conservés ; ce point doit être vérifié contre la publication.

## Méthode et conservation des comportements existants

Réutilisation sélective du noyau `percentiles.js` vérifié dans la branche externe,
et de la méthode Python `math.erfc` : **P = 100 × Φ(Z non arrondi)**.
Il s'agit du percentile du modèle normal associé au Z existant, pas d'une
nouvelle validation clinique de la distribution de chaque table.

Les anciens champs `zscores` / `zscore.z`, leurs arrondis et les critères
existants d'alerte sont conservés. Les exports ajoutent :

- Autopsie : `zscores_non_arrondis` et `percentiles`, clés gc/ma/mb.
- Neuropathologie, uniquement ME/MI : `zscore.z_brut` et `zscore.percentile`.
- Python : `z_brut_gc/ma/mb` et `percentile_gc/ma/mb` pour les masses.

Un P n'est pas inventé à partir d'un ancien Z arrondi. Le Hub et les comptes
rendus recalculent les anciens dossiers à partir des tables et des mesures ;
les archives JSON restent inchangées. En neuropathologie, un Z archivé n’est pas présenté comme un résultat recalculé lorsque la référence manque au terme courant ; il reste dans l’archive et sous z_archive dans le contexte. Les nouvelles saisies recalculent les
champs ajoutés au moment de l'export.

Les nouveaux P ne sont pas calculés pour un terme fractionnaire : les anciennes
règles d'arrondi des Z sont conservées, mais aucune règle d'interpolation nouvelle
n'est créée. Les jours séparément renseignés ne modifient pas les classes de SA.
Pour les organes nécessitant une strate MA, un grade absent en Python ne produit
pas de nouveau P MA ; les anciens Z restent inchangés pour compatibilité.
Le formulaire d'autopsie possède déjà un choix explicite 0 par défaut.

Le **grade de l'examen clinique est prioritaire dans le Hub et les CR**, comme
dans main, avec repli sur le grade d'autopsie. Le formulaire autonome utilise
son propre choix de grade. Comparer à terme et grade identiques ; des paramètres
contradictoires ne doivent pas être pris pour une erreur de percentile.
Le contexte effectivement utilisé est affiché sur les résultats recalculés.
Sans terme administratif, le terme du module d'autopsie ou de neuropathologie
est utilisable pour les masses correspondantes, sans modifier celui des autres modules.

## Présentation et sorties

Résultats de saisie, tableaux du Hub, CR complet/synthétique, aides de tableaux
Lumi et texte copiable du calculateur incluent les nouveaux P. L'ancien contrat
`calc_org` est conservé ; `calc_org_percentiles` fournit les sources supplémentaires
aux tableaux, y compris les masses sans référence GC.

Tableaux en Cambria 11 pt, repli Times New Roman/serif. Z-score insécable dans
les CR ; aucune colonne entièrement vide, zéro conservé, bordures neutres sans
soulignement rouge. Le pancréas seul conserve seulement ses colonnes GC.
Les tableaux du pack téléphone sont synchronisés avec les sources autonomes.

## Tests réalisés

`python -m unittest discover -s tests -v` : **7 tests réussis**.

- Oracle indépendant des tables : 136 combinaisons terme/grade, neuf masses,
  trois sources, limites de domaine, références absentes et macération.
- 2 001 points de Z entre −10 et +10, Python/JS à 2e−12 près.
- Empreinte des **128 résultats historiques de Z et d'alertes** inchangée.
- ME/MI : 222 cas Python/JS sur les domaines, zéro, moyenne, Z non arrondi et hors domaine, absence de mutation du document source ;
  rapport RI inchangé et compatibilité des anciens tableaux Lumi avec `ds` seul.
- Parcours Chromium : export JSON natif téléchargé, import ordinaire, recalcul
  d'un ancien dossier sans P exact, cas sans administratif, CR complet et synthèse,
  tableaux du Hub et calculateur unifié. Comparaison des transcriptions MB relevée.
- Font-family Cambria et taille 11 pt vérifiées dans la saisie réelle.
- Colonnes absentes, zéro, synchronisation HTML et pack vérifiés.
- Autotests : autopsie 131/131, neuropathologie 119/119, placenta 95/95,
  clinique 96/96, biométrie externe 61/61, radio 47/47.
  Trois assertions d'affichage de l'autopsie ont été adaptées : trois lignes
  de référence dans le tableau remplacent trois anciens badges ; calculs inchangés.
- Empreintes des tables JS, des références JSON existantes, des tables placentaires
  Python identiques à main pour les données médicales (la fonction de démarrage est désormais adaptée aux lanceurs, voir mise à jour).

`python hub/outils/verifier_cr.py` : **75 contrôles réussis**.
Inspection visuelle de tableaux et génération PDF A4 avec Chromium : en-têtes
lisibles, alignements conservés, colonnes MB absentes à 28 SA correctement omises.
Cambria n'est pas installée sous Linux : substitution effective ; Cambria réelle,
Finder, Safari, Word et impression sur Mac restent à vérifier.

## Essai manuel indépendant

Utiliser le serveur ordinaire de main et le Python disposant de Flask/Pillow.
Les raccourcis de lancement sont maintenant disponibles par reprise sélective.

```sh
python3 hub/app/serveur.py --base /chemin/vers/une/base_de_test --port 5005
```

Dans l'autopsie d'un dossier fictif, à 20 SA et grade 0, un foie de 14,33 g doit
donner Z GC = 0 et P GC = 50. Tester les autres références et les changements de
grade. En neuropathologie, à 28 SA, encéphale fixé 184,62 g et étage infratentoriel
7,63 g donnent chacun Z = 0 et P = 50 selon leurs tables propres.
Relire les résultats dans le Hub, le complet et la synthèse ; réexporter le JSON.
Ne pas conclure à la validation des entrées MB divergentes avant arbitrage.

Aucune table, aucun dossier médical existant, aucun port n'a été
modifié. Le serveur reste par défaut sur 5005. Aucune branche supprimée.

## Fichiers modifiés ou ajoutés

- `Macro/autopsie.html`
- `Macro/neuropath.html`
- `docs/VALIDATION_PERCENTILES_MASSES_ORGANES.md`
- `hub/app/biometrie.py`
- `hub/app/cr.py`
- `hub/app/cr_lumi.py`
- `hub/app/dossiers.html`
- `hub/app/gabarits/complet.jinja2`
- `hub/app/gabarits/synthese.jinja2`
- `hub/app/percentiles.py`
- `hub/app/percentiles_organes.py`
- `hub/app/serveur.py`
- `hub/app/web/percentiles.js`
- `hub/calculateur-unifie.html`
- `hub/outils/integrer_percentiles_organes.py`
- `hub/references/ecarts_transcriptions_masses.json`
- `hub/references/neuropath_masses.json`
- `pack_telephone.zip`
- `pack_telephone/EMPREINTES.txt`
- `pack_telephone/LISEZMOI.md`
- `pack_telephone/autopsie.html`
- `pack_telephone/neuropath.html`
- `tests/organes_browser.cjs`
- `tests/references_main.json`
- `tests/test_percentiles_organes.py`
- `tests/test_references_inchangees.py`

## Mise à jour : lancement autonome par double-clic

Les raccourcis ont été ajoutés à cette branche sans fusion dans test-integration.
Sur Mac, ouvrir `serveur.command` à la racine ; sur Windows, `serveur.bat`.
Port 5005 dans les deux cas. Le navigateur ne s'ouvre qu'après réservation
du port. Les dépendances sont préparées par les lanceurs existants repris
sélectivement. Aucun calcul, abaque ou dossier médical n'est modifié par cet ajout.

Le fichier local facultatif `base_locale.txt` permet de reprendre le même dossier
`hub` habituel, sans copier ni réinitialiser sa base. Il contient son chemin
absolu sur une seule ligne. Un chemin ne contenant pas `hub.sqlite` est refusé.
Arrêter le serveur précédent avec Ctrl+C avant de lancer l'autre branche :
les deux utilisent volontairement le même port 5005.

Les tests de lancement vérifient le serveur sur 5005, l'URL du navigateur,
le port occupé, les chemins avec espaces/accents, le choix de base locale et
les erreurs. Les essais réels Finder et Windows restent à réaliser.

Fichiers concernés par cette mise à jour : `.gitignore`, `serveur.command`,
`serveur.bat`, `hub/app/serveur.command`, `hub/app/serveur.bat`,
`hub/app/serveur.py`, `hub/app/requirements.txt`, `tests/test_lancement.py`,
`tests/references_main.json`, ce bilan et `docs/LANCER_BRANCHE_MAC.md`, ainsi que le lien de lancement dans `README.md`.
Les protections des tables numériques restent fondées sur main ; la protection
du démarrage a été mise à jour pour le lancement désormais demandé.

Validation après ajout des lanceurs : **11 tests réussis**, dont **4 tests de lancement**, sans changement des résultats médicaux précédents.
