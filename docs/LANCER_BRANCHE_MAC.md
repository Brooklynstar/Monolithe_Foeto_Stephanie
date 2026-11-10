# Lancer test-integration sur Mac

Cette version réunit le dossier fictif SLO, les biométries externes, les masses
d'organes, le placenta et les raccourcis de lancement.

1. Sauvegarder les données depuis Monolithe, puis arrêter le serveur avec Ctrl+C.
2. Télécharger le ZIP de **test-integration**, puis le décompresser dans un nouveau
   dossier sans remplacer votre installation actuelle.
3. Copier votre `base_locale.txt` à côté du nouveau `serveur.command` : il doit
   désigner le dossier `hub` habituel qui contient `hub.sqlite`.
4. Double-cliquer **serveur.command** : ouverture sur **http://127.0.0.1:5005/**.
5. Ouvrir **DEMO_SLO_001** depuis la liste habituelle. S'il est déjà présent,
   ne pas le réimporter. Sinon, l'import initial ordinaire est décrit dans le guide.

Sans `base_locale.txt`, le lanceur utilise le `hub` de la nouvelle installation,
qui peut être vide. Arrêter le serveur et corriger ce réglage si les dossiers
habituels n'apparaissent pas. Ne pas lancer deux versions sur la même base.

[Guide détaillé : téléchargement, sauvegarde, import initial et limites des essais](ESSAIS_MAC_TEST_INTEGRATION.md).

Python 3.10 minimum est nécessaire. Le double-clic Finder, les autorisations
macOS, Cambria et l'impression restent à vérifier sur un vrai Mac.
