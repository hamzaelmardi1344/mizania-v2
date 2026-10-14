# Relais de développement — Mizania V2

Ce document décrit l'état observé lors du transfert à Codex. La cible complète est dans `docs/CODEX_PROMPT.txt`. Ne pas confondre cible, code existant et preuves de tests.

## 1. Historique vérifié et reprise des interruptions

- Socle applicatif : `13fc9e02b340b2712c4a7c00ebd832b7391c35fb`.
- État documenté sur main avant ce relais : `35797498ed718aa6af81ef8eea41dbc0231342ee`.
- Branche de travail créée : `work/business-foundation`, tête vérifiée `f0b10a4472d6123bc1a3ff95484d3b412295b943`.
- Les deux commits supplémentaires de cette branche ajoutent uniquement `.github/workflows/business.yml` et `.github/workflows/toolchain.yml`. Le nom de la branche et du workflow ne prouve pas l'existence d'un moteur comptable.
- Une ébauche de modèles métier a été proposée pendant une reprise interrompue, mais son écriture n'a pas abouti. Aucun fichier `backend/app/business/models.py` correspondant n'a été constaté dans les sources locales inspectées. Ne pas considérer cette ébauche comme une implémentation ou une migration livrée.
- La sauvegarde de relais conserve les commits précédents et ajoute les instructions de reprise. Aucun module métier supplémentaire n'est déclaré finalisé par cette opération de sauvegarde.

Point d'entrée utilisateur : main après la sauvegarde de relais. Lire `git log` et `git status` avant toute modification ; ne pas revenir arbitrairement aux anciens commits ci-dessus.

## 2. Ce qui est vraiment présent

| Domaine | État constaté | Limites importantes |
|---|---|---|
| Authentification | API de connexion, session en base, token haché, cookie, contrôle Origin/CSRF, logout | Pas de MFA ou récupération de compte complète ; durcissement production restant |
| Dossiers | Liste selon affectations actives, ouverture, création, code, nom, ICE | Profil entreprise avancé et cycle de vie archivage/départ incomplets |
| Affectations | Rôles manager/reviewer/collaborator/client, attribution/retrait, contrôle serveur | Droits fins par module, durée de validité et délégation non complets |
| Exercices | Création, dates et refus des chevauchements | Clôture comptable, périodes et à-nouveaux non implémentés |
| Portail client | Invitation à usage unique, activation, dépôts, demandes/réponses, documents partagés | Livraison manuelle du lien ; pas de service e-mail transactionnel ; rapports financiers non implémentés |
| Documents | Fichier local privé, hash, doublons par dossier, quarantaine, téléchargement sous contrôle, partage | Pas d'OCR ni extraction comptable ; stockage objet/archivage renforcé restant |
| Traitement différé | Job en base, distribution Redis, worker, contrôle antivirus, revérification de l'accès, tâche de qualification | Pas d'orchestration comptable/fiscale complète ; reprise opérationnelle des échecs à compléter |
| Référentiel | Annuaire officiel, textes saisis avec provenance/dates/hash, revue à deux personnes, portée cabinet | Corpus non alimenté par défaut ; pas d'acquisition des originaux, de veille complète ni de règles exécutables |
| Audit | Événements enregistrés et triggers contre UPDATE/DELETE ordinaires | Pas de garantie contre administrateur SQL, de stockage WORM ni d'audit externe |
| Modules métier | Catalogue, navigation et sous-rubriques | Achats, ventes, comptabilité, trésorerie, banques, fiscalité, révision et reporting encore non opérationnels dans leur couverture complète |

Le portail peut consulter ses propres dépôts même s'ils ne sont pas encore publiés par le cabinet. Les documents internes du cabinet ne deviennent visibles que par partage explicite autorisé. Préserver cette distinction.

## 3. Carte du code

| Chemin | Responsabilité |
|---|---|
| `backend/app/main.py` | Routes auth, dossier, exercice, affectation, invitation, document, demande, audit et référentiel ; logique aujourd'hui concentrée à modulariser progressivement |
| `backend/app/models.py` | Cabinet, User, LoginSession, LoginAttempt, Dossier, Assignment, Exercise, Document, WorkItem, ClientRequest, Invitation, Job, Source, SourceVersion, Audit |
| `backend/app/schemas.py` | Validation Pydantic des commandes actuelles, champs supplémentaires interdits |
| `backend/app/security.py` | Mot de passe, token, principal, droits d'affectation, contrôle de portée et audit |
| `backend/app/config.py` / `db.py` | Paramètres, initialisation de stockage, moteur et sessions SQL |
| `backend/app/catalog.py` | Annuaire des autorités et catalogue des modules avec indicateur ready |
| `backend/app/processing.py` | Intégrité, antivirus, qualification et état des jobs |
| `backend/app/worker.py` | Distribution Redis/Dramatiq et réémission des jobs persistants |
| `backend/app/cli.py` | Création explicite du cabinet et de comptes collaborateurs sans mot de passe par défaut |
| `backend/migrations/versions/0001_foundation.py` | Schéma initial et protection ordinaire des audits ; utilise actuellement Base.metadata.create_all |
| `backend/tests/conftest.py` | Fixtures et base dédiée ; la variante PostgreSQL réinitialise son schéma |
| `backend/tests/test_boundaries.py` | Tests du socle et des frontières de sécurité |
| `backend/tests/seed_browser.py` | Données synthétiques navigateur, protégées par APP_ENV=test |
| `frontend/app/[[...path]]/page.tsx` | Chargement serveur session/dossiers, refus avant rendu et distinction cabinet/portail |
| `frontend/components/workspace.tsx` | Navigation et vues connectées, formulaires, dépôts, référentiel et écrans des modules restants |
| `frontend/components/ui.tsx` | Primitives visuelles conservées |
| `frontend/components/login.tsx` | Connexion et activation client |
| `frontend/lib/api.ts` / `types.ts` | Client HTTP, CSRF, erreurs et contrats frontend |
| `frontend/app/globals.css` / `v2.css` | Design validé repris et compositions des nouveaux parcours |
| `frontend/next.config.ts` | Relais vers API interne et en-têtes |
| `frontend/tests/workspaces.spec.ts` | Quatre parcours navigateur du premier incrément |
| `compose.yaml` | Web, API, migration, PostgreSQL, Redis, worker, dispatcher et ClamAV ; exposition locale du seul frontend |

## 4. Contrats API existants à conserver ou migrer explicitement

- `/api/auth/login`, `/api/auth/session`, `/api/auth/logout`, `/api/auth/activate`.
- `/api/dossiers`, `/api/dossiers/{dossier_id}`, exercices, affectations, invitations, aperçu, catalogue des modules.
- Documents : liste, dépôt, téléchargement et publication, tous dans la portée du dossier.
- Travaux : liste de qualification documentaire ; ce n'est pas encore une production comptable.
- Demandes : création cabinet, réponse client, clôture cabinet ; une réponse simple, pas une messagerie multi-fil complète.
- Historique audit du dossier selon rôle.
- `/api/knowledge/sources`, `/api/knowledge/versions`, détail et revue documentaire.
- `/api/dossiers/{dossier_id}/regulatory-readiness` : renvoie actuellement un blocage fixe de finalisation pour absence de règles exécutables approuvées.

Les futures opérations doivent avoir de vrais services métier ; ne pas remplacer le blocage réglementaire par un succès constant ou retourner les mêmes fixtures pour chaque dossier.

## 5. Risques et points de reprise prioritaires

1. **Migrations** : figer la baseline avant d'ajouter/importer de nouveaux modèles. Tester installation vide et upgrade réel. Ne pas modifier le schéma en développement avec create_all puis présenter cela comme une migration de production.
2. **Modularité** : main.py/workspace.tsx portent beaucoup de responsabilités. Extraire par domaine sans casser les routes ou la charte.
3. **Autorisations** : prévoir les références croisées de toutes les nouvelles entités. L'isolation actuelle repose surtout sur l'application et certaines contraintes composites ; RLS n'est pas déjà présent.
4. **Révocation frontend** : vérifier aussi caches, retours navigateur, onglets et données de l'en-tête, pas seulement le chargement d'une liste.
5. **Acquisition réglementaire** : une URL officielle associée à un texte saisi ne prouve pas sa fidélité. L'import des originaux, la hiérarchie des sources, les règles temporelles et la revue métier sont à construire.
6. **Jobs** : traiter doublons de distribution, concurrence, échecs définitifs, reprise autorisée, changement d'acteur et révocation sans traitement hors mandat.
7. **Documents** : les tests simulent le résultat antivirus. Vérifier le service réel, les gros dépôts, la durabilité et la restauration des fichiers.
8. **Invitations** : compléter expiration/annulation/renvoi/compte existant, contrôle de concurrence et livraison sécurisée. Aucun e-mail automatique aujourd'hui.
9. **Comptabilité** : aucun plan de comptes, journal, écriture ou moteur de validation métier complet dans le socle. Créer les invariants avant de brancher achats/ventes.
10. **Dépendances** : versions frontend initialement à plages et lockfile de vérification disponible en artefact/local. Contrôler le lockfile réellement présent dans le checkout et aligner npm ci/CI/Docker. Ne pas confondre un ancien audit npm avec une garantie actuelle.
11. **Production** : RELEASE_REVIEW_APPROVED est un garde technique, pas une preuve de revue. Formalités, hébergement, sous-traitants, sauvegardes, chiffrement, MFA et supervision restent à valider.

## 6. Preuves et limites de vérification

Le premier incrément a une exécution CI historique :
https://github.com/hamzaelmardi1344/mizania-v2/actions/runs/38596148242

Le rapport PostgreSQL récupéré contient 35 tests, zéro erreur, zéro échec, zéro test ignoré. Les quatre tests navigateur vérifient connexion obligatoire, affectations collaborateur, dépôt client persistant/accès internes interdits et référentiel visible. Cela ne valide pas des factures, écritures, rapprochements ou déclarations qui n'existent pas encore.

Lors de la préparation du relais, les sources disponibles ont été réexaminées et les commandes suivantes ont été réexécutées localement :
- `PYTHONPATH=backend pytest backend/tests/test_boundaries.py -q` : 35 tests réussis.
- `npm run typecheck` depuis frontend : réussi.

Le build et les tests PostgreSQL/navigateur sont à relancer dans le checkout de reprise pour tout prochain changement. L'assemblage complet Docker et ClamAV réel n'est pas déduit des résultats unitaires. Les captures jointes sont celles du socle V2 avec données synthétiques.

## 7. Règles produit à ne pas perdre

Le dossier est central ; B = cabinet + portail client ; conserver le design ; intelligence hors interface ; référentiel officiel conservé ; protection côté serveur ; dates/version de règle ; intervention humaine aux points sensibles ; opérations irréversibles sous autorisation ; pas de secret ou de donnée client dans Git.

Le prompt de reprise fournit les groupes de cas métier à reporter dans une matrice. Il ne constitue pas une certification d'exhaustivité juridique. Toute omission détectée doit devenir un cas explicite et non être masquée.

## 8. Premier résultat attendu de Codex

Un diagnostic basé sur le checkout réel, une matrice des cas connus avec état et preuves, une base de tests relancée, puis le premier lot métier vertical implémenté et testé. La cible reste tous les modules discutés ; aucune nouvelle maquette ou nouvelle liste d'agents ne doit remplacer les fonctionnalités.
