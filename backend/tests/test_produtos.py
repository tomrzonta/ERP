import uuid
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.core.exceptions import Conflito, LimiteDoPlano, NaoEncontrado, RegraDeNegocio
from app.modules.empresas.service import criar_empresa_com_padroes
from app.modules.produtos import service
from app.modules.produtos.models import Produto, TipoProduto, UnidadeMedida
from app.modules.produtos.repository import ProdutoRepositorio
from app.modules.produtos.unidades import UNIDADES
from app.modules.usuarios.models import Usuario


def criar_empresa(db):
    usuario = Usuario(nome="Dona", email=f"{uuid.uuid4().hex[:8]}@exemplo.com", senha_hash="x")
    db.add(usuario)
    db.flush()
    criada = criar_empresa_com_padroes(
        db, nome_fantasia=f"Loja {uuid.uuid4().hex[:6]}", usuario_dono_id=usuario.id
    )
    return criada.empresa.id


def test_catalogo_de_unidades_confere_com_o_banco(db):
    no_banco = {u.codigo: u for u in db.scalars(select(UnidadeMedida))}
    assert set(no_banco) == set(UNIDADES)
    for codigo, esperado in UNIDADES.items():
        assert no_banco[codigo].grandeza == esperado.grandeza
        assert no_banco[codigo].fator_canonico == esperado.fator_canonico


def test_cria_produto_com_sku_gerado(db):
    empresa_id = criar_empresa(db)
    produto = service.criar_produto(
        db, empresa_id, nome="Vaso impresso", unidade_codigo="un", preco_venda=Decimal("42.00")
    )
    assert produto.sku == "PRD-0001"
    assert produto.tipo is TipoProduto.SIMPLES
    assert produto.vendavel is True

    segundo = service.criar_produto(db, empresa_id, nome="Suculenta", unidade_codigo="un")
    assert segundo.sku == "PRD-0002"


def test_insumo_em_gramas_com_custo(db):
    empresa_id = criar_empresa(db)
    filamento = service.criar_produto(
        db,
        empresa_id,
        nome="Filamento PLA",
        unidade_codigo="g",
        vendavel=False,
        insumo=True,
        custo=Decimal("0.1205"),
    )
    assert filamento.unidade_codigo == "g"
    assert filamento.custo_medio == Decimal("0.120500")
    assert service.margem_percentual(filamento) is None


def test_margem_usa_custo_medio(db):
    empresa_id = criar_empresa(db)
    produto = service.criar_produto(
        db,
        empresa_id,
        nome="Caneca",
        unidade_codigo="un",
        preco_venda=Decimal("100.00"),
        custo=Decimal("60"),
    )
    assert service.margem_percentual(produto) == Decimal("40.00")


def test_sku_duplicado_e_recusado(db):
    empresa_id = criar_empresa(db)
    service.criar_produto(db, empresa_id, nome="Vaso", unidade_codigo="un", sku="vaso-01")
    with pytest.raises(Conflito):
        service.criar_produto(db, empresa_id, nome="Outro", unidade_codigo="un", sku="VASO-01")


def test_mesmo_sku_em_empresas_diferentes_e_permitido(db):
    primeira = criar_empresa(db)
    segunda = criar_empresa(db)
    service.criar_produto(db, primeira, nome="Vaso", unidade_codigo="un", sku="VASO-01")
    service.criar_produto(db, segunda, nome="Vaso", unidade_codigo="un", sku="VASO-01")


def test_produto_precisa_ser_vendavel_ou_insumo(db):
    empresa_id = criar_empresa(db)
    with pytest.raises(RegraDeNegocio):
        service.criar_produto(
            db, empresa_id, nome="Nada", unidade_codigo="un", vendavel=False, insumo=False
        )


def test_unidade_desconhecida_e_recusada(db):
    empresa_id = criar_empresa(db)
    with pytest.raises(RegraDeNegocio):
        service.criar_produto(db, empresa_id, nome="Bolo", unidade_codigo="fatia")


def test_categoria_de_outra_empresa_nao_e_encontrada(db):
    primeira = criar_empresa(db)
    segunda = criar_empresa(db)
    categoria = service.criar_categoria(db, primeira, nome="Vasos")
    with pytest.raises(NaoEncontrado):
        service.criar_produto(
            db, segunda, nome="Vaso", unidade_codigo="un", categoria_id=categoria.id
        )


def test_categoria_repetida_e_recusada(db):
    empresa_id = criar_empresa(db)
    service.criar_categoria(db, empresa_id, nome="Vasos")
    with pytest.raises(Conflito):
        service.criar_categoria(db, empresa_id, nome="vasos")


def test_busca_por_nome_sku_e_codigo_de_barras(db):
    empresa_id = criar_empresa(db)
    service.criar_produto(
        db, empresa_id, nome="Vaso hexagonal", unidade_codigo="un", codigo_barras="7890001"
    )
    service.criar_produto(db, empresa_id, nome="Suculenta", unidade_codigo="un")

    repo = ProdutoRepositorio(db, empresa_id)
    assert len(repo.buscar(termo="hexa")) == 1
    assert len(repo.buscar(termo="7890001")) == 1
    assert len(repo.buscar(termo="PRD-000")) == 2
    assert len(repo.buscar()) == 2


def test_produtos_de_outra_empresa_nao_aparecem(db):
    primeira = criar_empresa(db)
    segunda = criar_empresa(db)
    produto = service.criar_produto(db, primeira, nome="Vaso", unidade_codigo="un")

    assert ProdutoRepositorio(db, segunda).buscar() == []
    with pytest.raises(NaoEncontrado):
        service.obter_produto(db, segunda, produto.id)


def test_atualiza_preco_e_publicacao(db):
    empresa_id = criar_empresa(db)
    produto = service.criar_produto(db, empresa_id, nome="Vaso", unidade_codigo="un")
    atualizado = service.atualizar_produto(
        db,
        empresa_id,
        produto.id,
        {"preco_venda": Decimal("49.90"), "publicado_na_vitrine": True},
    )
    assert atualizado.preco_venda == Decimal("49.90")
    assert atualizado.publicado_na_vitrine is True


def test_unidades_alternativas_do_produto(db):
    empresa_id = criar_empresa(db)
    bolo = service.criar_produto(db, empresa_id, nome="Bolo de cenoura", unidade_codigo="un")
    fatia = service.adicionar_unidade(
        db, empresa_id, bolo.id, nome="Fatia", fator=Decimal("0.125"), usa_na_compra=False
    )
    assert fatia.fator == Decimal("0.125000")

    with pytest.raises(Conflito):
        service.adicionar_unidade(db, empresa_id, bolo.id, nome="fatia", fator=Decimal("0.2"))
    with pytest.raises(RegraDeNegocio):
        service.adicionar_unidade(db, empresa_id, bolo.id, nome="Caixa", fator=Decimal("0"))

    assert len(service.listar_unidades(db, empresa_id, bolo.id)) == 1


def test_limite_de_produtos_do_plano_base(db):
    """No Base o limite é 200; forçamos o cenário reduzindo o limite do plano."""
    from app.modules.assinaturas.models import PlanoRegra, TipoRegra
    from app.modules.assinaturas.repository import plano_por_codigo
    from app.modules.assinaturas.regras import PLANO_PRO

    empresa_id = criar_empresa(db)
    pro = plano_por_codigo(db, PLANO_PRO)
    regra = db.get(PlanoRegra, (pro.id, "max_produtos_simples"))
    assert regra.tipo is TipoRegra.LIMITE
    regra.valor = 1
    db.flush()

    service.criar_produto(db, empresa_id, nome="Primeiro", unidade_codigo="un")
    with pytest.raises(LimiteDoPlano):
        service.criar_produto(db, empresa_id, nome="Segundo", unidade_codigo="un")


def test_composto_ainda_nao_pode_ser_criado(db):
    empresa_id = criar_empresa(db)
    with pytest.raises(RegraDeNegocio):
        service.criar_produto(
            db, empresa_id, nome="Kit", unidade_codigo="un", tipo=TipoProduto.COMPOSTO
        )
