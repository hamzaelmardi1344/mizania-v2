from pathlib import Path
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from alembic.config import Config
from alembic import command
from app.main import create_app
from app.config import Settings
from app.models import Cabinet, User, Dossier, Assignment, Source
from app.catalog import SOURCES
from app.security import password_hash

PASSWORD = 'Fixture-test-password-2026'

@pytest.fixture
def app(tmp_path,monkeypatch):
    url = os.getenv('TEST_DATABASE_URL') or f'sqlite:///{tmp_path}/test.db'
    if os.getenv('TEST_DATABASE_URL'):
        # CI database is disposable and dedicated; never use a live DATABASE_URL here.
        engine=create_engine(url)
        with engine.begin() as c:
            c.exec_driver_sql('DROP SCHEMA public CASCADE')
            c.exec_driver_sql('CREATE SCHEMA public')
        engine.dispose()
    monkeypatch.setenv('DATABASE_URL',url)
    command.upgrade(Config(str(Path(__file__).parents[1]/'alembic.ini')),'head')
    settings=Settings(database_url=url,storage=tmp_path/'files',environment='test')
    app=create_app(settings)
    with app.state.db() as db:
        db.add_all([Cabinet(id='cab-a',name='Cabinet A'),Cabinet(id='cab-b',name='Cabinet B')]);db.flush()
        hashed=password_hash(PASSWORD)
        for id,cab,kind,admin,editor in [('manager','cab-a','staff',True,True),('staff','cab-a','staff',False,False),('reviewer','cab-a','staff',False,True),('client','cab-a','client',False,False),('foreign','cab-b','staff',True,False)]:
            db.add(User(id=id,cabinet_id=cab,email=id+'@test.invalid',name=id.title(),kind=kind,password_hash=hashed,cabinet_admin=admin,knowledge_editor=editor))
        db.flush()
        for id,cab in [('atlas','cab-a'),('sahara','cab-a'),('other','cab-b')]:
            db.add(Dossier(id=id,cabinet_id=cab,code=id,name=id.title()))
        db.flush()
        for uid,did,cab,role in [('manager','atlas','cab-a','manager'),('manager','sahara','cab-a','manager'),('staff','atlas','cab-a','collaborator'),('reviewer','atlas','cab-a','reviewer'),('client','atlas','cab-a','client'),('foreign','other','cab-b','manager')]:
            db.add(Assignment(user_id=uid,dossier_id=did,cabinet_id=cab,role=role))
        db.add_all([Source(**r) for r in SOURCES]);db.commit()
    yield app
    app.state.engine.dispose()

@pytest.fixture
def clients(app):
    opened=[]
    def login(name='manager'):
        c=TestClient(app,base_url='http://localhost:3000',headers={'origin':'http://localhost:3000'})
        assert c.post('/api/auth/login',json={'email':name+'@test.invalid','password':PASSWORD}).status_code==200
        c.headers['x-csrf-token']=c.get('/api/auth/session').json()['csrf']
        opened.append(c);return c
    yield login
    for c in opened:c.close()
