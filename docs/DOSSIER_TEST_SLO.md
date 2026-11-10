# Dossier fictif permanent — Smith-Lemli-Opitz

Branche `dossier_demonstration`, créée directement depuis `main`
`a3cc4b914e6b95549ef5939d0fe8b4645dae357e`.

## Importer une seule fois dans le Hub habituel

1. Lancer Monolithe avec son serveur habituel et sa base habituelle.
2. Dans **Ingestion**, cliquer **Déposer des JSON** (ou déposer le fichier dans
   la zone de dépôt), puis sélectionner **hub/exemples/DEMO_SLO_001.json**.
3. La reprise habituelle importe le dossier complet. Ouvrir **DEMO_SLO_001**
   dans la liste générale : **FICTIF – TEST – Smith-Lemli-Opitz**.

Le titre apparaît dans l'indication et les remarques. L'opérateur des saisies
et des comptes rendus initiaux est **Codex**. Les huit rubriques et les deux
comptes rendus préparés sont repris ensemble. Aucun script de démonstration,
aucun serveur particulier, aucune base séparée, aucun bandeau spécifique.
Aucun fichier n'est importé au démarrage : vous choisissez explicitement ce
fichier une seule fois. Un nouvel import du même identifiant est ignoré sans
écraser les corrections ni rendre courantes les anciennes saisies.

Chaque rubrique se consulte depuis la fiche et se corrige dans son module
normal. Utiliser **Enregistrer au hub**, puis revenir au dossier. Les saisies
sont conservées dans la base ordinaire après fermeture et réouverture.
Renseigner vos initiales en haut du Hub pour les nouvelles corrections ; les
saisies fictives initiales restent attribuées à Codex.

Dans **Compte rendu**, les deux textes déjà préparés sont accessibles par
**Relire**. **Modifier** permet une correction dans le texte affiché, puis
**Enregistrer une version** enregistre la correction et conserve la version
précédente dans l'historique. **Annuler** abandonne l'édition en cours.
La génération habituelle d'un nouveau brouillon reste disponible. Un nouveau
brouillon est distinct des corrections manuelles déjà enregistrées : il ne
fusionne pas automatiquement ces corrections dans le texte régénéré.
Les comptes rendus initiaux contiennent une conclusion rédigée distinguant les
constatations fictives de l'hypothèse diagnostique. Elle reste librement modifiable.

**Exporter le dossier JSON** exporte toutes les saisies courantes, leurs clichés
archivés éventuels et les comptes rendus, y compris les versions corrigées.
Le fichier exporté est réimportable par la même ingestion dans une installation
ne contenant pas déjà cet identifiant. Pour retirer le dossier de votre liste,
utiliser **Supprimer** sur sa fiche et confirmer son identifiant exact.
La suppression retire les saisies et comptes rendus de la base ; les fichiers
d'archive restent conservés. Un redémarrage ne recrée pas le dossier. Une reprise
manuelle complète des anciennes archives peut en revanche le restaurer.

## Données et récupération du travail précédent

- Identifiant permanent : `DEMO_SLO_001`.
- Scénario entièrement fictif : fœtus masculin de 19 SA, petit poids,
  microcéphalie, syndactylie cutanée bilatérale 2–3 des pieds et sous-virilisation.
- Confirmation de Smith-Lemli-Opitz non réalisée : le compte rendu distingue
  la morphologie de l'hypothèse et mentionne les stérols et DHCR7.
- Les huit fichiers sources initiaux sont conservés **octet pour octet** sous
  `hub/exemples/DEMO_SLO_001/sources_initiales/`.
- Les deux comptes rendus précédemment préparés sont conservés sous
  `comptes_rendus/`, avec leurs versions et leur texte d'origine. Il s'agit
  d'instantanés historiques : leurs mentions de démonstration et percentiles
  déjà calculés sont conservées. Ils ne prouvent pas qu'un moteur de percentile
  est installé dans la branche `dossier_demonstration` seule.
- Les rubriques importables se trouvent sous `modules/`, réexportées dans les
  formats des formulaires natifs : codes HPO reconnus, identifiants de champs
  et d'organes de microscopie, sections placentaires actuelles. Les précisions
  cliniques 2–3 des pieds sont conservées ; le libellé de puce natif est Syndactylie.
- `provenance.json` donne le commit source `672adfe` et les empreintes des sources
  et comptes rendus conservés. Le fichier complet est reproductible par
  `python3 hub/outils/preparer_dossier_slo.py`, qui ne lit ni ne modifie aucune base.

Cette branche ne reprend ni le moteur de percentiles, ni les scripts de
lancement de l'autre développement, ni le port 5006. Ces fonctions sont réunies
uniquement dans `test-integration`. Les données de référence sont inchangées.

## Adaptations minimales du fonctionnement ordinaire

Le dépôt acceptait les JSON de modules en sélection multiple mais pas les
comptes rendus dans un même import. Le format JSON `monolithe_dossier`, version 1,
ajoute cette possibilité à **la même chaîne de dépôt et d'ingestion**, en
réutilisant les adaptateurs de chaque module et l'archivage existants.
Les saisies sont validées avant écriture, puis importées dans une transaction.
Un identifiant déjà présent n'est jamais écrasé par cet import complet.
L'import individuel des modules continue à fonctionner comme avant.

Le Hub ne proposait pas de correction enregistrée d'un CR ni de suppression
sur la fiche. Ces deux actions génériques sont maintenant disponibles pour
les dossiers ordinaires ; aucune condition spéciale `DEMO_SLO_001` dans leur
code. L'édition conserve les versions précédentes. Le HTML importé ou corrigé
est limité au texte et à la mise en forme usuelle, sans scripts, événements ni
ressources actives. Les photos restent dans les rubriques du dossier.
La sélection de fichiers préserve aussi la liste avant remise à zéro du champ,
pour permettre l'import dans un véritable navigateur. La rubrique `micro` est
reconnue comme `microscopie` lors du calcul des modules manquants d'un CR.

## Vérifications sur cette branche

- **6 tests Python/Chromium réussis** : import par dépôt ordinaire, huit rubriques,
  idempotence après correction, persistance sur nouvelles connexions et application,
  CR corrigés historisés et export/réimport, suppression confirmée et absence de
  recréation, rejet atomique d'un paquet incohérent, nettoyage HTML.
- Parcours Chromium : sélection du JSON dans l'interface, consultation puis
  **correction et enregistrement dans chacun des huit modules**, relecture d'une
  mesure, modification enregistrée d'un CR, relecture après rechargement,
  génération du complet et de la synthèse, téléchargement de l'export complet,
  suppression depuis la fiche et contrôle du maintien d'un dossier témoin fictif.
- Les sources initiales ont été comparées octet pour octet au commit `672adfe`.
  Les empreintes de conservation et la reconstruction du fichier importable
  sont vérifiées automatiquement.
- **75 contrôles des comptes rendus existants réussis** sur cette branche issue
  de main (le contrôle biométrique enrichi est porté par l'autre branche).
- Un autre dossier entièrement fictif sert de sentinelle : son contenu reste
  identique pendant l'import, les corrections et la suppression du dossier SLO.
- Aucun test n'a utilisé une base clinique réelle. Aucune table de référence modifiée.

Les tests automatisés tournent sous Linux avec Chromium. Les vérifications
Finder, Safari, Cambria réelle, impression et copier-coller Word restent à
faire sur Mac. Le scénario reste pédagogique, sans validation clinique humaine.
