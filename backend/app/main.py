from contextlib import asynccontextmanager
from datetime import date
from pathlib import PurePath
import hashlib
import secrets
from urllib.parse import urlsplit
from fastapi import FastAPI, Request, Response, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select, func, or_, delete
from sqlalchemy.exc import IntegrityError
from .config import Settings
from .db import make_database
from .models import (Cabinet, User, LoginSession, LoginAttempt, Dossier, Assignment, Exercise,
                     Document, WorkItem, ClientRequest, Invitation, Job, Source, SourceVersion, Audit)
from .security import (principal, scoped, require_staff, audit, digest, now, verify, password_hash, DUMMY_HASH)
from .schemas import (Login, NewDossier, NewExercise, NewAssignment, Invite, AcceptInvitation,
                      NewRequest, Reply, NewVersion, ReviewVersion)
from .catalog import MODULES

def create_app(settings: Settings | None = None):
    settings = settings or Settings()
    settings.validate()
    engine, factory = make_database(settings)
    app = FastAPI(title="Mizania", docs_url="/api/docs" if settings.environment != "production" else None,
                  openapi_url="/api/openapi.json" if settings.environment != "production" else None)
    app.state.db, app.state.engine, app.state.settings = factory, engine, settings

    @app.middleware("http")
    async def boundaries(request: Request, call_next):
        # Origin check also protects login/invitation endpoints before a session exists.
        if request.method not in {"GET", "HEAD", "OPTIONS"} and request.headers.get("origin") != settings.origin:
            return JSONResponse({"detail":"Origine de la requête non autorisée."}, status_code=403)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store, private"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.exception_handler(IntegrityError)
    async def integrity_error(request, exc):
        return JSONResponse({"detail":"Conflit de données. Rechargez la page avant de réessayer."}, status_code=409)

    def actor(db, request): return principal(request, db)[0]
    def staff(db, request):
        user = actor(db, request); require_staff(user); return user
    def admin(db, request):
        user = staff(db, request)
        if not user.cabinet_admin: raise HTTPException(403, "Administration du cabinet requise.")
        return user
    def knowledge_editor(db, request):
        user = staff(db, request)
        if not user.knowledge_editor: raise HTTPException(403, "Habilitation référentiel requise.")
        return user
    def doc_query(user, dossier_id):
        query = select(Document).where(Document.cabinet_id == user.cabinet_id, Document.dossier_id == dossier_id)
        if user.kind == "client": query = query.where(or_(Document.uploaded_by == user.id, Document.published.is_(True)))
        return query
    def get_document(db, user, dossier_id, doc_id):
        scoped(db, user, dossier_id)
        doc = db.scalar(doc_query(user, dossier_id).where(Document.id == doc_id))
        if not doc: raise HTTPException(404, "Document introuvable.")
        return doc
    def doc_out(doc):
        return {key:getattr(doc,key) for key in ("id","filename","media_type","size","category","state","published","created_at")}
    def dossier_out(dossier, assignment):
        return {"id":dossier.id,"name":dossier.name,"code":dossier.code,"ice":dossier.ice,"role":assignment.role}
    def version_out(version, include_text=False):
        fields = ["id","source_id","title","citation","url","sha256","effective_from","effective_to",
                  "published_on","captured_at","status","created_by","reviewed_by","review_note"]
        result = {key:getattr(version,key) for key in fields}
        if include_text: result["text"] = version.text
        return result

    @app.get("/api/health")
    def health():
        with factory() as db: db.execute(select(1))
        return {"status":"ok"}

    @app.post("/api/auth/login")
    def login(body: Login, request: Request, response: Response):
        email = body.email.lower().strip()
        # The API is private behind the web gateway. Ignore spoofable forwarded headers.
        keys = [digest("email:"+email), digest("peer:"+(request.client.host if request.client else "unknown"))]
        with factory() as db:
            db.execute(delete(LoginAttempt).where(LoginAttempt.at < now()-900))
            for key, limit in zip(keys, (8, 100)):
                if db.scalar(select(func.count()).select_from(LoginAttempt).where(LoginAttempt.key == key)) >= limit:
                    raise HTTPException(429, "Trop de tentatives. Réessayez dans 15 minutes.", headers={"Retry-After":"900"})
            user = db.scalar(select(User).where(User.email == email))
            valid = verify(body.password, user.password_hash if user else DUMMY_HASH)
            if not user or not valid or not user.active:
                db.add_all([LoginAttempt(key=key, at=now()) for key in keys]); db.commit()
                raise HTTPException(401, "Identifiants incorrects.")
            token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            db.add(LoginSession(token_hash=digest(token), user_id=user.id, csrf=csrf, expires_at=now()+settings.session_seconds))
            audit(db, user, "session.opened", user.id); db.commit()
            response.set_cookie("mizania_session", token, max_age=settings.session_seconds,
                                httponly=True, secure=settings.secure, samesite="strict", path="/")
            return {"kind":user.kind}

    @app.get("/api/auth/session")
    def session(request: Request):
        with factory() as db:
            user, session = principal(request, db)
            return {"id":user.id,"name":user.name,"email":user.email,"kind":user.kind,
                    "cabinet_name":db.get(Cabinet,user.cabinet_id).name,"csrf":session.csrf,
                    "cabinet_admin":user.cabinet_admin,"knowledge_editor":user.knowledge_editor}

    @app.post("/api/auth/logout")
    def logout(request: Request, response: Response):
        with factory() as db:
            user, session = principal(request, db)
            db.delete(session); audit(db,user,"session.closed",user.id); db.commit()
        response.delete_cookie("mizania_session",path="/",secure=settings.secure,httponly=True,samesite="strict")
        return {"ok":True}

    @app.get("/api/dossiers")
    def dossiers(request: Request):
        with factory() as db:
            user=actor(db,request)
            rows=db.execute(select(Dossier,Assignment).join(Assignment,
                (Assignment.dossier_id==Dossier.id)&(Assignment.cabinet_id==Dossier.cabinet_id)).where(
                Dossier.cabinet_id==user.cabinet_id,Dossier.active.is_(True),Assignment.user_id==user.id,
                Assignment.active.is_(True),Assignment.role.in_(["client"] if user.kind=="client" else ["manager","reviewer","collaborator"])).order_by(Dossier.name)).all()
            return [dossier_out(d,a) for d,a in rows]

    @app.post("/api/dossiers",status_code=201)
    def create_dossier(body: NewDossier, request: Request):
        with factory() as db:
            user=admin(db,request)
            dossier=Dossier(cabinet_id=user.cabinet_id,**body.model_dump());db.add(dossier);db.flush()
            assignment=Assignment(cabinet_id=user.cabinet_id,dossier_id=dossier.id,user_id=user.id,role="manager")
            db.add(assignment);audit(db,user,"dossier.created",dossier.id,dossier.id);db.commit()
            return dossier_out(dossier,assignment)

    @app.get("/api/dossiers/{dossier_id}")
    def detail(dossier_id: str, request: Request):
        with factory() as db:
            user=actor(db,request);dossier,assignment=scoped(db,user,dossier_id)
            result=dossier_out(dossier,assignment)
            exercises=db.scalars(select(Exercise).where(Exercise.cabinet_id==user.cabinet_id,Exercise.dossier_id==dossier_id).order_by(Exercise.starts_on.desc())).all()
            result["exercises"]=[{"id":x.id,"label":x.label,"starts_on":x.starts_on,"ends_on":x.ends_on,"closed":x.closed} for x in exercises]
            return result

    @app.post("/api/dossiers/{dossier_id}/exercises",status_code=201)
    def create_exercise(dossier_id: str, body: NewExercise, request: Request):
        with factory() as db:
            user=staff(db,request);scoped(db,user,dossier_id,{"manager"})
            db.execute(select(Dossier).where(Dossier.id==dossier_id).with_for_update())
            overlap=db.scalar(select(Exercise).where(Exercise.cabinet_id==user.cabinet_id,Exercise.dossier_id==dossier_id,
                 Exercise.starts_on<=body.ends_on,Exercise.ends_on>=body.starts_on))
            if overlap: raise HTTPException(409,"Cet exercice chevauche une période existante.")
            ex=Exercise(cabinet_id=user.cabinet_id,dossier_id=dossier_id,**body.model_dump());db.add(ex);db.flush()
            audit(db,user,"exercise.created",ex.id,dossier_id);db.commit();return {"id":ex.id}

    @app.get("/api/cabinet/users")
    def members(request: Request):
        with factory() as db:
            user=admin(db,request)
            return [{"id":x.id,"name":x.name,"email":x.email,"kind":x.kind} for x in db.scalars(select(User).where(User.cabinet_id==user.cabinet_id,User.active.is_(True)))]

    @app.get("/api/dossiers/{dossier_id}/assignments")
    def assignments(dossier_id: str,request: Request):
        with factory() as db:
            user=staff(db,request);scoped(db,user,dossier_id,{"manager"})
            rows=db.execute(select(Assignment,User).join(User,User.id==Assignment.user_id).where(Assignment.cabinet_id==user.cabinet_id,Assignment.dossier_id==dossier_id)).all()
            return [{"user_id":u.id,"name":u.name,"email":u.email,"role":a.role,"active":a.active} for a,u in rows]

    @app.put("/api/dossiers/{dossier_id}/assignments")
    def assign(dossier_id: str,body: NewAssignment,request: Request):
        with factory() as db:
            user=admin(db,request);scoped(db,user,dossier_id,{"manager"})
            target=db.scalar(select(User).where(User.id==body.user_id,User.cabinet_id==user.cabinet_id,User.active.is_(True)))
            if not target: raise HTTPException(404,"Utilisateur introuvable.")
            if (target.kind=="client") != (body.role=="client"): raise HTTPException(422,"Rôle incompatible avec cet espace.")
            if target.id==user.id and (not body.active or body.role!="manager"):
                raise HTTPException(409,"Faites effectuer votre retrait par un autre responsable habilité.")
            row=db.scalar(select(Assignment).where(Assignment.user_id==target.id,Assignment.dossier_id==dossier_id))
            if row: row.role,row.active=body.role,body.active
            else: db.add(Assignment(cabinet_id=user.cabinet_id,dossier_id=dossier_id,**body.model_dump()))
            audit(db,user,"assignment.updated",target.id,dossier_id,{"role":body.role,"active":body.active});db.commit()
            return {"ok":True}

    @app.post("/api/dossiers/{dossier_id}/invitations",status_code=201)
    def invite(dossier_id: str,body: Invite,request: Request):
        with factory() as db:
            user=staff(db,request);scoped(db,user,dossier_id,{"manager"})
            if db.scalar(select(User).where(User.email==body.email.lower())):
                raise HTTPException(409,"Ce compte nécessite une affectation par l’administrateur, pas une nouvelle invitation.")
            token=secrets.token_urlsafe(32)
            db.add(Invitation(token_hash=digest(token),cabinet_id=user.cabinet_id,dossier_id=dossier_id,
                email=body.email.lower(),name=body.name,created_by=user.id,expires_at=now()+48*3600))
            audit(db,user,"client.invited",digest(token),dossier_id);db.commit()
            # Fragment keeps the one-time secret out of HTTP access logs and referrers.
            return {"activation_url":settings.origin+"/activation#token="+token,"expires_in_hours":48,"delivery":"manual"}

    @app.post("/api/auth/activate",status_code=201)
    def activate(body: AcceptInvitation):
        with factory() as db:
            invitation=db.scalar(select(Invitation).where(Invitation.token_hash==digest(body.token)).with_for_update())
            if not invitation or invitation.consumed or invitation.expires_at<=now():
                raise HTTPException(400,"Invitation expirée ou déjà utilisée.")
            issuer=db.get(User,invitation.created_by)
            if not issuer or not issuer.active: raise HTTPException(400,"Invitation révoquée.")
            scoped(db,issuer,invitation.dossier_id,{"manager"})
            user=User(cabinet_id=invitation.cabinet_id,email=invitation.email,name=invitation.name,
                password_hash=password_hash(body.password),kind="client")
            db.add(user);db.flush()
            db.add(Assignment(cabinet_id=user.cabinet_id,dossier_id=invitation.dossier_id,user_id=user.id,role="client"))
            invitation.consumed=True;audit(db,user,"client.activated",user.id,invitation.dossier_id);db.commit()
            return {"ok":True}

    @app.get("/api/dossiers/{dossier_id}/overview")
    def overview(dossier_id: str, request: Request):
        with factory() as db:
            user=actor(db,request);scoped(db,user,dossier_id)
            docs=list(db.scalars(doc_query(user,dossier_id)))
            requests=list(db.scalars(select(ClientRequest).where(ClientRequest.cabinet_id==user.cabinet_id,ClientRequest.dossier_id==dossier_id)))
            work=list(db.scalars(select(WorkItem).where(WorkItem.cabinet_id==user.cabinet_id,WorkItem.dossier_id==dossier_id,WorkItem.state=="open"))) if user.kind=="staff" else []
            return {"documents":len(docs),"received":sum(d.state=="received" for d in docs),"published":sum(d.published for d in docs),
                    "requests":sum(r.state!="closed" for r in requests),"work":len(work),
                    "recent_documents":[doc_out(d) for d in sorted(docs,key=lambda d:d.created_at,reverse=True)[:5]]}

    @app.get("/api/dossiers/{dossier_id}/modules")
    def modules(dossier_id: str,request: Request):
        with factory() as db: user=staff(db,request);scoped(db,user,dossier_id)
        return MODULES

    @app.get("/api/dossiers/{dossier_id}/documents")
    def documents(dossier_id: str,request: Request,q: str=Query(default="",max_length=100),limit: int=Query(default=100,ge=1,le=200)):
        with factory() as db:
            user=actor(db,request);scoped(db,user,dossier_id)
            query=doc_query(user,dossier_id)
            if q: query=query.where(Document.filename.icontains(q,autoescape=True))
            return [doc_out(d) for d in db.scalars(query.order_by(Document.created_at.desc(),Document.id).limit(limit))]

    @app.post("/api/dossiers/{dossier_id}/documents",status_code=201)
    async def upload(dossier_id: str,request: Request,file: UploadFile=File(...)):
        with factory() as db:
            user=actor(db,request);scoped(db,user,dossier_id)
            filename=(file.filename or "document").replace(chr(92), "/").split("/")[-1]
            if not filename or len(filename)>200 or any(ord(c)<32 for c in filename): raise HTTPException(422,"Nom de fichier invalide.")
            data=bytearray()
            while chunk:=await file.read(65536):
                data.extend(chunk)
                if len(data)>settings.max_upload: raise HTTPException(413,"La taille maximale est de 10 Mo.")
            await file.close()
            suffix=PurePath(filename).suffix.lower()
            signatures={".pdf":(b"%PDF-","application/pdf"),".png":(b"\x89PNG\r\n\x1a\n","image/png"),".jpg":(b"\xff\xd8\xff","image/jpeg"),".jpeg":(b"\xff\xd8\xff","image/jpeg")}
            if suffix not in signatures or not bytes(data).startswith(signatures[suffix][0]):
                raise HTTPException(415,"Seuls les fichiers PDF, PNG et JPEG valides sont acceptés.")
            sha=hashlib.sha256(data).hexdigest()
            if db.scalar(select(Document.id).where(Document.cabinet_id==user.cabinet_id,Document.dossier_id==dossier_id,Document.sha256==sha)):
                raise HTTPException(409,"Ce document a déjà été déposé dans ce dossier.")
            doc=Document(cabinet_id=user.cabinet_id,dossier_id=dossier_id,uploaded_by=user.id,filename=filename,
                         media_type=signatures[suffix][1],sha256=sha,size=len(data),created_at=now())
            db.add(doc);db.flush()
            folder=settings.storage/user.cabinet_id/dossier_id;folder.mkdir(parents=True,exist_ok=True)
            path=folder/doc.id
            try:
                with path.open("xb") as stream: stream.write(data)
                db.add(Job(cabinet_id=user.cabinet_id,dossier_id=dossier_id,document_id=doc.id,actor_id=user.id))
                audit(db,user,"document.received",doc.id,dossier_id,{"sha256":sha});db.commit()
            except Exception:
                path.unlink(missing_ok=True);raise
            return doc_out(doc)

    @app.get("/api/dossiers/{dossier_id}/documents/{document_id}/download")
    def download(dossier_id: str,document_id: str,request: Request):
        with factory() as db:
            user=actor(db,request);doc=get_document(db,user,dossier_id,document_id)
            if doc.scan!="clean": raise HTTPException(409,"Ce fichier reste indisponible avant son contrôle de sécurité.")
            path=settings.storage/user.cabinet_id/dossier_id/doc.id
            if not path.is_file(): raise HTTPException(404,"Fichier indisponible. Contactez le cabinet.")
            # Integrity is checked again before disclosure, not only at ingestion.
            if hashlib.sha256(path.read_bytes()).hexdigest()!=doc.sha256: raise HTTPException(409,"L’intégrité du fichier doit être vérifiée.")
            audit(db,user,"document.downloaded",doc.id,dossier_id);db.commit()
            return FileResponse(path,filename=doc.filename,media_type="application/octet-stream",content_disposition_type="attachment")

    @app.post("/api/dossiers/{dossier_id}/documents/{document_id}/publish")
    def publish(dossier_id: str,document_id: str,request: Request):
        with factory() as db:
            user=staff(db,request);scoped(db,user,dossier_id,{"manager","reviewer"})
            doc=get_document(db,user,dossier_id,document_id)
            if doc.scan!="clean": raise HTTPException(409,"Le contrôle de sécurité du document n’est pas terminé.")
            doc.published=True;audit(db,user,"document.published",doc.id,dossier_id);db.commit();return doc_out(doc)

    @app.get("/api/dossiers/{dossier_id}/work")
    def work(dossier_id: str,request: Request):
        with factory() as db:
            user=staff(db,request);scoped(db,user,dossier_id)
            return [{"id":w.id,"title":w.title,"reason":w.reason,"state":w.state,"document_id":w.document_id}
                for w in db.scalars(select(WorkItem).where(WorkItem.cabinet_id==user.cabinet_id,WorkItem.dossier_id==dossier_id))]

    @app.get("/api/dossiers/{dossier_id}/requests")
    def requests(dossier_id: str,request: Request):
        with factory() as db:
            user=actor(db,request);scoped(db,user,dossier_id)
            return [{key:getattr(r,key) for key in ("id","title","body","reply","state","created_at")}
                for r in db.scalars(select(ClientRequest).where(ClientRequest.cabinet_id==user.cabinet_id,
                    ClientRequest.dossier_id==dossier_id).order_by(ClientRequest.created_at.desc()))]

    @app.post("/api/dossiers/{dossier_id}/requests",status_code=201)
    def new_request(dossier_id: str,body: NewRequest,request: Request):
        with factory() as db:
            user=staff(db,request);scoped(db,user,dossier_id)
            row=ClientRequest(cabinet_id=user.cabinet_id,dossier_id=dossier_id,created_at=now(),**body.model_dump());db.add(row);db.flush()
            audit(db,user,"request.created",row.id,dossier_id);db.commit();return {"id":row.id}

    @app.post("/api/dossiers/{dossier_id}/requests/{request_id}/reply")
    def reply(dossier_id: str,request_id: str,body: Reply,request: Request):
        with factory() as db:
            user=actor(db,request);scoped(db,user,dossier_id)
            if user.kind!="client": raise HTTPException(403,"Réponse réservée au client.")
            row=db.scalar(select(ClientRequest).where(ClientRequest.id==request_id,ClientRequest.cabinet_id==user.cabinet_id,
                           ClientRequest.dossier_id==dossier_id).with_for_update())
            if not row: raise HTTPException(404,"Demande introuvable.")
            if row.state!="open": raise HTTPException(409,"Cette demande possède déjà une réponse ou est clôturée.")
            row.reply=body.reply;row.state="answered";audit(db,user,"request.answered",row.id,dossier_id);db.commit();return {"ok":True}

    @app.post("/api/dossiers/{dossier_id}/requests/{request_id}/close")
    def close_request(dossier_id: str,request_id: str,request: Request):
        with factory() as db:
            user=staff(db,request);scoped(db,user,dossier_id)
            row=db.scalar(select(ClientRequest).where(ClientRequest.id==request_id,ClientRequest.cabinet_id==user.cabinet_id,ClientRequest.dossier_id==dossier_id))
            if not row: raise HTTPException(404,"Demande introuvable.")
            row.state="closed";audit(db,user,"request.closed",row.id,dossier_id);db.commit();return {"ok":True}

    @app.get("/api/dossiers/{dossier_id}/audit")
    def history(dossier_id: str,request: Request):
        with factory() as db:
            user=staff(db,request);scoped(db,user,dossier_id,{"manager","reviewer"})
            return [{key:getattr(row,key) for key in ("id","action","target_id","at","actor_id","details")} for row in
                db.scalars(select(Audit).where(Audit.cabinet_id==user.cabinet_id,Audit.dossier_id==dossier_id).order_by(Audit.at.desc()).limit(100))]

    @app.get("/api/knowledge/sources")
    def sources(request: Request):
        with factory() as db:
            user=staff(db,request)
            return [{"id":s.id,"authority":s.authority,"title":s.title,"url":s.url,
                     "versions":db.scalar(select(func.count()).select_from(SourceVersion).where(SourceVersion.source_id==s.id,SourceVersion.cabinet_id==user.cabinet_id))}
                    for s in db.scalars(select(Source).order_by(Source.id))]

    @app.get("/api/knowledge/versions")
    def versions(request: Request,q: str=Query(default="",max_length=100)):
        with factory() as db:
            user=staff(db,request)
            query=select(SourceVersion).where(SourceVersion.cabinet_id==user.cabinet_id).order_by(SourceVersion.captured_at.desc())
            if q: query=query.where(SourceVersion.title.icontains(q,autoescape=True))
            return [version_out(v) for v in db.scalars(query.limit(100))]

    @app.get("/api/knowledge/versions/{version_id}")
    def version(version_id: str,request: Request):
        with factory() as db:
            user=staff(db,request)
            row=db.scalar(select(SourceVersion).where(SourceVersion.id==version_id,SourceVersion.cabinet_id==user.cabinet_id))
            if not row: raise HTTPException(404,"Référence introuvable.")
            return version_out(row,True)

    @app.post("/api/knowledge/versions",status_code=201)
    def create_version(body: NewVersion,request: Request):
        with factory() as db:
            user=knowledge_editor(db,request);source=db.get(Source,body.source_id)
            try:
                url=urlsplit(body.url)
                valid=source and url.scheme=="https" and url.hostname==source.host and not url.username and not url.password and url.port in {None,443}
            except ValueError:
                valid=False
            if not valid:
                raise HTTPException(422,"Utilisez une adresse HTTPS de l’autorité officielle sélectionnée.")
            version=SourceVersion(cabinet_id=user.cabinet_id,**body.model_dump(),sha256=digest(body.text),created_by=user.id,captured_at=now())
            db.add(version);db.flush();audit(db,user,"reference.submitted",version.id,details={"sha256":version.sha256});db.commit()
            return version_out(version)

    @app.post("/api/knowledge/versions/{version_id}/review")
    def review_version(version_id: str,body: ReviewVersion,request: Request):
        with factory() as db:
            user=knowledge_editor(db,request)
            row=db.scalar(select(SourceVersion).where(SourceVersion.id==version_id,SourceVersion.cabinet_id==user.cabinet_id).with_for_update())
            if not row: raise HTTPException(404,"Référence introuvable.")
            if row.created_by==user.id: raise HTTPException(403,"La vérification nécessite un second responsable habilité.")
            if row.status!="draft": raise HTTPException(409,"Cette version a déjà été examinée. Créez une nouvelle version pour la corriger.")
            row.status,row.reviewed_by,row.review_note=body.decision,user.id,body.note
            audit(db,user,"reference.reviewed",row.id,details={"decision":body.decision,"sha256":row.sha256});db.commit();return version_out(row)

    @app.get("/api/dossiers/{dossier_id}/regulatory-readiness")
    def readiness(dossier_id: str,request: Request):
        with factory() as db: user=staff(db,request);scoped(db,user,dossier_id)
        # A verified text is not an executable legal rule. Never manufacture a green compliance score.
        return {"status":"blocked","code":"EXECUTABLE_RULESET_NOT_APPROVED",
                "message":"La finalisation comptable et fiscale reste bloquée tant que les règles applicables n’ont pas été implémentées, testées et validées.",
                "finalization_available":False}
    return app

app = create_app()
