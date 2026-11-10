# Lancement local — bilan du 10 novembre 2026

Branche créée directement depuis `main` a3cc4b914e6b95549ef5939d0fe8b4645dae357e.
Aucune modification des fichiers médicaux, des tables ou des exports.

## Utilisation

macOS : double-cliquer `serveur.command` à la racine du dépôt.
Python 3.10 minimum doit être installé. Le lanceur prépare `hub/app/.venv`,
installe Flask et Pillow si nécessaire, puis ouvre le navigateur après réservation
du port. Internet est nécessaire au premier téléchargement des dépendances,
pas pour utiliser le programme ensuite. Si macOS bloque le fichier téléchargé,
utiliser les options d'ouverture autorisées par le système ; vérifier aussi que
les deux fichiers .command ont conservé leur droit d'exécution après extraction.

Windows : double-cliquer `serveur.bat` à la racine du dépôt.
Détection du Python portable existant, du lanceur `py -3`, puis de `python`.
Python 3.10 minimum ; Flask et Pillow installés si absents, depuis les roues
locales si disponibles, sinon via Internet. L'installation utilise le Python
sélectionné, comme le lanceur Windows historique. Le deuxième argument
historique de délai n'est plus utilisé : l'ouverture attend le serveur.

Les deux lanceurs utilisent `http://127.0.0.1:5005/`, sans hébergement distant.
Laisser la fenêtre ouverte ; Ctrl+C arrête le serveur. Si le port est occupé,
l'erreur est affichée et aucun navigateur n'est ouvert sur un autre service.
Les données restent dans le dossier `hub` du dépôt lancé. Le fonctionnement
normal du serveur conserve ses mécanismes d'initialisation/migration de base ;
aucune réécriture de dossier médical n'a été ajoutée par ces lanceurs.

## Fichiers

- .gitignore : exclut l'environnement virtuel local.
- serveur.command : point d'entrée Finder, exécutable.
- serveur.bat : point d'entrée Windows.
- hub/app/serveur.command : détection Python, environnement et dépendances.
- hub/app/serveur.bat : dépendances, détection Python et ouverture après écoute.
- hub/app/serveur.py : option `--ouvrir-navigateur`, réservation avant ouverture.
- hub/app/requirements.txt : dépendances du lanceur.
- tests/test_lancement.py : essais isolés.
- docs/VALIDATION_RACCOURCIS_LANCEMENT.md : ce bilan.

## Comparaison aux branches existantes

Le lanceur macOS, les dépendances et l'option d'ouverture du navigateur sont
repris sélectivement de `percentiles_biometries` 447ab7314df29b536bdbc9708a16af3f78078378.
Le port demeure celui de main, 5005, également dans la version de test intégrée. Le lanceur Windows historique est adapté pour détecter aussi Pillow,
contrôler Python et ouvrir le navigateur seulement après réservation du port.

## Tests exécutés sous Linux

- `bash -n serveur.command hub/app/serveur.command` : réussi.
- `python -m unittest discover -s tests -v` : 4 tests réussis.
- Serveur réel : écoute par défaut sur 127.0.0.1:5005, réponse HTTP de l'interface
  et de `/api/etat`, dossier de données attendu.
- Port occupé : échec signalé, aucun appel au navigateur, serveur initial intact.
- Port dynamique : URL réelle transmise au navigateur après écoute.
- Options incompatibles : refus avant initialisation des données.
- Lanceur Bash réellement exécuté depuis /tmp dans un chemin avec espaces et
  accent, avec interpréteur simulé : arguments corrects et erreur propagée.
- Seul l'appel de navigateur des tests serveur est remplacé par une sonde TCP
  enregistrant l'URL. Les bases sont jetables et isolées des données existantes.
- `git -c core.whitespace=cr-at-eol diff --check` : réussi (fichiers .bat CRLF). Aucun fichier médical ne figure dans le diff.

## Vérifications nécessaires sur de vrais postes

macOS : double-clic Finder Intel et Apple Silicon, Python python.org/Homebrew,
création initiale du venv, installation en ligne puis redémarrage hors ligne,
Cambria/interface dans le navigateur choisi, autorisations macOS, droits des
.command après téléchargement ZIP, fermeture et relance du programme.

Windows : exécution native .bat non disponible ici. Vérifier Windows 10/11,
Python portable et py/python, chemins avec espaces et accents, installation
par roues et par réseau, absence de Pillow, erreurs Python/dépendances,
port occupé, navigateur par défaut, arrêt/reprise et données existantes.
L'ouverture réelle du navigateur système reste à confirmer sur ces deux OS.

Conserver toutes les branches existantes. `percentiles_biometries` et `port_5006`
pourront être réévaluées pour suppression après validation complète explicite ;
aucune suppression, fusion ou création de `stephanie_stable` à cette étape.
