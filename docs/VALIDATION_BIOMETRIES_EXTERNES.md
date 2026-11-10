# Biométries externes — bilan du 10 novembre 2026

Branche créée directement depuis `main` a3cc4b914e6b95549ef5939d0fe8b4645dae357e.
Référence comparée : `percentiles_biometries` 447ab7314df29b536bdbc9708a16af3f78078378.

## Développement

Reprise sélective du moteur Python, du noyau JavaScript, des exports et des
comptes rendus. Les fichiers du moteur `biometrie.py`, du contexte `cr.py`,
du noyau `percentiles.js` et des deux gabarits sont identiques à cette référence.
Aucune reprise du serveur, des lanceurs ou de changements de port.
Les libellés de main sont conservés, notamment PC (périmètre crânien).
Les tables de références JSON restent strictement celles de main.

Le percentile utilise exclusivement le Z non arrondi : 100 × Φ(Z).
Les anciens champs `ecarts` sont conservés ; `ecarts_non_arrondis` et
`percentiles` sont ajoutés aux nouveaux exports. Les JSON archivés ne sont pas
réécrits. Les anciens dossiers sont recalculés au rendu avec les tables disponibles.
Sans tables ni Z exact, aucun percentile n'est inventé à partir d'un ancien Z arrondi.

Présentation : colonnes sans aucune valeur masquées au calculateur et retirées
du tableau externe des comptes rendus ; zéro reste une valeur. Les tableaux
de saisie présentent seulement les références disponibles. Cambria 11 points,
substitution Times New Roman puis serif ; bordures neutres, aucune ligne rouge
sous les anomalies. Les en-têtes conservent leurs intitulés et Z-score est insécable.
Les critères médicaux et les calculs des organes sont inchangés.
Le pack téléphone et son archive sont régénérés depuis les sources.

## Fichiers

- Macro/biometrie_clinique.html
- hub/app/biometrie.py
- hub/app/cr.py
- hub/app/cr_lumi.py
- hub/app/gabarits/complet.jinja2
- hub/app/gabarits/synthese.jinja2
- hub/app/web/percentiles.js
- hub/calculateur-unifie.html
- hub/outils/integrer_percentiles.py
- hub/outils/verifier_cr.py
- pack_telephone/biometrie_clinique.html
- pack_telephone/EMPREINTES.txt
- pack_telephone/LISEZMOI.md
- pack_telephone.zip
- tests/test_percentiles.py
- tests/test_parcours_percentiles.py
- tests/percentiles_browser.cjs
- docs/VALIDATION_BIOMETRIES_EXTERNES.md

## Validation exécutée sous Linux

`python -m unittest discover -s tests -v` : 14 tests réussis.
Python 3.12, Flask 3.1.3, Pillow 12.3.0, Playwright et Chromium.

- Oracle indépendant des tables : domaines, unités, termes absents/fractionnaires,
  références indisponibles, valeurs extrêmes et Z non arrondi.
- Python/JavaScript : 2 001 Z entre −10 et +10, tolérance absolue 2e−12.
- Empreintes des tables inchangées ; 128 calculs de masses d'organes inchangés.
- Parcours navigateur : 8 dossiers, 70 percentiles de saisie, 80 percentiles JSON,
  140 vérifications de percentiles de comptes rendus, 70 au calculateur.
- Import et réexport d'un ancien dossier, conservation de l'archive JSON,
  relecture des résultats et reprise dans complet/synthèse.
- Colonnes visibles comparées à leur contenu réel ; zéro, colonnes absentes,
  famille et taille de police vérifiés automatiquement.
- Autotests : biométrie 61/61 (source et téléphone), clinique 96/96,
  autopsie 131/131, neuropathologie 119/119, placenta 95/95, radio 47/47.

`python hub/outils/verifier_cr.py` : 76 vérifications réussies.
L'assertion historique à une décimale a été adaptée au Z externe à deux décimales.
`bash` n'est pas nécessaire à cette branche. `git diff --check` : réussi.
Un tableau de compte rendu a été inspecté visuellement à 1 000 px ; export PDF A4
paysage généré avec Chromium. Aucune coupure dans les en-têtes observés.

## Limites et suite

Cambria n'est pas installée dans l'environnement Linux : famille CSS vérifiée,
mais glyphe Cambria réel à contrôler sur Mac et Windows, ainsi que Word,
impression et export dans les logiciels utilisés au cabinet. La synthèse est un
compte rendu textuel : les percentiles y sont repris sous forme de lignes.
La validation médicale finale et les essais sur dossiers représentatifs restent
à réaliser par l'utilisatrice. Aucun écart numérique constaté avec le moteur
repris de l'ancienne branche ; aucune valeur de référence modifiée.

Conserver `percentiles_biometries` et `port_5006` jusqu'à validation explicite.
Elles pourront être proposées à la suppression après validation complète et
vérification de l'absence de développements encore utiles ; rien n'est supprimé.
Aucune fusion ni création de `stephanie_stable`.

## Séparation du dossier fictif permanent

Le dossier SLO, ses sources et ses comptes rendus ont été récupérés dans
`dossier_demonstration`, branche indépendante issue de main. Les scripts,
base isolée et conditions spécifiques au dossier fictif ont été retirés de
cette branche. Les améliorations générales de présentation des biométries
dans le Hub et à l'impression restent ici, sans identifiant de dossier codé
en dur. Les tables et moteurs de calcul restent inchangés.
