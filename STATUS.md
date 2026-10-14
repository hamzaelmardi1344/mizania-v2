# État de réalisation — incrément 1

## Livré dans le code

- Authentification réelle, sessions en base, connexion côté serveur avant affichage des dossiers, sortie de session.
- Dossiers et exercices, affectations actives, habilitations manager/reviewer/collaborator/client et contrôles API.
- Portail client distinct, invitation à usage unique et expiration, échanges avec réponses et clôture.
- Documents persistants, quarantaine, contrôles serveur, accès limité, partage explicite et historique.
- Outbox persistante, distribution asynchrone, relecture des habilitations, analyse ClamAV et reprise sur indisponibilité.
- Annuaire officiel, versions de textes, SHA-256, dates, revue documentaire à deux personnes et séparation des cabinets.
- Navigation métier sans exposition des mécanismes intelligents.
- 35 tests backend réussis localement sur SQLite au moment de l’implémentation. PostgreSQL et navigateur sont configurés dans CI et ne doivent être déclarés validés qu’après leur exécution réelle.

## Non livré / non certifié

- Production comptable complète, règles fiscales exécutables, télétransmissions, paiement ou intégration bancaire.
- OCR, extraction structurée et imputation : aucun faux résultat ne remplace ces fonctions.
- Collecte automatique exhaustive des textes officiels, archivage des PDF originaux, consolidation et veille réglementaire.
- Moteur d’applicabilité juridique, règles exécutables expertisées, jeux de tests réglementaires et audit légal.
- Supervision globale multi-dossiers, gestion avancée du portefeuille, clôture/archivage des dossiers, portail financier publié.
- MFA, récupération sécurisée de compte, gestion complète des invitations/relances, e-mail transactionnel.
- RLS PostgreSQL, stockage objet chiffré/WORM, audit externe, sauvegardes et restauration testées, monitoring production.
- Équivalence pixel par pixel de chaque ancien écran : primitives conservées ; les nouveaux parcours nécessitent une revue visuelle.

## Ordre de travail suivant

1. Revue navigateur et renforcement du socle (MFA, fin du cycle de vie des accès, stockage et exploitation).
2. Acquisition et validation du corpus officiel marocain, moteur de règles versionné et tests d’applicabilité.
3. Documents structurés et workflow achats/comptabilité de bout en bout, avec écritures contrôlées.
4. Banques/rapprochement/trésorerie ; fiscalité ; révision et reporting.

Ne pas changer ce fichier en « terminé » sur la seule base de menus ou d’écrans de présentation.
