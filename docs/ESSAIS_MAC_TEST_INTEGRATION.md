# Monolithe Stéphanie — version test-integration sur Mac

Cette branche réunit `dossier_demonstration`, `percentiles_biometries_externes`
et `raccourcis_lancement`. Elle utilise **le serveur ordinaire**, exclusivement
sur `127.0.0.1`, avec **5005** comme port par défaut. Aucun hébergement distant,
aucun serveur ou écran réservé au dossier fictif, aucune base de démonstration.
Le port 5005 reste le défaut de la branche indépendante `raccourcis_lancement`.

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

## Vérifications techniques réalisées

- `dossier_demonstration` créée directement depuis `main` ; sources initiales
  et deux comptes rendus récupérés avant retrait de l'ancien dispositif.
- Ancien serveur de démonstration, lanceurs dédiés, base séparée et conditions
  spécifiques au numéro SLO retirés de `percentiles_biometries_externes`.
- Intégration des trois branches par des commits de fusion dans `test-integration`
  uniquement. `main`, `raccourcis_lancement`, les branches de référence et les
  versions stables ne sont pas modifiées.
- **25 tests réussis** dans la version intégrée : dossier ordinaire, calculs,
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
  128 calculs de masses d'organes inchangés et autotests des modules réussis.
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
