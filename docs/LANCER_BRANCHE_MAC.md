# Lancer la branche Placenta sur Mac

1. Arrêter le Monolithe déjà ouvert : Ctrl+C dans sa fenêtre Terminal.
2. Télécharger le ZIP de cette branche et le décompresser dans son propre dossier,
   sans remplacer le dossier de votre installation habituelle.
3. Pour retrouver votre base habituelle, copier votre `base_locale.txt` à côté
   de `serveur.command`. Il doit contenir le chemin absolu du dossier `hub`
   existant, celui qui contient `hub.sqlite`. Ne pas déplacer ni écraser la base.
4. Double-cliquer **serveur.command**. L'interface s'ouvre sur
   **http://127.0.0.1:5005/**.

Python 3.10 minimum est nécessaire ; les dépendances sont installées au premier
lancement si besoin. Le serveur reste local. Sans `base_locale.txt`, il utilise
le dossier `hub` de la copie lancée et peut donc afficher une base vide.
Si votre base est vide de manière inattendue, arrêter et vérifier ce fichier.

Pour passer à l'autre branche : Ctrl+C, puis ouvrir son propre `serveur.command`.
Ne pas lancer les deux à la fois : toutes deux utilisent 5005. Un port occupé
est signalé sans ouvrir une autre application dans le navigateur.

Les fonctionnalités du dossier fictif et des raccourcis de test-integration
ne sont pas fusionnées ici : seule la partie lancement nécessaire est reprise.
Les dossiers déjà enregistrés dans la base choisie restent accessibles selon
les fonctions de main et de cette branche.

Si macOS signale une absence de permission d'exécution après extraction, depuis
le dossier décompressé :

```sh
chmod +x serveur.command hub/app/serveur.command
```

Les essais automatisés sont réalisés sous Linux/Bash ; le véritable double-clic
Finder et les autorisations macOS restent à confirmer sur votre Mac.
