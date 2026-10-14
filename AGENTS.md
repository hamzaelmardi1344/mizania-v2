# Mizania V2 — contraintes permanentes

- Produit centré sur le dossier client, dans un cabinet. Un utilisateur ne voit que ses affectations actives ; aucun rôle métier ne contourne implicitement cette affectation.
- Modèle B : espace cabinet et portail client distincts. Le client voit ses propres dépôts et les contenus explicitement autorisés/publiés ; jamais les notes internes, écritures de travail ou documents internes non partagés.
- Conserver le design validé du dépôt Mizania : sidebar marine, fond clair, accents indigo/violet, typographies, espacements et composants existants. Adapter les parcours, ne pas redessiner le produit.
- Les traitements intelligents sont exclusivement en arrière-plan. Aucun terme IA, agent, modèle, prompt, assistant IA ou score de modèle dans les interfaces métier. Les obligations légales d'information restent à respecter.
- Conserver la base de connaissances réglementaire marocaine : sources officielles, provenance, versions, dates d'effet, validations, preuves et règles exécutables séparées du corpus documentaire.
- Aucune règle fiscale inventée. Une source répertoriée n'est pas une règle validée. En cas d'absence de règle applicable validée, bloquer la finalisation sensible et expliquer la pièce ou décision manquante.
- Contrôler cabinet, dossier et permission côté serveur sur chaque lecture, écriture, export, recherche, fichier et traitement asynchrone. Ne jamais considérer le dossierId fourni comme une autorisation.
- Sessions révocables ; aucun secret ni document client dans Git. Aucune copie des .env ni de l'historique contenant des secrets de l'ancien dépôt.
- Distinguer un document reçu, un résultat préparé, une validation métier et une publication client. Aucun envoi fiscal, paiement ou effet externe sans workflow et autorisation explicites.
- Tests d'isolation et de révocation obligatoires. Ne pas annoncer une conformité juridique absolue sans validation experte et périmètre documenté.
- Documenter honnêtement ce qui fonctionne, ce qui est en construction et ce qui bloque une mise en production.

## Reprise du développement

Lire intégralement `docs/CODEX_PROMPT.txt`, `docs/CODEX_HANDOFF.md`, `STATUS.md`, `docs/DESIGN.md`, `docs/RELEASE-GATES.md` et `README.md` avant les modifications. Le prompt définit la cible, le handoff décrit le socle observé ; contrôler le code courant avant d'en déduire un avancement.

L'objectif est le périmètre complet discuté, pas des menus de démonstration. Maintenir `docs/IMPLEMENTATION_MATRIX.md` avec cas métier, permissions, règles, preuves de code, écrans et tests. Construire des parcours verticaux réellement raccordés au backend.

Les reprises interrompues n'ont pas livré le moteur métier comptable. Ne pas supposer l'existence de `backend/app/business/models.py` ou considérer le nom de la branche `work/business-foundation` comme une preuve. Vérifier le checkout réel.

Ne pas écraser des changements locaux, réinitialiser des données, contourner des validations ou forcer un push. Tests destructifs PostgreSQL exclusivement sur base jetable. Pas de donnée financière fictive dans les écrans hors environnement de test.
