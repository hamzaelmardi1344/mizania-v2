from datetime import date
from uuid import uuid4
from sqlalchemy import String, Integer, Boolean, Text, Date, JSON, ForeignKey, ForeignKeyConstraint, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

def uid(): return str(uuid4())
class Base(DeclarativeBase): pass
class Cabinet(Base):
    __tablename__ = "cabinets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(160))
class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("cabinet_id", "id"), CheckConstraint("kind in ('staff','client')"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    cabinet_id: Mapped[str] = mapped_column(ForeignKey("cabinets.id"))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(16), default="staff")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    cabinet_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    knowledge_editor: Mapped[bool] = mapped_column(Boolean, default=False)
class LoginSession(Base):
    __tablename__ = "sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    csrf: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[int] = mapped_column(Integer)
class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    key: Mapped[str] = mapped_column(String(64), index=True)
    at: Mapped[int] = mapped_column(Integer, index=True)
class Dossier(Base):
    __tablename__ = "dossiers"
    __table_args__ = (UniqueConstraint("cabinet_id", "id"), UniqueConstraint("cabinet_id", "code"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    cabinet_id: Mapped[str] = mapped_column(ForeignKey("cabinets.id"))
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(160))
    ice: Mapped[str] = mapped_column(String(15), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
class Assignment(Base):
    __tablename__ = "assignments"
    __table_args__ = (
        ForeignKeyConstraint(["cabinet_id", "dossier_id"], ["dossiers.cabinet_id", "dossiers.id"]),
        ForeignKeyConstraint(["cabinet_id", "user_id"], ["users.cabinet_id", "users.id"]),
        UniqueConstraint("user_id", "dossier_id"),
        CheckConstraint("role in ('manager','reviewer','collaborator','client')"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    cabinet_id: Mapped[str] = mapped_column(String(36))
    user_id: Mapped[str] = mapped_column(String(36))
    dossier_id: Mapped[str] = mapped_column(String(36))
    role: Mapped[str] = mapped_column(String(24))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
class Exercise(Base):
    __tablename__ = "exercises"
    __table_args__ = (ForeignKeyConstraint(["cabinet_id", "dossier_id"], ["dossiers.cabinet_id", "dossiers.id"]),
                     CheckConstraint("ends_on >= starts_on"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    cabinet_id: Mapped[str] = mapped_column(String(36))
    dossier_id: Mapped[str] = mapped_column(String(36))
    label: Mapped[str] = mapped_column(String(32))
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date] = mapped_column(Date)
    closed: Mapped[bool] = mapped_column(Boolean, default=False)
class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (ForeignKeyConstraint(["cabinet_id", "dossier_id"], ["dossiers.cabinet_id", "dossiers.id"]),
                     UniqueConstraint("cabinet_id", "dossier_id", "sha256"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    cabinet_id: Mapped[str] = mapped_column(String(36))
    dossier_id: Mapped[str] = mapped_column(String(36))
    uploaded_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column(String(200))
    media_type: Mapped[str] = mapped_column(String(80))
    sha256: Mapped[str] = mapped_column(String(64))
    size: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(32), default="documents")
    state: Mapped[str] = mapped_column(String(32), default="received")
    scan: Mapped[str] = mapped_column(String(24), default="pending")
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[int] = mapped_column(Integer)
class WorkItem(Base):
    __tablename__ = "work_items"
    __table_args__ = (ForeignKeyConstraint(["cabinet_id", "dossier_id"], ["dossiers.cabinet_id", "dossiers.id"]),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    cabinet_id: Mapped[str] = mapped_column(String(36))
    dossier_id: Mapped[str] = mapped_column(String(36))
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    reason: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(24), default="open")
class ClientRequest(Base):
    __tablename__ = "client_requests"
    __table_args__ = (ForeignKeyConstraint(["cabinet_id", "dossier_id"], ["dossiers.cabinet_id", "dossiers.id"]),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    cabinet_id: Mapped[str] = mapped_column(String(36))
    dossier_id: Mapped[str] = mapped_column(String(36))
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text)
    reply: Mapped[str] = mapped_column(Text, default="")
    state: Mapped[str] = mapped_column(String(24), default="open")
    created_at: Mapped[int] = mapped_column(Integer)
class Invitation(Base):
    __tablename__ = "invitations"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    cabinet_id: Mapped[str] = mapped_column(ForeignKey("cabinets.id"))
    dossier_id: Mapped[str] = mapped_column(ForeignKey("dossiers.id"))
    email: Mapped[str] = mapped_column(String(254))
    name: Mapped[str] = mapped_column(String(160))
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[int] = mapped_column(Integer)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)
class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    cabinet_id: Mapped[str] = mapped_column(String(36))
    dossier_id: Mapped[str] = mapped_column(String(36))
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), unique=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    state: Mapped[str] = mapped_column(String(24), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_at: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str] = mapped_column(String(64), default="")
class Source(Base):
    __tablename__ = "regulatory_sources"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    authority: Mapped[str] = mapped_column(String(160))
    title: Mapped[str] = mapped_column(String(160))
    url: Mapped[str] = mapped_column(Text)
    host: Mapped[str] = mapped_column(String(100))
class SourceVersion(Base):
    __tablename__ = "regulatory_versions"
    __table_args__ = (UniqueConstraint("cabinet_id", "source_id", "sha256"), CheckConstraint("effective_to is null or effective_to >= effective_from"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    cabinet_id: Mapped[str] = mapped_column(ForeignKey("cabinets.id"))
    source_id: Mapped[str] = mapped_column(ForeignKey("regulatory_sources.id"))
    title: Mapped[str] = mapped_column(String(200))
    citation: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    published_on: Mapped[date] = mapped_column(Date)
    captured_at: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), default="draft")
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    reviewed_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    review_note: Mapped[str] = mapped_column(Text, default="")
class Audit(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    cabinet_id: Mapped[str] = mapped_column(String(36), index=True)
    dossier_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    actor_id: Mapped[str] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(80))
    target_id: Mapped[str] = mapped_column(String(64))
    at: Mapped[int] = mapped_column(Integer)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
