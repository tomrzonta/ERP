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
