# Percentiles placentaires — bilan du 10 novembre 2026

Branche indépendante `percentiles_placenta`, créée directement depuis
`main` a3cc4b914e6b95549ef5939d0fe8b4645dae357e.
Bilan de la branche indépendante avant intégration. Sur demande explicite, ce
développement est désormais réuni dans `test-integration` ; main et les versions
stables restent inchangées.

## Résultat et limites à connaître avant les essais

La branche situe le **poids placentaire** parmi les seuils **P10, P50, P90**
présents dans main, sans inventer de percentile exact entre ces seuils.
Les valeurs hors bornes sont classées `< P10` / `> P90`, les valeurs intermédiaires
`P10–P50` / `P50–P90`. À une valeur égale à un seuil, le nom de ce seuil est
indiqué. Le champ **percentile_exact reste toujours null** : l'égalité avec un
seuil transcrit arrondi n'est pas présentée comme une précision statistique infinie.

**Aucune loi normale n'est supposée pour déduire ces positions.** Exemple à
28 SA : 214 g correspond au P50 transcrit alors que le Z descriptif est non nul,
la moyenne étant 223 g. Appliquer Φ(Z) aurait donné une autre valeur et aurait
contredit le seuil empirique. Il n'y a ni interpolation, ni extrapolation nouvelle.

La référence Redline réellement étiquetée comme telle dans main couvre ici
**22–42 SA**. Les données 18–21 sont explicitement marquées `Extrapol` dans
`cr_lumi.py` : elles sont conservées dans leurs tables d'origine mais ne servent
pas à produire les nouvelles positions percentiles.

Müller-Brochut possède des moyennes/ET placentaires à 12–20 SA dans le calculateur.
Le dépôt ne documente pas suffisamment leur distribution ni leur protocole pour
en déduire un percentile exact : **aucun Φ(Z) n'est ajouté pour ce placenta MB**.
Ses anciens Z du calculateur restent disponibles, accompagnés de la mention
« percentile non déterminable ». Cette limite reste à lever sur documentation
originale avant tout développement d'un percentile numérique supplémentaire.

## Inventaire de main et conditions de mesure

- `Macro/macro_placenta.html` : **pièce fraîche**, masse parée en grammes dans la
  section `paree`, après retrait du cordon et des membranes, avant les tranches.
- `hub/app/cr_lumi.py` : `DONNEES_PLACENTA`, contenant moyenne, ET, P10/P50/P90
  et provenance Redline ou Extrapol ; `RATIO_FP`, référentiel distinct du rapport.
- `hub/calculateur-unifie.html` : `RED` 18–42 SA avec moyennes/ET et `MB_O.Placenta`
  12–20 SA. Le tableau RED ne contient pas, à lui seul, de quantiles empiriques.
- Aucune autre mesure placentaire du module (axes, épaisseur, cordon…) ne possède
  ici d'abaque exploitable pour un nouveau percentile ; aucun n'est inventé.

La copie `hub/references/placenta_percentiles.json` reprend numériquement
`DONNEES_PLACENTA` sans changer aucune valeur. Le JavaScript autonome est généré
à partir de cette copie, pour éviter des transcriptions Python/JS divergentes.
Les tables originales JS et Python restent intactes.

Un choix explicite de **conditions de pesée** distingue frais paré, fixé et
non précisé/non paré. Seul le poids frais paré est proposé à cette comparaison.
Le choix frais paré est celui du formulaire natif de main ; le calculateur
unifié demande explicitement de le choisir avant de proposer une position.
La conformité des transcriptions et du protocole Redline avec la publication
originale reste à confirmer lors de la validation médicale ; les noms de source
viennent du dépôt et ne constituent pas une nouvelle vérification bibliographique.

Les poids fixés, protocoles inconnus, masses négatives/non finies/absentes et
termes non entiers ou hors domaine ne produisent pas de nouvelle comparaison.
Zéro reste une donnée numérique, jamais une cellule vide. Les jours n'introduisent
pas d'interpolation entre les semaines des tables.

**Le rapport fœto-placentaire reste distinct.** Ses calculs historiques, sa table
RATIO_FP et les critères existants ne sont pas modifiés ; aucun nouveau percentile
de rapport n'est déduit du percentile de masse. Les Z descriptifs et classifications
historiques de Lumi sont conservés ; seule la nouvelle position percentile est
soumise aux conditions et domaines ci-dessus dans son contexte de rendu.

## Sorties et anciens dossiers

- Saisie : résultat calculé automatiquement, Z descriptif non arrondi utilisé,
  affichage à deux décimales, position parmi les seuils et limite éventuelle.
- Export JSON : champs supplémentaires `conditions_masse` et
  `resultats_placentaires`, avec terme, masse, méthode, seuils, Z brut, position,
  `percentile_exact: null` et raison de non-calcul éventuelle.
- Hub : tableau recalculé à la consultation, à partir des mesures et des tables
  du dépôt ; endpoint de lecture `/api/dossiers/<numero>/percentiles-placenta`.
- Compte rendu complet : tableau HTML ; synthèse : reprise textuelle.
- Compte rendu placentaire dédié : nouveau gabarit version 1.2.0 au **format HTML**
  pour que le tableau soit réellement affiché, imprimable et copiable, et non du
  HTML littéral dans un compte rendu texte. Les anciens CR texte restent relus
  dans leur format d'origine ; aucune migration ni réécriture des archives.
- Calculateur : Z historiques conservés ; position empirique Redline dans les
  cellules et le texte copiable, avec refus du nouveau P si conditions inconnues.

Sur un ancien JSON natif, la section `paree` du module frais permet de reconnaître
le protocole initial. Une structure différente sans information de pesée est
considérée non documentée, sans hypothèse automatique. Le terme administratif
reste prioritaire s'il est présent, sinon celui de la macroscopie placentaire.
Les résultats archivés ne sont pas pris pour une nouvelle référence statistique.

Cambria 11 pt avec repli Times New Roman/serif, en-têtes sans coupure de Z-score,
colonnes entièrement vides omises, zéro conservé, alignement des valeurs et
bordures neutres sans soulignement rouge. Le pack téléphone est synchronisé.

## Validation réalisée

`python -m unittest discover -s tests -v` : **5 tests réussis**.

- **918 cas** comparés Python/JavaScript/calculateur : limites de SA, valeurs
  autour des seuils, égalités P10/P50/P90, données absentes, zéro et protocoles.
- Cas où P50 diffère de la moyenne : aucune substitution de percentile normal.
- Refus des semaines extrapolées, termes fractionnaires, poids fixés et protocole inconnu.
- Export JSON natif réellement téléchargé ; import d'un ancien JSON sans résultats,
  recalcul dans les trois comptes rendus et le Hub ; archive originale inchangée.
- Format HTML effectif vérifié pour le complet et le CR placentaire ; synthèse texte.
- Famille Cambria et taille 11 pt vérifiées dans la saisie réelle.
- Colonnes manquantes, présence du zéro et synchronisation du pack vérifiées.
- Autotests : autopsie 131/131, neuropathologie 119/119, placenta 95/95,
  clinique 96/96, biométrie externe 61/61, radio 47/47.
- Empreintes des tables JS, références JSON existantes, DONNEES_PLACENTA,
  RATIO_FP, autres modules médicaux concernés identiques à main pour les données médicales (le démarrage est désormais adapté aux lanceurs, voir mise à jour).

`python hub/outils/verifier_cr.py` : **75 contrôles réussis**.
Inspection visuelle et génération PDF A4 d'un tableau : en-têtes lisibles,
valeurs alignées et colonnes sans données omises.
Cambria réelle n'est pas installée sous Linux ; substitution effective. Finder,
Safari, Word, Cambria installée et impression sur Mac restent à vérifier.
Aucune base clinique réelle n'a été utilisée pour les essais.

## Essai manuel indépendant

Utiliser le serveur ordinaire de main et un Python disposant de Flask/Pillow :

```sh
python3 hub/app/serveur.py --base /chemin/vers/une/base_de_test --port 5005
```

Sur un dossier fictif, saisir **28 SA, pièce fraîche parée, masse 214 g** :
Z descriptif ≈ −0,14, position **P50**, percentile exact non déterminable.
Choisir « fixé » : la comparaison doit disparaître avec une explication, sans
modifier la masse saisie. Tester 140 g (P10) et 321 g (P90) à ce même terme.
À 19 SA, aucun nouveau percentile Redline publié n'est proposé : le dossier SLO
à 19 SA n'est donc pas un cas positif pour cet abaque.
Vérifier le complet, la synthèse, le CR placentaire et le JSON.

Initialement, aucun réglage de serveur ou de raccourci n'était modifié ; port par défaut 5005.
La branche ne reprend ni les percentiles d'organes ni les biométries externes.
Aucune branche supprimée. Les limites statistiques ci-dessus ne doivent pas être
confondues avec une validation clinique humaine ou un modèle normal démontré.

## Fichiers modifiés ou ajoutés

- `Macro/macro_placenta.html`
- `docs/VALIDATION_PERCENTILES_PLACENTA.md`
- `hub/app/cr.py`
- `hub/app/cr_lumi.py`
- `hub/app/dossiers.html`
- `hub/app/gabarits/complet.jinja2`
- `hub/app/gabarits/placenta.jinja2`
- `hub/app/gabarits/synthese.jinja2`
- `hub/app/percentiles.py`
- `hub/app/percentiles_placenta.py`
- `hub/app/serveur.py`
- `hub/app/web/percentiles_placenta.js`
- `hub/calculateur-unifie.html`
- `hub/outils/integrer_percentiles_placenta.py`
- `hub/references/placenta_percentiles.json`
- `pack_telephone.zip`
- `pack_telephone/EMPREINTES.txt`
- `pack_telephone/LISEZMOI.md`
- `pack_telephone/macro_placenta.html`
- `tests/placenta_browser.cjs`
- `tests/references_main.json`
- `tests/test_percentiles_placenta.py`
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

Validation après ajout des lanceurs : **9 tests réussis**, dont **4 tests de lancement**, sans changement des résultats médicaux précédents.
