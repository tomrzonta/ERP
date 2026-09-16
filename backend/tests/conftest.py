"""Fixtures compartilhadas pelos testes."""

import pytest
from sqlalchemy.orm import Session

import app.core.models_registry  # noqa: F401
from app.core.database import engine


@pytest.fixture
def db():
    """Sessão de banco isolada por teste.

    Tudo roda dentro de uma transação desfeita no final, então os testes
    não deixam dados para trás. Requer as migrações aplicadas.
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
