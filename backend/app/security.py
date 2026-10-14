import hashlib
import secrets
import time
from dataclasses import dataclass
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import User, LoginSession, Assignment, Dossier, Audit

hasher = PasswordHasher()
DUMMY_HASH = hasher.hash(secrets.token_urlsafe(32))
def digest(value: str) -> str: return hashlib.sha256(value.encode()).hexdigest()
def now() -> int: return int(time.time())
def password_hash(password: str) -> str: return hasher.hash(password)
def verify(password: str, hashed: str) -> bool:
    try: return hasher.verify(hashed, password)
    except (VerificationError, InvalidHashError): return False

def principal(request: Request, db: Session) -> tuple[User, LoginSession]:
    token = request.cookies.get("mizania_session", "")
    session = db.get(LoginSession, digest(token)) if token else None
    user = db.get(User, session.user_id) if session and session.expires_at > now() else None
    if not user or not user.active:
        raise HTTPException(401, "Votre session a expiré. Reconnectez-vous.")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        if not secrets.compare_digest(request.headers.get("x-csrf-token", ""), session.csrf):
            raise HTTPException(403, "Requête de sécurité invalide. Rechargez la page.")
    return user, session

def require_staff(user: User):
    if user.kind != "staff": raise HTTPException(403, "Accès réservé au cabinet.")

def scoped(db: Session, user: User, dossier_id: str, roles: set[str] | None = None) -> tuple[Dossier, Assignment]:
    pair = db.execute(select(Dossier, Assignment).join(Assignment,
        (Assignment.dossier_id == Dossier.id) & (Assignment.cabinet_id == Dossier.cabinet_id)).where(
        Dossier.id == dossier_id, Dossier.cabinet_id == user.cabinet_id, Dossier.active.is_(True),
        Assignment.user_id == user.id, Assignment.active.is_(True))).first()
    if not pair: raise HTTPException(404, "Dossier introuvable ou accès retiré.")
    dossier, assignment = pair
    if (user.kind == "client") != (assignment.role == "client"):
        raise HTTPException(404, "Dossier introuvable ou accès retiré.")
    if roles and assignment.role not in roles:
        raise HTTPException(403, "Cette action nécessite une habilitation supplémentaire.")
    return dossier, assignment

def audit(db: Session, user: User, action: str, target: str, dossier_id: str | None = None, details: dict | None = None):
    db.add(Audit(cabinet_id=user.cabinet_id, dossier_id=dossier_id, actor_id=user.id,
                 action=action, target_id=target, at=now(), details=details or {}))
