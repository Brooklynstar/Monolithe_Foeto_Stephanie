<!-- SPDX-License-Identifier: CC-BY-NC-SA-4.0 -->
# Placenta 1.1.0 — présentation Monolithe et calculs intégrés

Les corrections sont réalisées sur `module_placenta`, puis fusionnées dans
`test-integration`. Point de départ de cette correction :
`ecac7375bc6823ed5d9ce8b393bda28b6790bd5c` pour la branche source,
`e6af2d1baf0f6a2f45063f28d7aa1036d75d23eb` pour l'intégration.
Aucune pull request vers Rémi n'est créée à ce stade.

## Présentation et contenu

Les styles des formulaires existants sont repris de `Macro/macro_placenta.html` :
jetons de couleur et de thème, largeur 920 px, en-tête, cartes, typographie,
champs, choix en boutons et boutons d'action. Les trois sections du formulaire
restent **Macroscopie**, **Microscopie**, **Conclusion**, dans cet ordre.
Les 32 champs, les 155 choix, leur ordre et les types de réponse sont inchangés.
Les champs du relevé restent facultatifs. Les métadonnées nécessaires au calcul
(terme et conditions de pesée) ne remplacent aucune question du relevé.

Les réponses à choix unique restent de vrais groupes radio accessibles, présentés
avec l'apparence des boutons de choix existants ; une réponse peut être effacée.
Le thème suit celui du hub. Le dossier et l'opérateur utilisent la liaison existante.

[Capture Placenta](captures/placenta-v110.png) ·
[Capture Macro placenta de référence](captures/placenta-reference.png).
Les captures montrent le dossier fictif fourni, aucune donnée clinique réelle.

## Calculs et mesures communes

Le moteur Python, le moteur JavaScript et les tables sont repris **sans changement**
de la version déjà présente dans `test-integration`. Ils sont inclus dans la
branche autonome. Aucune loi normale ni interpolation de percentile n'est ajoutée.

Le terme administratif fait autorité et est affiché en lecture seule lorsqu'il
existe ; sans terme administratif, il peut être renseigné pour le calcul.
Un poids frais paré et des conditions connues sont nécessaires. À **19 SA**, les
quantiles publiés Redline ne sont pas exploités : le motif est affiché.
À **28 SA**, **214 g frais paré → P50**, Z brut −0,13636… . Un poids fixé ou un
protocole inconnu ne reçoit pas de position percentile.

Le résultat est affiché près des mesures et sauvegardé dans le document. Le
serveur le recalcule : il ne fait pas confiance à un résultat transmis par le
navigateur. Le hub et les comptes rendus reprennent les trois sections et le
résultat. Les anciens CR restent des versions historiques.

Le champ **Percentile placenta** reçoit la position calculée si aucune
transcription manuelle n'existe. Une saisie manuelle ou une ancienne valeur
reste préservée, distincte du résultat de référence affiché. Un bouton permet
de reprendre explicitement le résultat calculé. Le calcul ne transforme pas
un texte historique en chiffre ni ne l'efface silencieusement.

Quatre mesures sont partagées avec Macro placenta :

| Placenta | Macro placenta |
|---|---|
| Poids du placenta en g | Masse parée |
| Longueur placenta en cm | Grand axe |
| largeur placenta en cm | Petit axe |
| Epaisseur placenta en cm | Épaisseur |

À l'ouverture, les valeurs de Macro placenta remplissent les champs vides du
nouveau module. Une divergence déjà présente est affichée avec les deux valeurs ;
il faut confirmer les mesures retenues ou reprendre celles de Macro placenta.
À l'enregistrement au hub, les mesures numériques communes sont mises à jour
**dans les deux documents, dans une seule transaction SQLite**. Cela fonctionne
également lorsqu'on modifie puis enregistre Macro placenta. Les constatations
propres aux autres champs et les clichés sont conservés, et les versions
antérieures restent dans l'historique. Aucun Macro placenta vide n'est créé.

Une réponse courte vide ou non numérique reste conservée dans Placenta mais
ne supprime pas une mesure numérique de Macro placenta. L'absence de mesure
utilisable est signalée dans le calcul. Le terme SLO n'est jamais modifié pour
obtenir un percentile. Les formulaires ouverts sur une version périmée sont
bloqués à l'enregistrement (HTTP 409) et demandent de relire les données.

Aucune migration SQL nouvelle. Le document du formulaire reste en schéma
`0.1.0`, avec des métadonnées supplémentaires compatibles avec l'adaptateur
à plat. La réindexation du dossier SLO a révélé une omission ancienne de la
table `examen_clinique_retention` dans les tables à vider : cette omission est
corrigée pour permettre de réindexer sans doublon.

## Essayer la branche autonome

Dans un clone de `module_placenta`, avec Python 3.10+ :

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install flask pillow
python hub/outils/importer_placenta_demo.py --base "/chemin/vers/base-test-placenta"
python hub/app/serveur.py --port 5005 --base "/chemin/vers/base-test-placenta"
```

L'importeur utilise le fichier exact `hub/exemples/DEMO_SLO_001.json` inclus
sur la branche. Il refuse de remplacer un dossier SLO déjà présent. Les bases
et nouvelles saisies ne sont pas versionnées. Ouvrir http://127.0.0.1:5005,
le dossier **DEMO_SLO_001**, puis **Placenta → Le saisir maintenant**.
Les mesures de Macro placenta sont reprises sans les ressaisir.

Sous Windows : `py -3 -m venv .venv`, puis remplacer `python` dans les commandes
par `.\.venv\Scripts\python.exe`. Le lanceur Windows existant peut aussi être
utilisé avec Flask installé. Le module ne nécessite aucun fichier d'une autre branche.

## Tests sur la branche autonome — 15 novembre 2026

Linux, Python 3.12, Chromium 156 via Playwright. Pas d'essai natif Mac/Windows.

- **4 tests d'intégration/protection réussis**, dont un parcours du vrai serveur
  sur **5005**, avec le fichier SLO exact, une base temporaire, fermeture du
  navigateur et arrêt/redémarrage du serveur ; les trois sections et les
  résultats sont retrouvés. Les huit saisies source et les deux CR historiques
  sont conservés lorsque leurs mesures ne sont pas modifiées.
- Comparaison des styles calculés avec Macro placenta : corps, largeur,
  en-tête, titre, cartes, champs, choix non sélectionnés et sélectionnés,
  dans les **quatre thèmes**. Captures inspectées ; affichage mobile sans
  débordement horizontal. Le contenu des cartes reste propre au module.
- Les **32 champs / 155 choix** sont comparés au relevé ; les libellés ne sont
  pas corrigés. **918 cas Python/JavaScript** du moteur existant concordent.
- Test positif **28 SA / 214 g → P50** et synchronisation inverse **321 g → P90** ;
  protocole fixé/inconnu exclus, résultats falsifiés recalculés par le serveur.
- Conservation des clichés (archive base64 comprise), clés supplémentaires,
  textes historiques, autres constatations et historique ; conflit de version
  bloqué avant toute écriture. Réponses non numériques conservées sans supprimer
  une mesure existante. Réindexation et intégrité SQLite vérifiées.
- Les CR complet, synthèse et placentaire contiennent les nouvelles sections.
  **75 contrôles existants des CR réussis**, ainsi que le banc historique
  `verifier_placenta.py` adapté à la synchronisation des mesures.
- Aucune erreur JavaScript dans le parcours final.

Les essais intermédiaires ont révélé et permis de corriger la fausse alerte de
perte de données quand un résultat calculé devient inapplicable, ainsi que le
doublon de réindexation de la rétention clinique mentionné plus haut.

Pour reproduire : installer `playwright` pour Python, puis
`python -m playwright install chromium`. Exécuter :

```sh
python -m unittest discover -s tests -p 'test_*.py' -v
python hub/outils/verifier_placenta.py
python hub/outils/verifier_cr.py
```

Le premier banc accepte `MONOLITHE_CHROMIUM` pour utiliser un navigateur déjà
installé ; le banc historique accepte `--chromium /chemin/chromium`.

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
