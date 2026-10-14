"""Durable background document intake. No invented OCR, tax rate or journal entry."""
import hashlib
import socket
import struct
from fastapi import HTTPException
from sqlalchemy import select
from .models import Job, Document, User, WorkItem
from .security import scoped, now, audit

def clam_scan(path, host: str, port: int) -> bool:
    if not host: raise ConnectionError("scanner_not_configured")
    with socket.create_connection((host,port),timeout=15) as sock:
        sock.sendall(b"zINSTREAM\0")
        with path.open("rb") as stream:
            while chunk:=stream.read(65536): sock.sendall(struct.pack("!I",len(chunk))+chunk)
        sock.sendall(struct.pack("!I",0))
        response=bytearray()
        while len(response)<8192:
            chunk=sock.recv(1024)
            if not chunk: break
            response.extend(chunk)
            if b"\0" in chunk: break
        answer=bytes(response).rstrip(b"\0\n")
        if answer.endswith(b" OK"): return True
        if answer.endswith(b" FOUND"): return False
        raise ConnectionError("scanner_unavailable")

def process_job(factory, settings, job_id: str, scanner=clam_scan):
    with factory() as db:
        job=db.scalar(select(Job).where(Job.id==job_id).with_for_update(skip_locked=True))
        if not job or job.state in {"done","cancelled","failed"} or job.next_at>now(): return
        user=db.get(User,job.actor_id)
        try:
            if not user or not user.active: raise HTTPException(403)
            scoped(db,user,job.dossier_id)
            if user.cabinet_id!=job.cabinet_id: raise HTTPException(403)
        except HTTPException:
            job.state="cancelled";job.error_code="ACCESS_REVOKED";db.commit();return
        doc=db.scalar(select(Document).where(Document.id==job.document_id,Document.cabinet_id==job.cabinet_id,
                      Document.dossier_id==job.dossier_id))
        if not doc:
            job.state="failed";job.error_code="DOCUMENT_SCOPE_MISMATCH";db.commit();return
        job.attempts+=1
        path=settings.storage/job.cabinet_id/job.dossier_id/doc.id
        try:
            intact=path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==doc.sha256
            if not intact:
                doc.scan="rejected";doc.state="blocked";job.state="failed";job.error_code="INTEGRITY_FAILURE"
                audit(db,user,"document.integrity_failed",doc.id,doc.dossier_id);db.commit();return
            clean=scanner(path,settings.clamav_host,settings.clamav_port)
        except (OSError,TimeoutError,ConnectionError):
            job.state="pending" if job.attempts<8 else "failed"
            job.next_at=now()+min(2**job.attempts*15,1800)
            job.error_code="SCANNER_UNAVAILABLE";db.commit();return
        doc.scan="clean" if clean else "rejected"
        doc.state="review" if clean else "blocked"
        job.state="done"
        db.add(WorkItem(cabinet_id=job.cabinet_id,dossier_id=job.dossier_id,document_id=doc.id,
            title="Pièce à qualifier" if clean else "Document bloqué",
            reason="Le fichier a été reçu et contrôlé. La qualification comptable reste à effectuer." if clean else "Le contrôle de sécurité a bloqué ce fichier. Demandez une nouvelle pièce."))
        audit(db,user,"document.checked",doc.id,doc.dossier_id,{"scan":doc.scan});db.commit()
