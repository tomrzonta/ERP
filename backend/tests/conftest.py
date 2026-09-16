"""Fixtures compartilhadas pelos testes."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.core.models_registry  # noqa: F401
from app.core.database import engine, get_db
from app.main import app


@pytest.fixture
def db():
    """Sessão de banco isolada por teste.

    Tudo roda dentro de uma transação desfeita no final, então os testes
    não deixam dados para trás, mesmo quando as rotas fazem commit.
    Requer as migrações aplicadas.
    """
    conexao = engine.connect()
    transacao = conexao.begin()
    sessao = Session(bind=conexao, join_transaction_mode="create_savepoint")
    try:
        yield sessao
    finally:
        sessao.close()
        transacao.rollback()
        conexao.close()


@pytest.fixture
def cliente(db):
    """Cliente HTTP da API usando a sessão isolada do teste."""
    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
