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


def test_filtros_de_insumo_e_vendaveis_separam_as_telas(db):
    empresa_id = criar_empresa(db)
    # Vendável e insumo ao mesmo tempo: aparece nas duas telas, sem duplicar cadastro
    service.criar_produto(db, empresa_id, nome="Vaso", unidade_codigo="un", insumo=True)
    service.criar_produto(
        db, empresa_id, nome="Filamento", unidade_codigo="g", vendavel=False, insumo=True
    )
    service.criar_produto(db, empresa_id, nome="Kit vaso", unidade_codigo="un", tipo=TipoProduto.KIT)

    repo = ProdutoRepositorio(db, empresa_id)
    assert {p.nome for p in repo.buscar(apenas_vendaveis=True, tipo=TipoProduto.SIMPLES)} == {"Vaso"}
    assert {p.nome for p in repo.buscar(apenas_insumos=True)} == {"Vaso", "Filamento"}
    assert {p.nome for p in repo.buscar(tipo=TipoProduto.KIT)} == {"Kit vaso"}


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


def test_custo_medio_pode_ser_corrigido_manualmente(db):
    """Ex.: o fornecedor reajustou o preço do insumo, sem entrada de estoque nova."""
    empresa_id = criar_empresa(db)
    filamento = service.criar_produto(
        db, empresa_id, nome="Filamento", unidade_codigo="g", vendavel=False, insumo=True,
        custo=Decimal("0.10"),
    )
    atualizado = service.atualizar_produto(
        db, empresa_id, filamento.id, {"custo_medio": Decimal("0.135")}
    )
    assert atualizado.custo_medio == Decimal("0.135000")


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


def test_kit_sempre_controla_estoque_proprio(db):
    empresa_id = criar_empresa(db)
    kit = service.criar_produto(
        db, empresa_id, nome="Kit vaso", unidade_codigo="un", tipo=TipoProduto.KIT,
        controla_estoque=False,  # ignorado: kit sempre controla o próprio estoque
    )
    assert kit.controla_estoque is True


def test_limite_de_kits_do_plano(db):
    from app.modules.assinaturas.models import PlanoRegra
    from app.modules.assinaturas.regras import PLANO_PRO
    from app.modules.assinaturas.repository import plano_por_codigo

    empresa_id = criar_empresa(db)
    pro = plano_por_codigo(db, PLANO_PRO)
    regra = db.get(PlanoRegra, (pro.id, "max_compostos"))
    regra.valor = 1
    db.flush()

    service.criar_produto(db, empresa_id, nome="Kit 1", unidade_codigo="un", tipo=TipoProduto.KIT)
    with pytest.raises(LimiteDoPlano):
        service.criar_produto(db, empresa_id, nome="Kit 2", unidade_codigo="un", tipo=TipoProduto.KIT)


def test_controla_estoque_de_kit_nao_e_editavel(db):
    empresa_id = criar_empresa(db)
    kit = service.criar_produto(db, empresa_id, nome="Kit", unidade_codigo="un", tipo=TipoProduto.KIT)
    with pytest.raises(RegraDeNegocio):
        service.atualizar_produto(db, empresa_id, kit.id, {"controla_estoque": False})


def test_uso_dos_limites_do_plano_pela_api(cliente, db):
    from app.modules.assinaturas.models import PlanoRegra
    from app.modules.assinaturas.regras import PLANO_PRO
    from app.modules.assinaturas.repository import plano_por_codigo
    from tests.test_auth import cabecalho, cadastrar

    # No Pro os limites são ilimitados; forçamos um teto de 4 pra ver o percentual.
    pro = plano_por_codigo(db, PLANO_PRO)
    db.get(PlanoRegra, (pro.id, "max_produtos_simples")).valor = 4
    db.flush()

    cab = cabecalho(cadastrar(cliente)["tokens"]["access_token"])
    for nome in ("A", "B", "C"):
        cliente.post(
            "/api/v1/produtos", headers=cab, json={"nome": f"Produto {nome}", "unidade_codigo": "un"}
        )

    resposta = cliente.get("/api/v1/assinatura/uso", headers=cab)

    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    produtos = next(item for item in corpo["limites"] if item["chave"] == "max_produtos_simples")
    assert (produtos["usado"], produtos["limite"]) == (3, 4)
    assert float(produtos["percentual"]) == 75.0
    kits = next(item for item in corpo["limites"] if item["chave"] == "max_compostos")
    assert kits["usado"] == 0 and kits["limite"] is None and kits["percentual"] is None
