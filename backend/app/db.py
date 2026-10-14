from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from .config import Settings

def make_database(settings: Settings):
    settings.storage.mkdir(parents=True, exist_ok=True)
    engine = create_engine(settings.database_url, pool_pre_ping=True,
                           connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {})
    if engine.dialect.name == "sqlite":
        @event.listens_for(engine, "connect")
        def configure(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA busy_timeout=5000")
    return engine, sessionmaker(engine, expire_on_commit=False)

def get_db(request):
    with request.app.state.db() as db:
        yield db
