from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings

_engine = None


def _get_engine() -> object:
    global _engine
    if _engine is None:
        _engine = create_engine(get_settings().database_url, echo=False)
    return _engine


def init_db() -> None:
    SQLModel.metadata.create_all(_get_engine())


def get_session() -> Generator[Session, None, None]:
    with Session(_get_engine()) as session:
        yield session
