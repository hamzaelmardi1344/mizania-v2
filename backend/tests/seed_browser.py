"""Synthetic, empty-account browser fixtures. Explicit test environment only."""
import os
from pathlib import Path
from alembic.config import Config
from alembic import command
from app.config import Settings
from app.db import make_database
from app.models import Cabinet, User, Dossier, Assignment, Source
from app.catalog import SOURCES
from app.security import password_hash
if os.environ.get("APP_ENV") != "test":
    raise SystemExit("Browser fixtures are forbidden outside APP_ENV=test")
password=os.environ["E2E_PASSWORD"]
settings=Settings();settings.storage.mkdir(parents=True,exist_ok=True)
command.upgrade(Config(str(Path(__file__).parents[1]/"alembic.ini")),"head")
_,factory=make_database(settings)
with factory() as db:
    if db.get(Cabinet,"e2e-cabinet"):
        raise SystemExit("Use an empty disposable database for browser tests")
    db.add(Cabinet(id="e2e-cabinet",name="Cabinet de test"));db.flush()
    for name,kind in [("manager","staff"),("staff","staff"),("client","client")]:
        db.add(User(id=name,cabinet_id="e2e-cabinet",email=name+"@test.invalid",name=name.title(),kind=kind,
            cabinet_admin=name=="manager",knowledge_editor=name=="manager",password_hash=password_hash(password)))
    db.flush()
    for id,name in [("atlas","Atlas — dossier de test"),("sahara","Sahara — dossier de test")]:
        db.add(Dossier(id=id,cabinet_id="e2e-cabinet",code=id.upper(),name=name))
    db.flush()
    for user,dossier,role in [("manager","atlas","manager"),("manager","sahara","manager"),("staff","atlas","collaborator"),("client","atlas","client")]:
        db.add(Assignment(cabinet_id="e2e-cabinet",user_id=user,dossier_id=dossier,role=role))
    db.add_all([Source(**s) for s in SOURCES]);db.commit()
