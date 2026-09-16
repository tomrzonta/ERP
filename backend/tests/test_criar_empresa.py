import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.exceptions import LimiteDoPlano, RecursoDoPlano
from app.core.permissions import catalogo
from app.modules.acesso import service as acesso_service
from app.modules.acesso.models import Papel, StatusMembro
from app.modules.acesso.papeis_padrao import PAPEIS_PADRAO
from app.modules.assinaturas import repository as assinaturas_repository
from app.modules.assinaturas import service as assinaturas
from app.modules.assinaturas.models import StatusAssinatura, TipoRegra
from app.modules.assinaturas.regras import DIAS_TRIAL, PLANO_BASE, PLANO_PRO, Limite, Recurso
from app.modules.empresas.service import criar_empresa_com_padroes
from app.modules.usuarios.models import Usuario

AGORA = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)
APOS_TRIAL = AGORA + timedelta(days=DIAS_TRIAL + 1)


def criar_usuario(db):
    usuario = Usuario(nome="Dona", email=f"{uuid.uuid4().hex[:8]}@exemplo.com", senha_hash="x")
    db.add(usuario)
    db.flush()
    return usuario


def criar(db, nome=None):
    nome = nome or f"Loja Teste {uuid.uuid4().hex[:6]}"
    return criar_empresa_com_padroes(
        db, nome_fantasia=nome, usuario_dono_id=criar_usuario(db).id, agora=AGORA
    )


def test_planos_cobrem_todos_os_recursos_e_limites(db):
    base = assinaturas_repository.plano_por_codigo(db, PLANO_BASE)
    pro = assinaturas_repository.plano_por_codigo(db, PLANO_PRO)
    assert base and pro

    for plano in (base, pro):
        for limite in Limite:
            regra = assinaturas_repository.regra(db, plano.id, limite.value)
            assert regra is not None and regra.tipo == TipoRegra.LIMITE, (plano.codigo, limite)

    for recurso in Recurso:
        assert assinaturas_repository.regra(db, pro.id, recurso.value) is not None, recurso
        assert assinaturas_repository.regra(db, base.id, recurso.value) is None, recurso


def test_cria_empresa_com_papeis_dono_e_trial(db):
    criada = criar(db)

    papeis = db.query(Papel).filter(Papel.empresa_id == criada.empresa.id).all()
    assert {papel.codigo_padrao for papel in papeis} == {p.codigo for p in PAPEIS_PADRAO}

    assert criada.dono.status == StatusMembro.ATIVO
    assert criada.assinatura.status == StatusAssinatura.TRIAL
    assert criada.assinatura.trial_termina_em == AGORA + timedelta(days=DIAS_TRIAL)


def test_dono_tem_todas_as_permissoes_e_caixa_nao(db):
    criada = criar(db)
    papeis = {
        papel.codigo_padrao: papel
        for papel in db.query(Papel).filter(Papel.empresa_id == criada.empresa.id)
    }
    assert acesso_service.permissoes_do_papel(db, papeis["dono"]) == frozenset(catalogo())
    assert "papeis.gerenciar" not in acesso_service.permissoes_do_papel(db, papeis["gerente"])
    assert acesso_service.permissoes_do_papel(db, papeis["caixa"]) == frozenset()


def test_slug_repetido_ganha_sufixo(db):
    nome = f"Loja Repetida {uuid.uuid4().hex[:6]}"
    primeira = criar(db, nome)
    segunda = criar(db, nome)
    assert segunda.empresa.slug == f"{primeira.empresa.slug}-2"


def test_durante_trial_tem_recursos_do_pro(db):
    empresa_id = criar(db).empresa.id
    assert assinaturas.plano_efetivo(db, empresa_id, AGORA).codigo == PLANO_PRO
    assert assinaturas.tem_recurso(db, empresa_id, Recurso.CUPONS, AGORA)
    assert assinaturas.valor_do_limite(db, empresa_id, Limite.MAX_COMPOSTOS, AGORA) is None


def test_apos_trial_cai_para_base_com_limites(db):
    empresa_id = criar(db).empresa.id
    assert assinaturas.plano_efetivo(db, empresa_id, APOS_TRIAL).codigo == PLANO_BASE
    assert not assinaturas.tem_recurso(db, empresa_id, Recurso.CUPONS, APOS_TRIAL)

    with pytest.raises(RecursoDoPlano):
        assinaturas.exigir_recurso(db, empresa_id, Recurso.CUPONS, APOS_TRIAL)

    assinaturas.verificar_limite(db, empresa_id, Limite.MAX_COMPOSTOS, 4, APOS_TRIAL)
    with pytest.raises(LimiteDoPlano):
        assinaturas.verificar_limite(db, empresa_id, Limite.MAX_COMPOSTOS, 5, APOS_TRIAL)
