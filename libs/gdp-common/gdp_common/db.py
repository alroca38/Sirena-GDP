# DB.PY
from __future__ import annotations
 
import os
from collections.abc import Iterator
from functools import lru_cache
 
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, sessionmaker

##########################
ENV_DB_URL = "DB_URL"
_SQLSTATE_UNICIDAD = "23505"
##########################

def _normalizeUrl(url: str) -> str:
    parsed = make_url(url)
    if parsed.drivername in ("postgresql", "postgres"):
        parsed = parsed.set(drivername="postgresql+psycopg")
    return parsed.render_as_string(hide_password=False)

@lru_cache(maxsize=1)
def getEngine() -> Engine:
    url = os.environ.get(ENV_DB_URL)
    if not url and any(k in os.environ for k in ("POSTGRES_USER", "POSTGRES_DB", "POSTGRES_HOST")):
        user = os.environ.get("POSTGRES_USER", "postgres")
        password = os.environ.get("POSTGRES_PASSWORD", "postgres")
        host = os.environ.get("POSTGRES_HOST", "postgres")
        port = os.environ.get("POSTGRES_PORT", "5432")
        db = os.environ.get("POSTGRES_DB", "sirena")
        url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"
    if not url:
        raise RuntimeError(f"Falta la variable de entorno {ENV_DB_URL}")
    return create_engine(
        _normalizeUrl(url),
        pool_pre_ping=True,       # descarta conexiones muertas (p. ej. tras reiniciar postgres)
        pool_size=5,
        max_overflow=5,
    )

@lru_cache(maxsize=1)
def getSessionFactory() -> sessionmaker[Session]:
    # expire_on_commit=False: los objetos siguen legibles después del commit.
    return sessionmaker(bind=getEngine(), expire_on_commit=False)

def session() -> Iterator[Session]:
    with getSessionFactory()() as s:
        yield s

def isUniquenessViolation(exc: BaseException) -> bool:
    if not isinstance(exc, DBAPIError):
        return False
    return getattr(exc.orig, "sqlstate", None) == _SQLSTATE_UNICIDAD

def restartEngine() -> None:
    if getEngine.cache_info().currsize:
        getEngine().dispose()
    getSessionFactory.cache_clear()
    getEngine.cache_clear()