# **AGENTS.md — Monolithe Bordeaux**

## **1. Environnement de travail**

- Travailler exclusivement sur la branche `monolithe-bordeaux`, sauf autorisation explicite.
- Vérifier la branche active, le répertoire de travail et l’état des modifications locales avant toute intervention.
- Ne jamais modifier la branche `main`.
- Ne jamais modifier directement le dépôt de Rémi Mathevet.
- Ne pas créer de branche, de copie du projet ou de worktree supplémentaire sans nécessité justifiée.
- Préserver systématiquement les modifications déjà réalisées.

## **2. Fonctionnement de Monolithe**

- Maintenir un fonctionnement exclusivement local, hors cloud.
- Garantir la compatibilité avec macOS et Windows.
- Utiliser le port 5005 comme port de référence.
- Préserver les raccourcis de lancement habituels.
- Garantir que le lancement depuis le Finder restitue la dernière version développée.
- Ne pas rendre le fonctionnement de Monolithe dépendant de VS Code ou de Codex.
- Arrêter les serveurs temporaires après les tests.

## **3. Méthodologie de développement**

- Examiner l’architecture existante avant toute modification.
- Réutiliser autant que possible les fonctionnalités et structures déjà présentes.
- Éviter les duplications de code et les solutions provisoires inutiles.
- Anticiper les conséquences de chaque modification sur l’ensemble de l’application.
- Rechercher la cause réelle d’un dysfonctionnement plutôt que d’en corriger uniquement les symptômes.
- Ne pas supprimer ou modifier une fonctionnalité existante sans justification.
- Privilégier les solutions pérennes, simples et maintenables.

## **4. Cohérence médicale**

- Respecter rigoureusement la terminologie médicale et anatomopathologique.
- Ne jamais modifier de sa propre initiative une donnée médicale, une classification, une formule biométrique ou une référence scientifique.
- Préserver la concordance entre les données saisies, les fichiers JSON, les conclusions et les comptes rendus générés.
- Ne jamais inventer de données médicales manquantes.
- Respecter les conventions de présentation des comptes rendus médicaux.

## **5. Validation des développements**

- Tester systématiquement les fonctionnalités modifiées.
- Vérifier l’absence de régression sur les fonctionnalités existantes.
- Tester l’ensemble du circuit des données, de la saisie jusqu’à la génération du compte rendu, lorsque la modification le concerne.
- Vérifier que les données sont correctement enregistrées, restaurées et exportées.
- Vérifier que le raccourci habituel lance effectivement la dernière version de Monolithe.
- Ne jamais considérer une tâche comme terminée sur la seule base d’une modification du code.
- Signaler explicitement les vérifications qui n’ont pas pu être réalisées.

## **6. Confidentialité et sécurité**

- Ne jamais transférer de données médicales vers un service externe ou un espace cloud.
- Utiliser exclusivement des dossiers fictifs pour les tests.
- Ne jamais inclure de données patients, de mots de passe ou de clés API dans GitHub.
- Ne pas accorder ou solliciter d’autorisations système étendues lorsqu’une solution moins intrusive existe.

## **7. Gestion de Git et GitHub**

- Utiliser Git et GitHub CLI (`gh`), déjà installés et configurés sur le Mac.
- Consulter l’historique Git pour retrouver les anciennes implémentations sans changer de branche ni restaurer d’ancienne version.
- Privilégier `git fetch` pour consulter les évolutions distantes sans modifier les fichiers de travail.
- Ne jamais effectuer de `git pull` sans autorisation explicite.
- Ne jamais écraser les modifications locales.
- Ne jamais effectuer de réinitialisation destructive.
- Ne jamais effectuer de commit, de push, de fusion ou de pull request sans autorisation explicite.
- Lors d’une synchronisation avec le dépôt de Rémi, préserver les développements propres à Monolithe Bordeaux.
- Analyser les conflits et les risques de régression avant toute intégration.

## **8. Autonomie et communication**

- Réaliser les opérations techniques autorisées de manière autonome, jusqu’à leur validation.
- Éviter de solliciter inutilement l’utilisatrice pour des opérations techniques courantes.
- Expliquer brièvement les choix techniques et leurs conséquences.
- Signaler les risques avant toute opération potentiellement destructive.
- Anticiper les difficultés susceptibles de survenir lors de l’utilisation réelle de Monolithe.
- En fin de tâche, préciser les modifications réalisées, les tests effectués et les éventuelles limitations restantes.

## **9. Amélioration continue**

- Lorsqu’un dysfonctionnement révèle une insuffisance dans les procédures de développement, proposer une nouvelle règle permettant d’éviter sa répétition.
- Ne pas modifier les règles du présent fichier sans validation de l’utilisatrice.
- Prendre systématiquement connaissance de ces instructions au début de chaque nouvelle session de travail.
