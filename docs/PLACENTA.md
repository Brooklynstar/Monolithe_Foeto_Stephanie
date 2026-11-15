<!-- SPDX-License-Identifier: CC-BY-NC-SA-4.0 -->
# Module Placenta — branche module_placenta

Point de départ : `origin/main`, commit `a3cc4b914e6b95549ef5939d0fe8b4645dae357e`.
Dépôt : https://github.com/Brooklynstar/Monolithe_Foeto_Stephanie

Le module réunit les sections 18 à 20 du Google Form, dans l'ordre
Macroscopie (21 champs), Microscopie (10 champs), Conclusion (1 champ).
Les 155 choix sont à sélection unique. Les 16 réponses courtes restent des
champs texte, sans conversion numérique ni contrainte ajoutée. Tous les
champs cliniques sont facultatifs ; le numéro de dossier et l'opérateur
suivent les règles d'enregistrement du hub.

Le [relevé de référence](placenta_releve.md) est la partie descriptive du
fichier fourni, sans les instructions destinées à Codex. Ses graphies,
ponctuations et choix sont conservés. Le fichier joint emploie des apostrophes
droites et des guillemets droits là où le texte collé dans la conversation
emploie parfois leurs variantes typographiques ; la transcription jointe fait
référence pour ces caractères.

## Ouvrir et enregistrer

Depuis un dossier dans le hub, choisir l'onglet **Placenta**, puis **Le saisir
maintenant** ou **Rouvrir ce module**. Il existe aussi dans la page **Modules**.
Les trois sections se suivent et les liens en haut permettent d'y accéder.

La saisie existante est lue en base avant de permettre l'édition, y compris
sans opérateur dans l'URL. Saisir les initiales si nécessaire, puis utiliser
**Enregistrer au hub** avant de fermer. Les réponses antérieures non modifiées
et les clés supplémentaires du document sont conservées. La version précédente
reste dans l'historique du dossier. Le bouton **Dossiers** revient au même cas.
Pour changer de dossier, revenir à la fiche ; aucun brouillon n'est partagé
entre dossiers dans le navigateur.

Le module `placenta`, schéma `0.1.0`, utilise l'adaptateur à plat, la table
`valeurs_plates`, les archives et l'historique existants. Aucune nouvelle
migration SQL n'est nécessaire. Il est facultatif dans le suivi du dossier.
Les anciens modules `macro_placenta` et `grille_placenta` restent accessibles et
leurs données restent distinctes : aucune conversion automatique entre leurs
trames et celle du Google Form. Les gabarits de CR existants ne sont pas
étendus à cette nouvelle trame dans cette livraison.

## Libellés incomplets conservés — à vérifier avant correction

Les 13 occurrences suivantes semblent tronquées (la proposition de grade 2
est répétée dans deux questions) :

| Question | Libellé conservé |
|---|---|
| Membranes | de grade 2 - sévère (au moins 3 micro-abcès sous-choriaux, ou polynucléaires neutrophiles |
| Cordon micro | de grade 2 - sévère (polynucléaires neutrophiles confluents dans la parois des vaisseaux |
| Plaque choriale vaisseaux | hyperplasie histiocytaire chorionique (infiltrat lympho-histiocytaire lichénoïde de |
| Plaque choriale inflammation | de grade 2 - sévère (au moins 3 micro-abcès sous-choriaux, ou polynucléaires neutrophiles |
| Villosités | avance de maturation villositaire: villosités terminales hypotrophiques, avec un axe |
| Villosités | lésions de villite chronique (infiltrat inflammatoire à prédominance lymphocytaire, |
| Villosités | de haut grade (plusieurs foyers dont 1 foyer ‹ |
| Villosités | dystrophies villositaires avec villosités de grande taille, anfractueuses, présentant |
| Chambre intervilleuse | intervillite chronique d'étiologie indéterminée d'accompagnement (infiltrat inflammatoire |
| Chambre intervilleuse | intervillite chronique d'étiologie indéterminée de grade 1 (infiltrat inflammatoire à prédominance |
| Chambre intervilleuse | intervillite chronique d'étiologie indéterminée de grade 2 (infiltrat inflammatoire à prédominance |
| Chambre intervilleuse | intervillite chronique d'étiologie indéterminée de grade 3 (infiltrat inflammatoire à prédominance |
| Conclusion | des dystrophies villositaires fréquemment retrouvées dans les aneuploïdes ou |

Les graphies inhabituelles (`cubigue`, `foetalec(RIF)`, `avaculaires`,
`esamine`, `maternal foor infarct`, etc.) restent inchangées.
**Thrombose sous-choriale épaisseur max en cm** conserve son type choix unique
et sa seule réponse **Option 1** ; aucune mesure numérique n'est substituée.

Dans l'éditeur du Google Form, vérifier les contraintes de réponse courte
(nombre, plage, expression régulière), le caractère obligatoire des questions,
les éventuels sauts de section selon les réponses, les fins de libellés et la
configuration native Other du champ Cordon. Ces paramètres n'ont pas été
vérifiés dans l'éditeur et ne sont pas inventés ici. Seul **Autre + texte libre**
de **Cordon** révèle un texte libre ; **autre** dans **Cordon d'insertion** est
une réponse fixe. Le bouton d'effacement permet de laisser chaque choix vide.

## Récupérer cette branche seule

Dans un nouveau répertoire (cela évite de toucher à un travail local en cours) :

```sh
git clone --single-branch --branch module_placenta https://github.com/Brooklynstar/Monolithe_Foeto_Stephanie.git Monolithe-placenta
cd Monolithe-placenta
```

Mac, avec Python 3 installé :

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install flask pillow
python hub/app/serveur.py --port 5005
```

Windows PowerShell, avec Python 3 installé :

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install flask pillow
.\.venv\Scripts\python.exe hub\app\serveur.py --port 5005
```

Ouvrir http://127.0.0.1:5005. La base par défaut est `hub/hub.sqlite`.
Le lanceur Windows `serveur.bat` existant peut également être utilisé avec un
Python disposant de Flask. Aucun élément d'une autre branche n'est requis.

Pour essayer avec une base existante, arrêter le serveur habituel puis copier
**tout son répertoire de données** (`hub.sqlite`, archives, photos, etc.) vers
un autre répertoire local. Utiliser cette copie :

```sh
python hub/app/serveur.py --port 5005 --base "/chemin/vers/copie-hub"
```

Sous Windows, employer le Python du venv et un chemin Windows entre guillemets.
Ne pas lancer deux serveurs sur 5005. Le nouveau clone ne contient pas de
`DEMO_SLO_001` : les bases et saisies de test ne sont pas publiées.

## Tests exécutés le 15 novembre 2026

Environnement : Linux, Python 3.12, Flask 3.1.3, Chromium 156 via Playwright.
Pas de validation native sur Mac ou Windows dans cet environnement. Les
commandes et le code utilisent Python, Flask et les API Web communes aux deux
systèmes ; les essais natifs restent à effectuer sur leurs postes.

Aucune base locale et aucun dossier `DEMO_SLO_001` n'étaient disponibles.
Le test crée une base fictive équivalente (Smith-Lemli-Opitz, 19 SA, IMG), avec
un administratif, une saisie de l'ancien module macro et les trois sections
du nouveau module déjà renseignées. Il copie cette base et ses archives dans
un répertoire temporaire et teste uniquement la copie sur le port 5005.
Le répertoire de test et les saisies sont supprimés à la fin.

Commande exécutée :

```sh
python hub/outils/verifier_placenta.py --chromium /usr/bin/chromium
```

Résultats :

- navigation depuis le dossier vers Placenta et ouverture des trois sections préremplies ;
- comparaison intégrale des 32 champs et 155 choix au relevé : titres, ordre, types, ponctuation et facultativité ;
- sélection unique, effacement, texte Other et réponse fixe `autre` ;
- absence de relecture différée annulant un effacement après ouverture ;
- enregistrement dans les trois sections, fermeture, nouveau contexte navigateur, réouverture et restitution des valeurs ;
- conservation de l'administratif, du terme, de l'IMG, de l'indication, de l'ancien module macro, des valeurs préexistantes et des clés supplémentaires ;
- version précédente conservée dans l'historique ;
- autre dossier vide sans contamination, enregistrement possible avec les réponses facultatives vides ;
- erreur de lecture simulée : sauvegarde bloquée, saisie courante inchangée ;
- réindexation et intégrité SQLite vérifiées, base fictive source inchangée ;
- aucune erreur JavaScript pendant le parcours.

Le banc existant `python hub/outils/verifier_cr.py` passe aussi :
**75 vérifications, 0 échec**.

Pour reproduire le banc navigateur sur Mac ou Windows, installer en plus
`playwright`, puis son navigateur :

```sh
python -m pip install playwright
python -m playwright install chromium
python hub/outils/verifier_placenta.py
```

Aucune base ni aucun export de saisie n'est requis dans le dépôt pour ce test.
