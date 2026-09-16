import pytest
from pydantic import ValidationError

from app.core.config import Settings


def criar(url: str) -> Settings:
    return Settings(database_url=url)


def test_troca_postgresql_por_psycopg():
    s = criar("postgresql://u:p@host:5432/db")
    assert s.database_url == "postgresql+psycopg://u:p@host:5432/db"


def test_troca_postgres_por_psycopg():
    s = criar("postgres://u:p@host:5432/db")
    assert s.database_url == "postgresql+psycopg://u:p@host:5432/db"


def test_mantem_url_ja_correta_e_remove_espacos():
    s = criar("  postgresql+psycopg://u:p@host:5432/db  ")
    assert s.database_url == "postgresql+psycopg://u:p@host:5432/db"


def test_recusa_colchetes_na_senha():
    with pytest.raises(ValidationError):
        criar("postgresql://u:[senha]@host:5432/db")


def test_recusa_mais_de_um_arroba():
    with pytest.raises(ValidationError):
        criar("postgresql://u:x@senha@host:5432/db")
