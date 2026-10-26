from functools import lru_cache
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from .config import settings


@lru_cache
def engine():
    url = settings().database_url
    e = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {}, pool_pre_ping=True)
    if url.startswith("sqlite"):
        @event.listens_for(e, "connect")
        def enable_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA busy_timeout=10000")
    return e


def session_factory():
    return sessionmaker(bind=engine(), expire_on_commit=False)


def get_db():
    with session_factory()() as db:
        try:
            yield db
            db.commit()
            db.info.pop("created_files", None)
        except Exception:
            db.rollback()
            for path in db.info.pop("created_files", []):
                path.unlink(missing_ok=True)
            raise
