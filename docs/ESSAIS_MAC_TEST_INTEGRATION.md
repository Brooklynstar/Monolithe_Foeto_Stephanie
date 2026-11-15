# Monolithe Stéphanie — version test-integration sur Mac

Cette branche réunit `dossier_demonstration`, `percentiles_biometries_externes`
, `raccourcis_lancement`, `percentiles_masses_organes` et
`percentiles_placenta`, avec le nouveau module `Placenta` fusionné depuis
`module_placenta`. Elle utilise **le serveur ordinaire**, exclusivement
sur `127.0.0.1`, avec **5005** comme port par défaut. Aucun hébergement distant,
aucun serveur ou écran réservé au dossier fictif, aucune base de démonstration.
Le port 5005 reste le défaut de la branche indépendante `raccourcis_lancement`.

## Mise à jour du 15 novembre 2026 — nouveau module Placenta

Fusion sans conflit de `module_placenta` (`ecac7375bc6823ed5d9ce8b393bda28b6790bd5c`)
dans `test-integration` (point de départ `a59f0323a85396de161fc80b86761f42a94cec87`).
La branche source `module_placenta` reste disponible séparément. L'ancien module
**Macro placenta**, ses calculs et ses tables de référence sont conservés.
Le nouvel onglet **Placenta** rassemble **Macroscopie**, **Microscopie**,
**Conclusion**, dans cet ordre. [Relevé et libellés à vérifier](PLACENTA.md).

### Récupérer et essayer avec GitHub Desktop sur Mac

Pour un essai isolé, sans toucher à votre installation habituelle :

1. Arrêter Monolithe avec **Ctrl+C** dans son Terminal pour libérer le port 5005.
2. Dans **GitHub Desktop → File → Clone Repository… → URL**, saisir
   `https://github.com/Brooklynstar/Monolithe_Foeto_Stephanie.git`.
   Choisir un **nouveau dossier local**, par exemple `Monolithe-test-integration`,
   puis **Clone**. Si ce clone d'essai existe déjà, le sélectionner dans
   **Current Repository**, puis cliquer **Fetch origin**.
3. Dans **Current Branch**, sélectionner **test-integration** (chercher ce nom
   dans la liste des branches distantes si nécessaire). Cliquer **Pull origin**
   si ce bouton apparaît après **Fetch origin**. Ne pas choisir `module_placenta`
   pour cet essai : `test-integration` réunit les deux modules et les percentiles.
4. Vérifier le propriétaire du dépôt : **Repository → Repository Settings… →
   Remote** doit indiquer votre fork `Brooklynstar/Monolithe_Foeto_Stephanie`.
   Vérifier **Current Branch : test-integration**, puis **Repository → Show in Finder**.
5. Dans ce nouveau dossier, double-cliquer **serveur.command**. Python 3.10 ou
   plus récent est nécessaire ; le lanceur prépare son environnement et ses
   dépendances au premier lancement. Laisser le Terminal ouvert.
   Monolithe s'ouvre sur **http://127.0.0.1:5005**.
6. Dans **Ingestion → Déposer des JSON → les choisir**, sélectionner le fichier
   **hub/exemples/DEMO_SLO_001.json** de ce clone. La reprise est automatique.
   Si ce dossier est déjà présent dans la base choisie, l'ouvrir directement.
7. Revenir à **Dossiers** et ouvrir **DEMO_SLO_001**. Saisir vos initiales dans
   le bandeau. L'onglet **Placenta → Le saisir maintenant** ouvre les trois
   sections. Après saisie, cliquer **Enregistrer au hub**, revenir à **Dossiers**,
   puis **Placenta → Rouvrir ce module** pour retrouver les valeurs.
8. Ouvrir aussi **macro placenta → Rouvrir ce module** : les données du dossier
   fourni comprennent 19 SA, une masse placentaire parée de 90 g, des axes de
   9 × 8 cm et un cordon de 22 cm. À 19 SA, l'absence de percentile Redline
   est attendue et expliquée à l'écran (référence exploitable de 22 à 42 SA).

Ce clone neuf utilise son propre `hub/hub.sqlite`, créé au premier lancement.
Les nouvelles saisies restent dans ce répertoire local et ne doivent pas être
commitées. Pour continuer à utiliser votre installation et votre base habituelles,
voir les précautions et le réglage `base_locale.txt` décrits plus bas. Ne pas
remplacer une base existante avec une base d'essai.

Si macOS refuse l'exécution du lanceur, ouvrir un Terminal **dans ce dossier** :

```sh
chmod +x serveur.command hub/app/serveur.command
./serveur.command
```

### Résultats réellement exécutés après fusion

Environnement : Linux, Python 3.12 et Chromium 156. Pas d'essai natif macOS.
Aucun conflit de fusion et aucune correction de code fonctionnel nécessaire.

- **37 tests existants réussis**, dont les 918 cas Python/JavaScript/calculateur
  unifié des percentiles placentaires et les autotests des modules.
- **1 nouveau test navigateur d'intégration réussi** : vrai serveur ordinaire
  sur **5005**, import du fichier exact `hub/exemples/DEMO_SLO_001.json` par
  l'interface Ingestion, puis accès aux deux onglets depuis le dossier.
- **32 champs et 155 choix** comparés au relevé ; les trois sections ouvertes
  dans l'ordre et renseignées, y compris le texte libre de Cordon.
- Après fermeture du navigateur et arrêt/redémarrage du processus serveur sur
  la même base temporaire : les valeurs des trois sections sont retrouvées ;
  les **huit saisies préexistantes** et les **deux CR historiques** sont inchangés.
- Macro placenta : **90 g à 19 SA**, axes et cordon retrouvés ; absence attendue
  de percentile Redline, avec le motif de limite affiché.
- Cas positif distinct, sans changer le terme du SLO : **28 SA, 214 g frais paré
  → P50**, identique dans le navigateur et l'API ; Z brut **−0,13636…**,
  aucun percentile exact interpolé. Poids fixé exclu de la comparaison.
- **76 contrôles des comptes rendus réussis**. Aucune erreur JavaScript dans
  le nouveau parcours. Le fichier SLO source reste identique octet pour octet.

La base et les saisies générées vivent dans un répertoire temporaire supprimé
à la fin du test. Aucun fichier de données supplémentaire n'est versionné.

Commandes de validation :

```sh
python -m unittest discover -s tests -p 'test_*.py' -v
python hub/outils/verifier_cr.py
```

Le test ajouté s'exécute aussi seul avec
`python -m unittest discover -s tests -p test_reunion_placenta.py -v`.
Les bancs nécessitent Python Playwright (`pip install playwright`), Node
Playwright (`npm install playwright` hors du dépôt), et leurs navigateurs de test.
`MONOLITHE_CHROMIUM` permet de désigner un Chromium déjà installé.

## Récupérer la version sans écraser vos données

### Avant de changer de version

Dans votre Monolithe actuel, utiliser **Sauvegarde** vers un dossier extérieur
à l'installation. Vérifier que la sauvegarde contient `hub.sqlite`, `archive/`
et `photos/` si ces dossiers contiennent des données. Puis arrêter le serveur
actuel avec Ctrl+C dans sa fenêtre Terminal. Ne pas faire tourner simultanément
deux versions sur le même dossier de données, même sur deux ports différents.

Aucun fichier de base n'est inclus dans le dépôt ou dans le ZIP de code.
Ne pas remplacer ni supprimer votre dossier `hub` existant dans le Finder.
Ne pas effacer `hub.sqlite`, `archive`, `photos`, `arrivee`, `rejets` ou `biblio`.

### Méthode ZIP, en conservant votre base habituelle au même endroit

1. Télécharger :
   https://github.com/Brooklynstar/Monolithe_Foeto_Stephanie/archive/refs/heads/test-integration.zip
2. Décompresser dans un **nouveau dossier de code**, par exemple
   `Monolithe_Stephanie_test`. Ne pas décompresser par-dessus votre installation actuelle.
3. Dans ce nouveau dossier, à côté de `serveur.command`, créer avec TextEdit
   un fichier **en texte brut** nommé exactement **base_locale.txt**.
   Il doit contenir sur une seule ligne le **chemin absolu du dossier hub actuel**,
   celui qui contient votre `hub.sqlite`. Exemple fictif à remplacer :

   ```text
   /Users/stephanie/Documents/Monolithe_Stephanie/hub
   ```

   Pour obtenir le chemin exact dans le Finder, sélectionner votre ancien
   dossier `hub`, puis **Option + Commande + C** et coller dans le fichier.
   Ne pas ajouter de guillemets ni mettre le chemin du fichier `hub.sqlite`
   lui-même. Ne pas utiliser le format RTF de TextEdit.
4. Double-cliquer **serveur.command** dans le **nouveau dossier de code**.
   Le programme utilise le code de test mais lit et enregistre dans votre
   **même base ordinaire existante**, sans la déplacer ni la copier.
   Si le chemin indiqué ne contient pas `hub.sqlite`, le lanceur refuse de
   continuer et ne crée pas une base vide de remplacement.
5. Le navigateur s'ouvre sur **http://127.0.0.1:5005/**. Vérifier dans **Ingestion**
   le chemin de base affiché et la présence de vos dossiers avant l'import du SLO.

`base_locale.txt` est un réglage local du lanceur ordinaire ; il est ignoré par
Git. Il ne contient ni dossier médical ni mot de passe. Une fois ce réglage fait,
les démarrages suivants se font par le même double-clic, sans commande Terminal.
Sans ce fichier, Monolithe utilise normalement le dossier `hub` de l'installation
lancée ; il ne peut pas deviner où se trouve votre ancienne installation.

Python **3.10 minimum** est nécessaire. Le lanceur prépare un environnement
Python local et installe les dépendances au premier lancement si nécessaire.
Internet sert au téléchargement initial des dépendances ; l'application reste
locale. Si les droits d'exécution sont perdus à la décompression, dépannage
ponctuel depuis le nouveau dossier de code :

```sh
chmod +x serveur.command hub/app/serveur.command
```

En cas de blocage macOS, utiliser les options d'ouverture autorisées par le
système. Un port 5005 occupé est signalé sans ouvrir le navigateur sur un autre
service. Laisser la fenêtre ouverte pendant l'utilisation, Ctrl+C pour arrêter.

### Si votre installation actuelle est déjà un clone Git

Après la sauvegarde et l'arrêt du serveur, conserver le même clone et le même
`hub`. Dans son dossier, une seule opération de récupération de code :

```sh
git status --short
git fetch origin
git switch --track origin/test-integration
```

Si une branche locale `test-integration` existe déjà, utiliser `git switch
test-integration` puis examiner son état avant toute mise à jour. Ne pas forcer
le changement de branche si Git signale des modifications locales ; ne pas
utiliser `reset --hard` ou `clean`. Les fichiers de données ignorés par Git
restent à leur place. Double-cliquer ensuite `serveur.command` comme d'habitude.
Le réglage `base_locale.txt` n'est pas nécessaire si ce clone utilise déjà son
propre `hub` comme base habituelle.

## Import initial du dossier SLO : un geste, une seule fois

**Si votre dossier SLO est déjà présent dans la base choisie, ouvrez-le
directement depuis la liste habituelle : aucun nouvel import nécessaire.**

Dans **Ingestion → Déposer des JSON**, choisir dans le nouveau code :

**hub/exemples/DEMO_SLO_001.json**

Le dépôt et la reprise habituels chargent ensemble les huit rubriques et les
deux comptes rendus déjà préparés. Le dossier apparaît à côté des autres :

**DEMO_SLO_001 — FICTIF – TEST – Smith-Lemli-Opitz**, opérateur **Codex**.

À partir de là : ouvrir le dossier depuis la liste générale, compléter ses
modules et cliquer **Enregistrer au hub**. Fermer puis relancer Monolithe
conserve les corrections. Aucun import n'est exécuté au démarrage.
Si vous sélectionnez de nouveau le même fichier, le dossier existant et ses
corrections ne sont pas remplacés.

Les comptes rendus initiaux sont disponibles par **Relire**. **Modifier**, puis
**Enregistrer une version**, conserve une correction et garde l'ancienne version.
La génération de nouveaux brouillons complet/synthèse reste le fonctionnement
habituel ; elle ne reprend pas automatiquement les corrections d'un ancien
brouillon. Les textes préparés restent disponibles dans l'historique.
**Exporter le dossier JSON** inclut les saisies courantes et les comptes rendus.
**Supprimer** sur la fiche retire le dossier de la base après confirmation de
son identifiant exact. Les archives restent conservées ; aucun redémarrage
ne le recrée. Vous seul décidez de cette suppression.

Le scénario et la conclusion sont entièrement fictifs. Le dossier permet de
tester les fonctions générales, les nouvelles rubriques pouvant être ajoutées
progressivement comme sur tout autre dossier. [Détails du dossier et des sources](DOSSIER_TEST_SLO.md).

## Essais des organes et du placenta dans le même dossier

Les percentiles des masses d'organes et les positions placentaires sont réunis
avec les biométries externes. Ouvrir les modules habituels, enregistrer au Hub,
puis générer un nouveau compte rendu complet ou une synthèse. Les anciens
comptes rendus enregistrés restent des versions historiques.

Le SLO source reste à **19 SA**, sans modification automatique des données.
À ce terme, l'absence de percentile placentaire Redline est attendue : les
seuils publiés exploités couvrent **22–42 SA**. Pour un essai placentaire positif,
utiliser un autre dossier fictif à **28 SA**, avec un placenta **frais émondé de
214 g** : position publiée **P50**. Ce résultat ne vient pas de la loi normale ;
aucun percentile exact n'est inventé entre les seuils publiés.

Réserve persistante pour les organes : **27 écarts de transcription historiques
Müller-Brochut** existent entre les tables de l'autopsie et du calculateur unifié.
Ils sont documentés et signalés ; aucune valeur de référence n'a été corrigée
sans validation médicale. Voir les bilans [organes](VALIDATION_PERCENTILES_MASSES_ORGANES.md)
et [placenta](VALIDATION_PERCENTILES_PLACENTA.md).

## Vérifications techniques réalisées

- `dossier_demonstration` créée directement depuis `main` ; sources initiales
  et deux comptes rendus récupérés avant retrait de l'ancien dispositif.
- Ancien serveur de démonstration, lanceurs dédiés, base séparée et conditions
  spécifiques au numéro SLO retirés de `percentiles_biometries_externes`.
- Intégration des cinq branches par des commits de fusion dans `test-integration`
  uniquement. `main`, `raccourcis_lancement`, les branches de référence et les
  versions stables ne sont pas modifiées.
- **37 tests réussis** dans la version intégrée : dossier ordinaire, calculs,
  Python/JavaScript, tableaux/JSON/comptes rendus, lanceurs et test de redémarrage.
- Vrai processus du serveur ordinaire sur **127.0.0.1:5005** : base habituelle de
  test initialement vide, import par l'API normale de dépôt/reprise, correction
  administrative, génération d'un CR avec percentiles, arrêt puis relance sur
  la même base. Dossier, correction et CR conservés ; nouvel import ignoré.
- Parcours Chromium dans l'interface normale : import unique, correction puis
  enregistrement de chacune des huit rubriques, CR modifié et relu après
  rechargement, génération complet/synthèse, export téléchargé, suppression
  confirmée par l'interface et maintien du dossier témoin fictif.
- **76 contrôles de comptes rendus réussis**, 2 001 points Python/JavaScript,
  128 calculs protégeant les anciens Z-scores/alertes et autotests des modules réussis.
- Organes : 136 cas autopsie et 222 cas neuropathologie Python/JavaScript ;
  placenta : 918 cas Python/JavaScript/calculateur unifié.
- Parcours SLO combiné dans une base temporaire : huit rubriques, masses à P50,
  placenta hors limites à 19 SA, essai placenta à 28 SA, trois comptes rendus,
  export JSON et conservation après réouverture. La source SLO reste inchangée.
- Lanceurs macOS : syntaxe Bash, exécution dans un chemin avec espaces/accents,
  erreurs propagées, base existante sélectionnée par `base_locale.txt`, fichier
  témoin inchangé, chemin inexistant refusé sans création de répertoire.
- Tables de référence inchangées. Aucune base clinique réelle utilisée dans les tests.

Les tests ont tourné sous Linux/Chromium. Restent à vérifier sur votre Mac :
Finder, autorisations, Python installé localement, Safari/Chrome, Cambria réelle,
impression et copier-coller Word. Les scripts Windows conservent le lancement
local mais n'ont pas été exécutés dans un Windows natif. Le jeu fictif ne
remplace pas une validation médicale humaine ou des tests exhaustifs de
fonctionnalités futures. Aucun résultat de diagnostic réel n'est affirmé.

## Retour au code précédent

Arrêter le serveur de test, puis relancer l'ancien code ou revenir à son ancienne
branche dans le clone Git. La base habituelle reste au même emplacement et cette
étape n'ajoute aucune migration de schéma. Les corrections explicitement faites
et le dossier fictif restent dans cette base. Pour récupérer un état antérieur
des données, utiliser la sauvegarde initiale après arrêt du serveur, en conservant
également une copie de l'état courant ; ne pas écraser une base ouverte.
