# Démonstration — Syndrome de Smith-Lemli-Opitz

Dossier **DEMO_SLO_001**, opérateur **Codex**, entièrement fictif.
Il est fourni sur la branche `percentiles_biometries_externes` uniquement.
Aucune donnée réelle, photographie de patient ou analyse biologique réelle.

## Ouvrir sur Mac, sans importer de JSON

1. Télécharger cette branche :
   https://github.com/Brooklynstar/Monolithe_Foeto_Stephanie/archive/refs/heads/percentiles_biometries_externes.zip
2. Décompresser le ZIP dans un dossier séparé de votre installation clinique.
3. Installer Python 3.10 ou plus récent depuis https://www.python.org/downloads/macos/
   si Python n'est pas déjà disponible.
4. Double-cliquer **ouvrir_demonstration.command**, à la racine du dossier décompressé.
5. Dans le navigateur ouvert automatiquement, cliquer **DEMO_SLO_001**.

Le premier lancement prépare un environnement Python indépendant `.demo-python`
et télécharge Flask/Pillow si nécessaire. Internet sert à cette installation ;
la consultation de la démonstration fonctionne ensuite exclusivement en local.
Garder la fenêtre Terminal ouverte ; **Ctrl+C** arrête cette démonstration.

La page porte un bandeau **CAS ENTIÈREMENT FICTIF**. Le dossier apparaît déjà
complet dans la liste : aucune création ni succession d'imports n'est nécessaire.
L'onglet **biométrie clinique** donne les Z-scores et percentiles par référence.
L'onglet **Compte rendu** contient déjà un complet et une synthèse : **Relire**
pour les consulter, ou choisir un gabarit et **Produire un brouillon**.
Les sources et les comptes rendus sont attribués à Codex.
Le lien **Exporter le dossier JSON** du bandeau télécharge toutes les rubriques
et les biométries recalculées. Le module de saisie biométrique permet aussi
son export JSON habituel.

Si macOS bloque l'ouverture, suivre ses options d'autorisation d'une application
identifiée. Si les droits d'exécution ont été perdus à la décompression, dépannage
ponctuel dans le Terminal, depuis ce dossier :

```sh
chmod +x ouvrir_demonstration.command reinitialiser_demonstration.command
```

Le port par défaut est **5005**, sur `127.0.0.1` seulement. Si votre Hub clinique
utilise déjà ce port, fermer la démonstration en erreur, arrêter le Hub clinique
ou lancer, dans ce dossier :

```sh
./ouvrir_demonstration.command --port 5011
```

En cas de port occupé, le lanceur n'ouvre pas le navigateur sur le service existant.

## Isolation, relance et réinitialisation

Les données de test vivent uniquement dans **.demo-slo/base/**. Le chargement
ne prend aucun chemin de base clinique en paramètre de ligne de commande et
n'utilise jamais `hub/hub.sqlite`. Une base cible déjà remplie mais sans marqueur
de démonstration est refusée, avant migration ou ingestion. Une base marquée
contenant un autre identifiant de dossier est également refusée.
Ne pas importer de dossier réel dans cette base de démonstration.

Une relance réapplique les sources : un seul dossier, huit saisies initiales et
deux comptes rendus initiaux. Les essais de génération manuelle produisent de
nouveaux brouillons historiques, comme dans le Hub normal. Les sources changées
ou les saisies modifiées donnent lieu à un nouveau jeu de comptes rendus ;
une relance sans changement n'ajoute rien. Les dates de génération des nouveaux
brouillons sont celles de l'exécution ; les résultats biométriques sont reproductibles.

Pour repartir à zéro après vos essais : arrêter le serveur, puis double-cliquer
**reinitialiser_demonstration.command**. Cette action efface uniquement la base
fictive réservée, y compris ses modifications et brouillons, puis réinstalle les
sources et rouvre le Hub. Elle refuse également une base non marquée ou contenant
un autre dossier. Elle ne touche pas à la base clinique.

Chargement seul pour les tests automatisés, avec un Python disposant de Flask/Pillow :

```sh
python3 hub/outils/demonstration_slo.py --preparer
```

## Scénario médical simulé

Fœtus masculin de 19 SA, sexe chromosomique fictif 46,XY. Petit poids, réduction
du périmètre crânien, syndactylie cutanée bilatérale 2–3 des pieds, hypospadias
proximal, petit bourgeon génital et scrotum bifide. Examen interne,
neuropathologie, radiologie, placenta et histologie sont décrits comme simulés.
Aucune confirmation biologique ou moléculaire n'est revendiquée.

La conclusion sépare les constatations de l'hypothèse de Smith-Lemli-Opitz,
qui demanderait une confirmation par étude des stérols, notamment du
7-déhydrocholestérol, et analyse de DHCR7. Les aspects morphologiques ne sont
pas présentés comme une preuve diagnostique.

Les sources `DEMO_SLO_001/*.json` ne contiennent **aucun percentile ni Z-score
précalculé**. Le chargeur appelle le moteur biométrique existant, puis enregistre
les résultats dans les champs habituels des nouveaux JSON. Le Hub et les comptes
rendus reprennent ces données ; les valeurs exactes sont conservées dans l'export.

| Mesure | Valeur | But du test |
| --- | ---: | --- |
| Masse | 150 g | Inférieure aux références, interprétation variable selon la référence |
| PC | 130 mm | Microcéphalie dans le scénario |
| BIP / FO | 35 / 45 mm | Valeurs basses, Müller-Brochut disponible |
| Pied | 29,5 mm | Z MB = 0, percentile MB = 50 calculé automatiquement |
| Main | 25,4 mm | Au-dessus de la moyenne MB, Z = +1,5 |
| PT | 126,4 mm | Proche de la moyenne MB |
| VT / VC | 220 / 145 mm | Comparaison des trois références |
| PA | 95 mm | Autre mesure sous la moyenne |
| DICI, DICE, fentes palpébrales, DIM, sternum | Non renseignés | Cellules absentes et champs vides |

Toutes les références étant disponibles à 19 SA sur au moins certaines mesures,
les trois groupes de colonnes sont légitimement conservés dans ce dossier.
Le cas d'une référence entièrement vide est vérifié séparément dans les tests.
Une colonne contenant zéro est conservée.

## Validation technique — 10 novembre 2026

- Suite complète Python/Chromium : **19 tests réussis**, dont 5 pour cette démonstration.
- Vérificateur des comptes rendus existant : **76 contrôles réussis**.
- Un dossier, huit saisies, deux comptes rendus initiaux ; deuxième chargement
  sans doublon et export identique. Réinitialisation isolée vérifiée.
- Refus d'une base non marquée et d'une base marquée contenant un autre dossier,
  avec contrôle de l'absence de modification des octets de la base refusée.
- Parcours réel Chromium : liste du Hub → fiche biométrique → complet et synthèse
  → réouverture du module avec ses mesures → téléchargement JSON. Comparaison
  des percentiles exportés Python/JavaScript à 2e−12 près.
- Sources sans Z ni percentiles ; vérification de 100 × Φ(Z) à partir des Z exacts,
  cohérence avec les lignes recalculées des comptes rendus.
- Colonnes vides masquées, zéro préservé ; Cambria 11 déclarée, en-têtes et absence
  de soulignement vérifiés dans le conteneur réel du Hub.
- Inspection visuelle du tableau et export PDF A4 avec Chromium ; regroupement
  du titre/tableau, en-têtes en `thead`, Z-score insécable et bordures neutres.
- Lanceur Bash exécuté sous Linux depuis /tmp, avec environnement Python déjà
  préparé ; contrôle syntaxique des deux .command réussi.
- Les tests numériques antérieurs, les autotests des modules et les 128 calculs
  de masses d'organes inchangés passent. Aucune table de référence modifiée.

Corrections d'affichage liées au parcours : tableau biométrique du Hub enrichi
des percentiles archivés ; pas de percentile inventé pour un ancien Z arrondi.
Le noyau JS commun est intégré aussi à la page du Hub. Le module `micro` est
reconnu comme la rubrique `microscopie` dans la liste des modules manquants du CR.
La conclusion fictive n'est insérée que pour `DEMO_SLO_001` avec son indicateur
explicite ; le comportement des autres dossiers reste celui des gabarits habituels.

Limites : environnement Linux, sans Cambria installée. La substitution de police
est donc utilisée ici. Tester sur un véritable Mac le double-clic Finder,
l'installation initiale, les autorisations, Cambria réelle, Safari/Chrome,
l'impression et le copier-coller Word. La synthèse reste textuelle. La cohérence
médicale pédagogique a été relue dans les sources et le rendu ; aucune validation
clinique humaine n'est revendiquée. Le scénario ne teste pas des maladies réelles
ni les analyses de confirmation. Aucun fichier PDF de rapport n'est imposé aux
installations : les comptes rendus sont générés localement.

Les seules écritures Git concernent `percentiles_biometries_externes`.
Aucune fusion, suppression de branche ou modification de `main`,
`raccourcis_lancement` ou `stephanie_stable`.
