# Conditions de mise en production — bloquantes

Ce premier incrément est destiné au développement et à la validation fonctionnelle. L’autorisation `RELEASE_REVIEW_APPROVED=true` ne doit être donnée qu’après une revue documentée de tous les points applicables ci-dessous ; elle n’est pas une certification légale.

## Réglementation

Établir avec des experts comptables/juridiques marocains la matrice des obligations par module, type d’entreprise et période. Acquérir les textes officiels originaux, leur preuve de publication, dates, portée, modifications et dispositions transitoires. L’annuaire des sites n’est pas une preuve de complétude. Une importation manuelle de texte peut être altérée : la revue doit comparer avec l’original officiel. Séparer vérification documentaire et interprétation métier.

Toute règle exécutable doit porter une référence officielle, une version, les dates d’applicabilité, les conditions/exceptions et des tests approuvés. Une règle absente ou contestée bloque l’opération sensible. Un dossier ne peut pas afficher « 100 % conforme » à partir d’une réponse de modèle ou d’un annuaire de liens.

Examiner le traitement des données, les formalités applicables, les sous-traitants, transferts et hébergement. Aucune donnée de dossier n’est envoyée à un fournisseur externe dans cet incrément. L’hébergement au Maroc n’exonère pas à lui seul des autres obligations.

## Sécurité et exploitation

MFA, récupération/révocation, durcissement de la passerelle et anti-abus distribué, séparation des rôles SQL et RLS, chiffrement, clés et rotation, sauvegardes/restauration, protection et rétention des audits, observabilité, alertes de file bloquée et supervision antivirus. Utiliser un rôle SQL applicatif non propriétaire distinct du rôle de migration en production.

Les déclencheurs interdisent les modifications des audits par les opérations ordinaires ; ils ne résistent pas seuls à un administrateur de base. Les fichiers locaux et volumes Docker ne sont pas un archivage légal certifié.

L’outbox réémet les tâches en cas de panne. Les accès sont relus avant leur exécution. Les tâches annulées après retrait d’affectation devront être reprises par un acteur autorisé via un futur workflow explicite, jamais réactivées silencieusement.

Passer les tests PostgreSQL, isolation, navigateur et charges. Geler les dépendances et images, examiner les avis officiels des éditeurs et les audits de dépendances, corriger les failles avant exposition publique. Les versions Node/Python ou les images « stable » de développement ne constituent pas une politique de patch.

## Source officielle et sécurité d’ingestion

Annuaire initial : SGG, DGI, ministère des Finances/CNC, CNDP, Office des Changes et CNSS. Seuls les domaines HTTPS exacts sont acceptés pour les références ; le serveur ne télécharge pas d’URL utilisateur, ce qui évite d’introduire une récupération réseau arbitraire. La collecte réseau future doit gérer redirections autorisées, contenu malveillant, taille et hash.

Le corpus public pourra être distribué centralement après une procédure éditoriale distincte. Dans cet incrément, les sources de l’annuaire sont partagées, mais les textes soumis et revus restent cloisonnés par cabinet. Aucun document de dossier ne peut être promu automatiquement dans un corpus commun.
