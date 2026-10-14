"""Initial dossier, session, document, outbox and regulatory schema.
Future revisions must use explicit alter operations; keep this baseline stable.
"""
from alembic import op
from app.models import Base
revision="0001"
down_revision=None
branch_labels=None
depends_on=None

def upgrade():
    connection=op.get_bind()
    Base.metadata.create_all(connection)
    if connection.dialect.name=="postgresql":
        op.execute("""CREATE FUNCTION deny_audit_changes() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN RAISE EXCEPTION 'audit events are append only'; END; $$""")
        op.execute("CREATE TRIGGER audit_immutable BEFORE UPDATE OR DELETE ON audit_events FOR EACH ROW EXECUTE FUNCTION deny_audit_changes()")
    else:
        for action in ("UPDATE","DELETE"):
            op.execute(f"CREATE TRIGGER audit_no_{action.lower()} BEFORE {action} ON audit_events BEGIN SELECT RAISE(ABORT, 'audit events are append only'); END")

def downgrade():
    raise RuntimeError("Destructive downgrade disabled. Restore a reviewed backup instead.")
