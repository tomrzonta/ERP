"""Conexão com o banco e sessão por requisição."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # descarta conexões mortas antes de usar
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Dependência do FastAPI: abre uma sessão por requisição e fecha no final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
