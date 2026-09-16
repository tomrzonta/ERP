import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.acesso.models import Membro, Papel, PapelPermissao, StatusMembro
from app.modules.empresas.models import Empresa
from app.modules.usuarios.models import Usuario


def criar_empresa(db, nome="Loja"):
    empresa = Empresa(nome_fantasia=nome, slug=f"{nome.lower()}-{uuid.uuid4().hex[:8]}")
    db.add(empresa)
    db.flush()
    return empresa


def criar_usuario(db, email=None):
    usuario = Usuario(
        nome="Pessoa",
        email=email or f"{uuid.uuid4().hex[:8]}@exemplo.com",
        senha_hash="hash-de-teste",
    )
    db.add(usuario)
    db.flush()
    return usuario


def criar_papel(db, empresa, nome="Caixa"):
    papel = Papel(empresa_id=empresa.id, nome=nome)
    db.add(papel)
    db.flush()
    return papel


def test_cria_membro_com_papel_da_mesma_empresa(db):
    empresa = criar_empresa(db)
    usuario = criar_usuario(db)
    papel = criar_papel(db, empresa)

    membro = Membro(empresa_id=empresa.id, usuario_id=usuario.id, papel_id=papel.id)
    db.add(membro)
    db.flush()
    db.refresh(membro)

    assert membro.status == StatusMembro.ATIVO
    assert empresa.fuso_horario == "America/Sao_Paulo"


def test_mesmo_usuario_em_duas_empresas(db):
    usuario = criar_usuario(db)
    for nome in ("LojaA", "LojaB"):
        empresa = criar_empresa(db, nome)
        papel = criar_papel(db, empresa)
        db.add(Membro(empresa_id=empresa.id, usuario_id=usuario.id, papel_id=papel.id))
    db.flush()


def test_recusa_papel_de_outra_empresa(db):
    empresa_a = criar_empresa(db, "LojaA")
    empresa_b = criar_empresa(db, "LojaB")
    usuario = criar_usuario(db)
    papel_de_a = criar_papel(db, empresa_a)

    db.add(Membro(empresa_id=empresa_b.id, usuario_id=usuario.id, papel_id=papel_de_a.id))
    with pytest.raises(IntegrityError):
        db.flush()


def test_recusa_email_duplicado(db):
    criar_usuario(db, "repetido@exemplo.com")
    with pytest.raises(IntegrityError):
        criar_usuario(db, "repetido@exemplo.com")


def test_recusa_usuario_duas_vezes_na_mesma_empresa(db):
    empresa = criar_empresa(db)
    usuario = criar_usuario(db)
    papel = criar_papel(db, empresa)
    db.add(Membro(empresa_id=empresa.id, usuario_id=usuario.id, papel_id=papel.id))
    db.flush()

    db.add(Membro(empresa_id=empresa.id, usuario_id=usuario.id, papel_id=papel.id))
    with pytest.raises(IntegrityError):
        db.flush()


def test_permissao_repetida_no_mesmo_papel_e_recusada(db):
    empresa = criar_empresa(db)
    papel = criar_papel(db, empresa)
    db.add(PapelPermissao(papel_id=papel.id, permissao="vendas.criar"))
    db.flush()

    # Remove da sessão para que a checagem aconteça no banco, não na memória
    db.expunge_all()
    db.add(PapelPermissao(papel_id=papel.id, permissao="vendas.criar"))
    with pytest.raises(IntegrityError):
        db.flush()
