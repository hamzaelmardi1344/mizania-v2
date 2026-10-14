import hashlib
from urllib.parse import urlsplit, parse_qs
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update, delete
from sqlalchemy.exc import DBAPIError, IntegrityError
from app.models import User, Assignment, Document, Job, WorkItem, SourceVersion, Audit
from app.processing import process_job
from conftest import PASSWORD

PDF=b'%PDF-1.4\n% synthetic test fixture, no financial data\n%%EOF'
def upload(c,dossier='atlas',name='piece.pdf',payload=PDF):
    return c.post(f'/api/dossiers/{dossier}/documents',files={'file':(name,payload,'application/pdf')})
def run_jobs(app,scanner=lambda *args:True):
    with app.state.db() as db: ids=list(db.scalars(select(Job.id)))
    for id in ids:process_job(app.state.db,app.state.settings,id,scanner=scanner)

@pytest.mark.parametrize('path',['/api/auth/session','/api/dossiers','/api/dossiers/atlas','/api/dossiers/atlas/documents','/api/knowledge/sources'])
def test_auth_required(app,path):
    assert TestClient(app).get(path).status_code==401

def test_assignment_not_admin_bypass(clients):
    c=clients('staff')
    assert [d['id'] for d in c.get('/api/dossiers').json()]==['atlas']
    assert c.get('/api/dossiers/sahara').status_code==404
    assert clients('manager').get('/api/dossiers/other').status_code==404

@pytest.mark.parametrize('resource',['documents','overview','work','requests','audit','modules','regulatory-readiness'])
def test_cross_cabinet_every_resource(clients,resource):
    assert clients('foreign').get('/api/dossiers/atlas/'+resource).status_code==404

def test_portal_cannot_access_internal_resources(clients):
    c=clients('client')
    for path in ['work','modules','audit','regulatory-readiness','assignments']:
        assert c.get('/api/dossiers/atlas/'+path).status_code==403
    assert c.get('/api/knowledge/sources').status_code==403
    assert c.post('/api/dossiers',json={'name':'Illicit','code':'xxx'}).status_code==403

def test_csrf_origin_and_session_revocation(clients):
    c=clients()
    assert c.post('/api/dossiers',json={'name':'No csrf','code':'NC'},headers={'x-csrf-token':''}).status_code==403
    assert c.post('/api/dossiers',json={'name':'Bad origin','code':'BO'},headers={'origin':'https://evil.invalid'}).status_code==403
    raw=c.cookies.get('mizania_session')
    assert c.post('/api/auth/logout').status_code==200
    c.cookies.set('mizania_session',raw)
    assert c.get('/api/dossiers').status_code==401

def test_assignment_revocation_effective_immediately(app,clients):
    staff=clients('staff');manager=clients()
    result=manager.put('/api/dossiers/atlas/assignments',json={'user_id':'staff','role':'collaborator','active':False})
    assert result.status_code==200
    assert staff.get('/api/dossiers/atlas').status_code==404
    assert staff.get('/api/dossiers').json()==[]

def test_cannot_assign_foreign_user_or_wrong_kind(clients):
    c=clients()
    assert c.put('/api/dossiers/atlas/assignments',json={'user_id':'foreign','role':'manager'}).status_code==404
    assert c.put('/api/dossiers/atlas/assignments',json={'user_id':'client','role':'collaborator'}).status_code==422

def test_database_rejects_cross_tenant_relation(app):
    with app.state.db() as db:
        db.add(Assignment(cabinet_id='cab-a',dossier_id='atlas',user_id='foreign',role='manager'))
        with pytest.raises(IntegrityError):db.commit()

def test_dossier_creation_and_exercise_overlap(clients):
    c=clients();r=c.post('/api/dossiers',json={'name':'Nouvelle société','code':'NEW','ice':'123456789012345'})
    assert r.status_code==201
    assert r.json()['role']=='manager'
    ex={'label':'2026','starts_on':'2026-01-01','ends_on':'2026-12-31'}
    assert c.post('/api/dossiers/atlas/exercises',json=ex).status_code==201
    assert c.post('/api/dossiers/atlas/exercises',json=ex).status_code==409
    assert clients('client').post('/api/dossiers/atlas/exercises',json=ex).status_code==403

def test_upload_quarantine_idor_duplicate_and_visibility(app,clients):
    manager=clients();client=clients('client');foreign=clients('foreign')
    r=upload(manager);assert r.status_code==201
    doc=r.json()['id'];path=f'/api/dossiers/atlas/documents/{doc}'
    assert manager.get(path+'/download').status_code==409
    assert client.get('/api/dossiers/atlas/documents').json()==[]
    assert client.get(path+'/download').status_code==404
    assert foreign.get(path+'/download').status_code==404
    assert upload(manager).status_code==409
    assert upload(manager,'sahara').status_code==201
    run_jobs(app)
    assert manager.get(path+'/download').content==PDF
    assert manager.post(path+'/publish').status_code==200
    assert len(client.get('/api/dossiers/atlas/documents').json())==1
    assert client.get(path+'/download').content==PDF
    assert client.get('/api/dossiers/atlas/overview').json()['documents']==1

def test_client_owns_received_document_but_cannot_publish(app,clients):
    c=clients('client');doc=upload(c).json()['id']
    assert len(c.get('/api/dossiers/atlas/documents').json())==1
    assert c.post(f'/api/dossiers/atlas/documents/{doc}/publish').status_code==403
    assert upload(c,'sahara').status_code==404

def test_invalid_files_and_size_limit(app,clients):
    c=clients()
    assert upload(c,name='attack.html',payload=b'<script>bad</script>').status_code==415
    assert upload(c,payload=b'not a PDF').status_code==415
    assert upload(c,payload=PDF+b'0'*(app.state.settings.max_upload)).status_code==413

def test_worker_is_idempotent_and_invisible(app,clients):
    c=clients();upload(c)
    run_jobs(app);run_jobs(app)
    with app.state.db() as db:
        assert len(list(db.scalars(select(WorkItem))))==1
        assert db.scalar(select(Job)).state=='done'
    assert c.get('/api/dossiers/atlas/work').json()[0]['title']=='Pièce à qualifier'

def test_worker_rechecks_access_after_revocation(app,clients):
    upload(clients('staff'))
    clients().put('/api/dossiers/atlas/assignments',json={'user_id':'staff','role':'collaborator','active':False})
    run_jobs(app)
    with app.state.db() as db:
        assert db.scalar(select(Job)).state=='cancelled'
        assert not db.scalar(select(WorkItem))

def test_scanner_failure_is_closed(app,clients):
    c=clients();doc=upload(c).json()['id']
    def broken(*args):raise ConnectionError('offline')
    run_jobs(app,broken)
    assert c.get(f'/api/dossiers/atlas/documents/{doc}/download').status_code==409
    with app.state.db() as db:assert db.scalar(select(Job)).error_code=='SCANNER_UNAVAILABLE'

def test_infected_and_tampered_documents_are_blocked(app,clients):
    c=clients();doc=upload(c).json()['id'];run_jobs(app,lambda *args:False)
    assert c.get(f'/api/dossiers/atlas/documents/{doc}/download').status_code==409
    with app.state.db() as db:assert db.get(Document,doc).state=='blocked'

def test_requests_end_to_end_and_no_cross_dossier_reply(clients):
    c=clients();portal=clients('client')
    r=c.post('/api/dossiers/atlas/requests',json={'title':'Pièce manquante','body':'Merci de déposer le relevé bancaire.'})
    assert r.status_code==201;id=r.json()['id']
    assert len(portal.get('/api/dossiers/atlas/requests').json())==1
    assert portal.post(f'/api/dossiers/sahara/requests/{id}/reply',json={'reply':'OK'}).status_code==404
    assert portal.post(f'/api/dossiers/atlas/requests/{id}/reply',json={'reply':'Le relevé sera transmis demain.'}).status_code==200
    assert portal.post(f'/api/dossiers/atlas/requests/{id}/reply',json={'reply':'Overwrite'}).status_code==409
    assert c.get('/api/dossiers/atlas/requests').json()[0]['state']=='answered'
    assert c.post(f'/api/dossiers/atlas/requests/{id}/close').status_code==200

def test_invitation_single_use_and_scoped(app,clients):
    r=clients().post('/api/dossiers/atlas/invitations',json={'email':'nouveau@test.invalid','name':'Nouveau client'})
    assert r.status_code==201
    token=parse_qs(urlsplit(r.json()['activation_url']).fragment)['token'][0]
    client=TestClient(app,headers={'origin':'http://localhost:3000'})
    assert client.post('/api/auth/activate',json={'token':token,'password':PASSWORD}).status_code==201
    assert client.post('/api/auth/activate',json={'token':token,'password':PASSWORD}).status_code==400
    assert client.post('/api/auth/login',json={'email':'nouveau@test.invalid','password':PASSWORD}).status_code==200
    assert [x['id'] for x in client.get('/api/dossiers').json()]==['atlas']

def version_payload():
    return {'source_id':'sgg','title':'Texte de test NON JURIDIQUE','citation':'Fixture technique article fictif',
        'url':'https://www.sgg.gov.ma/test-fixture','text':'Texte synthétique de test, sans valeur juridique et sans règle fiscale réelle.',
        'published_on':'2026-01-01','effective_from':'2026-01-01'}

def test_knowledge_four_eyes_and_immutable_version(clients):
    c=clients();r=c.post('/api/knowledge/versions',json=version_payload());assert r.status_code==201
    id=r.json()['id'];assert r.json()['sha256']==hashlib.sha256(version_payload()['text'].encode()).hexdigest()
    review={'decision':'verified','note':'Contrôle documentaire effectué sur une fixture de test, pas une loi.'}
    assert c.post(f'/api/knowledge/versions/{id}/review',json=review).status_code==403
    reviewer=clients('reviewer');assert reviewer.post(f'/api/knowledge/versions/{id}/review',json=review).status_code==200
    assert reviewer.post(f'/api/knowledge/versions/{id}/review',json=review).status_code==409
    assert c.get('/api/dossiers/atlas/regulatory-readiness').json()['finalization_available'] is False

def test_knowledge_rejects_unofficial_and_escalation(clients):
    p=version_payload();p['url']='https://www.sgg.gov.ma.evil.invalid/fake'
    assert clients().post('/api/knowledge/versions',json=p).status_code==422
    assert clients('staff').post('/api/knowledge/versions',json=version_payload()).status_code==403
    p=version_payload();p['status']='verified'
    assert clients().post('/api/knowledge/versions',json=p).status_code==422

def test_audit_is_append_only(app,clients):
    clients()
    for action in (update(Audit).values(action='altered'),delete(Audit)):
        with app.state.db() as db:
            with pytest.raises(DBAPIError):db.execute(action);db.commit()

def test_bruteforce_account_limit(app):
    c=TestClient(app,headers={'origin':'http://localhost:3000'})
    for _ in range(8):assert c.post('/api/auth/login',json={'email':'unknown@test.invalid','password':'wrong'}).status_code==401
    assert c.post('/api/auth/login',json={'email':'unknown@test.invalid','password':'wrong'}).status_code==429

def test_regulatory_drafts_do_not_cross_cabinets(app,clients):
    owner=clients();row=owner.post('/api/knowledge/versions',json=version_payload()).json()
    with app.state.db() as db:
        user=db.get(User,'foreign');user.knowledge_editor=True;db.commit()
    stranger=clients('foreign')
    assert stranger.get('/api/knowledge/versions').json()==[]
    assert stranger.get('/api/knowledge/versions/'+row['id']).status_code==404
    assert all(s['versions']==0 for s in stranger.get('/api/knowledge/sources').json())
    assert stranger.post('/api/knowledge/versions/'+row['id']+'/review',json={'decision':'verified','note':'Attempted cross-cabinet verification must be denied.'}).status_code==404

def test_malformed_reference_url_is_rejected(clients):
    p=version_payload();p['url']='https://www.sgg.gov.ma:notaport/document'
    assert clients().post('/api/knowledge/versions',json=p).status_code==422

def test_document_tamper_fails_closed(app,clients):
    c=clients();doc=upload(c).json()['id']
    (app.state.settings.storage/'cab-a'/'atlas'/doc).write_bytes(b'tampered')
    run_jobs(app)
    assert c.get(f'/api/dossiers/atlas/documents/{doc}/download').status_code==409
    with app.state.db() as db: assert db.scalar(select(Job)).error_code=='INTEGRITY_FAILURE'
