# Mizania V2

Plateforme de cabinet centrée sur les dossiers clients, avec un portail client distinct. Premier incrément de développement : authentification, affectations, documents, échanges et référentiel réglementaire. **Ce dépôt n’est pas encore une version de production ni un logiciel comptable complet.**

## Démarrage local avec Docker

Prérequis : Docker avec Compose, Node 22/Python 3.13 uniquement pour un développement sans conteneurs. La première installation télécharge les dépendances et les signatures antivirus.

```sh
git clone https://github.com/hamzaelmardi1344/mizania-v2.git
cd mizania-v2
cp .env.example .env
# Remplacer la valeur vide de POSTGRES_PASSWORD dans .env par le résultat de :
openssl rand -hex 32
docker compose up --build -d
# Le mot de passe personnel est demandé sans être affiché ni écrit dans Git :
docker compose exec api python -m app.cli bootstrap --name "Votre nom" --email "vous@cabinet.ma" --cabinet "Votre cabinet" --knowledge-editor
```

Ouvrir `http://localhost:3000`. Se connecter, créer un dossier, puis ouvrir **Paramètres du dossier** pour créer un exercice, affecter un collaborateur et inviter un représentant client. Aucun compte, mot de passe par défaut ou dossier fictif n’est installé.

Pour créer un deuxième collaborateur (utiliser l’identifiant du cabinet affiché au bootstrap) :

```sh
docker compose exec api python -m app.cli add-staff --name "Collaborateur" --email "collaborateur@cabinet.ma" --cabinet-id "IDENTIFIANT_DU_CABINET"
```

Ajouter `--knowledge-editor` seulement pour un responsable autorisé à vérifier les références. La validation d’une référence exige **deux personnes distinctes**. Affecter ensuite le collaborateur au dossier depuis l’interface. Une invitation client génère un lien personnel : aucun e-mail n’est envoyé dans cet incrément.

Seul le port local 3000 est publié. PostgreSQL, Redis, fichiers, antivirus et API ne sont pas exposés à Internet. Ne pas utiliser cette composition locale comme déploiement public.

## Fonctionnement implémenté

Connexion obligatoire côté serveur, sessions révocables en base, cookies HttpOnly/SameSite, contrôle Origin et CSRF. Sélection exclusivement parmi les dossiers attribués. Affectations et contrôles d’accès également appliqués aux téléchargements et aux traitements différés.

Portail client : dépôts et suivi de ses documents, consultation des documents explicitement partagés, réponses aux demandes. Les travaux internes et le référentiel du cabinet ne sont pas accessibles au client.

Dépôt PDF/PNG/JPEG limité à 10 Mo : empreinte SHA-256, détection des doublons par dossier, quarantaine, tâche persistante en base, distribution Redis, analyse ClamAV, reprise contrôlée et tâche de qualification. **Aucun OCR ou écriture comptable n’est simulé.** Un antivirus indisponible maintient le fichier en quarantaine.

Base de connaissances conservée : annuaire de sources officielles marocaines, texte importé avec référence, dates et empreinte, revue documentaire à deux personnes. Les versions éditoriales sont cloisonnées par cabinet. **L’annuaire n’est pas un corpus de lois déjà validé. Un texte vérifié n’est pas une règle exécutable.** Les finalisations comptables/fiscales sont volontairement indisponibles.

## Modules en cours de construction

Achats, ventes, comptabilité, trésorerie, rapprochement, fiscalité, révision et reporting disposent de leur place dans la navigation et de leur périmètre issu des captures Bleez. Leurs opérations métier complètes, règles et intégrations sont **à implémenter** ; l’interface le signale sans données financières inventées. Voir [STATUS.md](STATUS.md).

## Architecture et design

Next.js/React/TypeScript ; FastAPI/Pydantic/SQLAlchemy ; PostgreSQL/Alembic ; Redis/Dramatiq ; ClamAV. Monolithe modulaire, tâches hors requête, aucun fournisseur de modèles externe appelé à ce stade.

Les tokens et primitives du frontend Mizania approuvé sont repris, les parcours sont réorganisés autour des dossiers. [Provenance et invariants visuels](docs/DESIGN.md). Aucun fichier `.env`, secret, document client ou historique du dépôt précédent n’a été recopié.

## Tests

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt -r backend/requirements-test.txt
PYTHONPATH=backend pytest backend/tests/test_boundaries.py -q
cd frontend
npm install
npm run typecheck
npm run build
```

Le workflow GitHub vérifie SQLite et PostgreSQL, le typage, le build et les parcours Playwright avec comptes synthétiques et base jetable. Les captures de validation sont publiées en artefact CI, jamais des documents réels. Ne jamais définir `TEST_DATABASE_URL` sur une base réelle : les tests réinitialisent son schéma.

Les dépendances frontend sont résolues dans leur version majeure ; la CI produit le lockfile. Le gel des dépendances et la revue des avis de sécurité sont requis avant une release. Une CI non exécutée ou échouée ne constitue pas une validation.

## Avant toute production

Lire [les conditions de mise en production](docs/RELEASE-GATES.md). L’application bloque `APP_ENV=production` sans configuration HTTPS/PostgreSQL/antivirus et revue explicitement déclarée ; cet indicateur technique ne remplace aucun audit. Aucune conformité juridique absolue n’est revendiquée.
