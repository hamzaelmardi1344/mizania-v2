# État de réalisation — incrément 1

## Livré dans le code

- Authentification réelle, sessions en base, connexion côté serveur avant affichage des dossiers, sortie de session.
- Dossiers et exercices, affectations actives, habilitations manager/reviewer/collaborator/client et contrôles API.
- Portail client distinct, invitation à usage unique et expiration, échanges avec réponses et clôture.
- Documents persistants, quarantaine, contrôles serveur, accès limité, partage explicite et historique.
- Outbox persistante, distribution asynchrone, relecture des habilitations, adaptateur ClamAV et reprise sur indisponibilité.
- Annuaire officiel, versions de textes, SHA-256, dates, revue documentaire à deux personnes et séparation des cabinets.
- Navigation métier sans exposition des mécanismes intelligents.

## Vérification effectuée le 14 octobre 2026

Commit applicatif vérifié : `13fc9e02b340b2712c4a7c00ebd832b7391c35fb`.

[Exécution GitHub Actions terminée avec succès](https://github.com/hamzaelmardi1344/mizania-v2/actions/runs/38596148242).

| Vérification | Résultat observé |
| --- | --- |
| Backend SQLite | 35 tests réussis localement ; job CI réussi |
| Backend PostgreSQL | 35 tests, 0 erreur, 0 échec, 0 ignoré dans le rapport JUnit CI |
| TypeScript | `tsc --noEmit` réussi |
| Frontend | Build Next.js réussi |
| Parcours navigateur Chromium | 4 tests réussis : protection avant connexion, affectations collaborateur, dépôt client persistant et refus des accès internes, référentiel visible |
| Audit des dépendances frontend | Job réussi, aucun problème signalé par npm audit à cette exécution |

Les captures de l’accueil dossier, du portail client et du référentiel ont été récupérées et inspectées. Elles sont disponibles dans l’artefact `web-verification` de cette exécution. Il s’agit de données de test synthétiques, pas de dossiers réels.

Ces résultats ne valent ni certification de conformité réglementaire, ni audit de sécurité exhaustif. L’analyse antivirus est simulée dans les tests unitaires : le fonctionnement du service ClamAV réel et de l’ensemble Docker Compose doit encore être vérifié dans son environnement de déploiement. Les versions de dépendances résolues sont conservées dans le lockfile de l’artefact CI ; leur gel dans le dépôt reste à effectuer.

## Non livré / non certifié

- Production comptable complète, règles fiscales exécutables, télétransmissions, paiement ou intégration bancaire.
- OCR, extraction structurée et imputation : aucun faux résultat ne remplace ces fonctions.
- Collecte automatique exhaustive des textes officiels, archivage des PDF originaux, consolidation et veille réglementaire.
- Moteur d’applicabilité juridique, règles exécutables expertisées, jeux de tests réglementaires et audit légal.
- Supervision globale multi-dossiers, gestion avancée du portefeuille, clôture/archivage des dossiers, portail financier publié.
- MFA, récupération sécurisée de compte, gestion complète des invitations/relances, e-mail transactionnel.
- RLS PostgreSQL, stockage objet chiffré/WORM, audit externe, sauvegardes et restauration testées, monitoring production.
- Équivalence pixel par pixel de chaque ancien écran : primitives conservées ; validation finale des nouveaux parcours avec l’utilisateur encore nécessaire.

## Ordre de travail suivant

1. Renforcement du socle : MFA, cycle de vie des accès, gel des dépendances, validation de Compose et ClamAV, stockage et exploitation.
2. Acquisition et validation du corpus officiel marocain, moteur de règles versionné et tests d’applicabilité.
3. Documents structurés et workflow achats/comptabilité de bout en bout, avec écritures contrôlées.
4. Banques/rapprochement/trésorerie ; fiscalité ; révision et reporting.

Ne pas changer ce fichier en « terminé » sur la seule base de menus ou d’écrans de présentation.
