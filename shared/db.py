from __future__ import annotations

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from shared.settings import get_settings


def create_db_engine() -> Engine:
    # psycopg3 + SQLAlchemy 2.x
    url = get_settings().database_url
    return create_engine(url, pool_pre_ping=True)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


@contextmanager
def session_scope(session_factory: sessionmaker[Session]):
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

