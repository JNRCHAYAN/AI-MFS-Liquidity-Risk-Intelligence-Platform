"""Database engine and session lifecycle.

This is the only module that constructs an engine or a session. Repositories
receive a ``Session`` and never create one.

There is **no SQLite fallback**: the schema uses PostgreSQL-only types (JSONB)
and the target is a managed PostgreSQL instance. If ``DATABASE_URL`` is unset,
:func:`get_engine` raises the typed ``Unavailable`` error instead of silently
connecting to some other database.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.errors import Unavailable

#: Statement used by readiness checks. Cheap and side-effect free.
_LIVENESS_SQL = text("SELECT 1")


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Return the process-wide engine, or raise if the database is unconfigured.

    ``pool_pre_ping`` avoids handing out connections that a managed provider
    has already closed.
    """
    database_url = get_settings().database_url
    if not database_url:
        raise Unavailable(
            "DATABASE_URL is not configured; the database is unavailable.",
            details={"dependency": "database"},
        )
    return create_engine(database_url, pool_pre_ping=True, future=True)


@lru_cache(maxsize=1)
def get_sessionmaker() -> sessionmaker[Session]:
    """Return the process-wide session factory.

    ``expire_on_commit=False`` keeps ORM objects readable after a commit so a
    repository can return an object that outlives its session. It does **not**
    populate relationships: model relationships are declared ``lazy="raise"``
    on purpose, so accessing one forces an explicit, bounded eager-load in a
    repository method rather than a surprise query.
    """
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        expire_on_commit=False,
        future=True,
    )


@contextmanager
def session_scope() -> Iterator[Session]:
    """Run a unit of work in an explicit transaction.

    Commits on success, rolls back on any exception (which is re-raised, never
    swallowed), and always closes the session.
    """
    session = get_sessionmaker()()
    try:
        yield session
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


def database_is_ready() -> tuple[bool, str | None]:
    """Check database reachability for the readiness endpoint.

    Returns ``(True, None)`` when reachable, else ``(False, reason)``. Only
    SQLAlchemy errors and a missing configuration are treated as "not ready";
    an unexpected exception propagates so it is not silently hidden.
    """
    try:
        engine = get_engine()
        with engine.connect() as connection:
            connection.execute(_LIVENESS_SQL)
    except Unavailable as exc:
        return False, exc.code
    except SQLAlchemyError as exc:
        return False, type(exc).__name__
    return True, None
