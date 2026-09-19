import uuid
from decimal import Decimal

import pytest

from app.core.exceptions import Conflito, NaoEncontrado, RecursoDoPlano, RegraDeNegocio
from app.modules.composicao import service as composicao_service
from app.modules.empresas.service import criar_empresa_com_padroes
from app.modules.estoque import service as estoque_service
from app.modules.produtos import service as produtos_service
from app.modules.produtos.models import TipoProduto
from app.modules.usuarios.models import Usuario


def criar_empresa(db):
    usuario = Usuario(nome="Dona", email=f"{uuid.uuid4().hex[:8]}@exemplo.com", senha_hash="x")
    db.add(usuario)
    db.flush()
    criada = criar_empresa_com_padroes(
        db, nome_fantasia=f"Loja {uuid.uuid4().hex[:6]}", usuario_dono_id=usuario.id
    )
    return criada.empresa.id


def criar_simples(db, empresa_id, nome, **kwargs):
    kwargs.setdefault("unidade_codigo", "un")
    return produtos_service.criar_produto(db, empresa_id, nome=nome, **kwargs)


def criar_kit(db, empresa_id, nome="Kit"):
    return produtos_service.criar_produto(
        db, empresa_id, nome=nome, unidade_codigo="un", tipo=TipoProduto.KIT
    )


def test_adicionar_e_listar_componentes(db):
    empresa_id = criar_empresa(db)
    kit = criar_kit(db, empresa_id)
    suculenta = criar_simples(db, empresa_id, "Suculenta")

    componente = composicao_service.adicionar_componente(
        db, empresa_id, kit.id, componente_id=suculenta.id, quantidade=Decimal("1")
    )
    assert componente.quantidade == Decimal("1.0000")

    componentes = composicao_service.listar_componentes(db, empresa_id, kit.id)
    assert len(componentes) == 1


def test_componente_duplicado_e_recusado(db):
    empresa_id = criar_empresa(db)
    kit = criar_kit(db, empresa_id)
    suculenta = criar_simples(db, empresa_id, "Suculenta")
    composicao_service.adicionar_componente(
        db, empresa_id, kit.id, componente_id=suculenta.id, quantidade=Decimal("1")
    )
    with pytest.raises(Conflito):
        composicao_service.adicionar_componente(
            db, empresa_id, kit.id, componente_id=suculenta.id, quantidade=Decimal("2")
        )


def test_produto_simples_nao_pode_ter_componentes(db):
    empresa_id = criar_empresa(db)
    simples = criar_simples(db, empresa_id, "Vaso")
    outro = criar_simples(db, empresa_id, "Suculenta")
    with pytest.raises(RegraDeNegocio):
        composicao_service.adicionar_componente(
            db, empresa_id, simples.id, componente_id=outro.id, quantidade=Decimal("1")
        )


def test_componente_sem_controle_de_estoque_e_recusado(db):
    empresa_id = criar_empresa(db)
    kit = criar_kit(db, empresa_id)
    servico = criar_simples(db, empresa_id, "Mão de obra", controla_estoque=False)
    with pytest.raises(RegraDeNegocio):
        composicao_service.adicionar_componente(
            db, empresa_id, kit.id, componente_id=servico.id, quantidade=Decimal("1")
        )


def test_remover_componente(db):
    empresa_id = criar_empresa(db)
    kit = criar_kit(db, empresa_id)
    suculenta = criar_simples(db, empresa_id, "Suculenta")
    composicao_service.adicionar_componente(
        db, empresa_id, kit.id, componente_id=suculenta.id, quantidade=Decimal("1")
    )

    composicao_service.remover_componente(db, empresa_id, kit.id, suculenta.id)
    assert composicao_service.listar_componentes(db, empresa_id, kit.id) == []

    with pytest.raises(NaoEncontrado):
        composicao_service.remover_componente(db, empresa_id, kit.id, suculenta.id)


def test_kit_aninhado_exige_recurso_composto_aninhado(db):
    empresa_id = criar_empresa(db)
    kit_externo = criar_kit(db, empresa_id, "Kit externo")
    kit_interno = criar_kit(db, empresa_id, "Kit interno")

    from app.modules.assinaturas.models import PlanoRegra
    from app.modules.assinaturas.regras import PLANO_PRO, Recurso
    from app.modules.assinaturas.repository import plano_por_codigo

    pro = plano_por_codigo(db, PLANO_PRO)
    db.delete(db.get(PlanoRegra, (pro.id, Recurso.COMPOSTO_ANINHADO.value)))
    db.flush()

    with pytest.raises(RecursoDoPlano):
        composicao_service.adicionar_componente(
            db, empresa_id, kit_externo.id, componente_id=kit_interno.id, quantidade=Decimal("1")
        )


def test_ciclo_de_composicao_e_bloqueado(db):
    empresa_id = criar_empresa(db)
    kit_a = criar_kit(db, empresa_id, "Kit A")
    kit_b = criar_kit(db, empresa_id, "Kit B")

    composicao_service.adicionar_componente(
        db, empresa_id, kit_a.id, componente_id=kit_b.id, quantidade=Decimal("1")
    )
    with pytest.raises(RegraDeNegocio):
        composicao_service.adicionar_componente(
            db, empresa_id, kit_b.id, componente_id=kit_a.id, quantidade=Decimal("1")
        )


def test_kit_pode_ter_outro_kit_como_componente(db):
    empresa_id = criar_empresa(db)
    kit_externo = criar_kit(db, empresa_id, "Kit externo")
    kit_interno = criar_kit(db, empresa_id, "Kit interno")

    componente = composicao_service.adicionar_componente(
        db, empresa_id, kit_externo.id, componente_id=kit_interno.id, quantidade=Decimal("1")
    )
    assert componente.componente_id == kit_interno.id


def test_perda_percentual_exige_recurso(db):
    empresa_id = criar_empresa(db)
    kit = criar_kit(db, empresa_id)
    suculenta = criar_simples(db, empresa_id, "Suculenta")

    from app.modules.assinaturas.models import PlanoRegra
    from app.modules.assinaturas.regras import PLANO_PRO, Recurso
    from app.modules.assinaturas.repository import plano_por_codigo

    pro = plano_por_codigo(db, PLANO_PRO)
    db.delete(db.get(PlanoRegra, (pro.id, Recurso.PERDA_NA_COMPOSICAO.value)))
    db.flush()

    with pytest.raises(RecursoDoPlano):
        composicao_service.adicionar_componente(
            db, empresa_id, kit.id, componente_id=suculenta.id,
            quantidade=Decimal("1"), perda_percentual=Decimal("5"),
        )


def test_montagem_consome_componentes_e_credita_o_kit(db):
    empresa_id = criar_empresa(db)
    kit = criar_kit(db, empresa_id)
    filamento = criar_simples(db, empresa_id, "Filamento", unidade_codigo="g", vendavel=False, insumo=True)
    terra = criar_simples(db, empresa_id, "Terra", unidade_codigo="kg", vendavel=False, insumo=True)

    composicao_service.adicionar_componente(
        db, empresa_id, kit.id, componente_id=filamento.id, quantidade=Decimal("85")
    )
    composicao_service.adicionar_componente(
        db, empresa_id, kit.id, componente_id=terra.id, quantidade=Decimal("0.15")
    )
    estoque_service.registrar_entrada(
        db, empresa_id, filamento.id, quantidade=Decimal("1000"), custo_unitario=Decimal("0.10")
    )
    estoque_service.registrar_entrada(
        db, empresa_id, terra.id, quantidade=Decimal("10"), custo_unitario=Decimal("5.00")
    )

    movimento = composicao_service.montar(db, empresa_id, kit.id, quantidade=Decimal("2"))

    assert movimento.quantidade == Decimal("2.0000")
    saldo_filamento = estoque_service.obter_saldo(db, empresa_id, filamento.id)
    saldo_terra = estoque_service.obter_saldo(db, empresa_id, terra.id)
    saldo_kit = estoque_service.obter_saldo(db, empresa_id, kit.id)
    assert saldo_filamento.fisico == Decimal("1000") - Decimal("170.0000")
    assert saldo_terra.fisico == Decimal("10") - Decimal("0.3000")
    assert saldo_kit.fisico == Decimal("2.0000")

    # custo: (170*0.10 + 0.30*5.00) / 2 = (17 + 1.5) / 2 = 9.25
    kit_atualizado = produtos_service.obter_produto(db, empresa_id, kit.id)
    assert kit_atualizado.custo_medio == Decimal("9.250000")


def test_montagem_aplica_perda_percentual_no_consumo(db):
    empresa_id = criar_empresa(db)
    kit = criar_kit(db, empresa_id)
    filamento = criar_simples(db, empresa_id, "Filamento", unidade_codigo="g", vendavel=False, insumo=True)

    composicao_service.adicionar_componente(
        db, empresa_id, kit.id, componente_id=filamento.id,
        quantidade=Decimal("100"), perda_percentual=Decimal("5"),
    )
    estoque_service.registrar_entrada(
        db, empresa_id, filamento.id, quantidade=Decimal("1000"), custo_unitario=Decimal("0.10")
    )

    composicao_service.montar(db, empresa_id, kit.id, quantidade=Decimal("1"))

    # 100g + 5% de perda = 105g consumidos
    saldo = estoque_service.obter_saldo(db, empresa_id, filamento.id)
    assert saldo.fisico == Decimal("1000") - Decimal("105.0000")


def test_montagem_sem_componentes_e_recusada(db):
    empresa_id = criar_empresa(db)
    kit = criar_kit(db, empresa_id)
    with pytest.raises(RegraDeNegocio):
        composicao_service.montar(db, empresa_id, kit.id, quantidade=Decimal("1"))


def test_montagem_de_produto_simples_e_recusada(db):
    empresa_id = criar_empresa(db)
    simples = criar_simples(db, empresa_id, "Vaso")
    with pytest.raises(RegraDeNegocio):
        composicao_service.montar(db, empresa_id, simples.id, quantidade=Decimal("1"))


def test_montagem_e_idempotente_pelo_id_do_cliente(db):
    empresa_id = criar_empresa(db)
    kit = criar_kit(db, empresa_id)
    filamento = criar_simples(db, empresa_id, "Filamento", unidade_codigo="g", vendavel=False, insumo=True)
    composicao_service.adicionar_componente(
        db, empresa_id, kit.id, componente_id=filamento.id, quantidade=Decimal("10")
    )
    estoque_service.registrar_entrada(
        db, empresa_id, filamento.id, quantidade=Decimal("100"), custo_unitario=Decimal("0.10")
    )

    id_cliente = uuid.uuid4()
    primeiro = composicao_service.montar(
        db, empresa_id, kit.id, quantidade=Decimal("1"), id=id_cliente
    )
    segundo = composicao_service.montar(
        db, empresa_id, kit.id, quantidade=Decimal("1"), id=id_cliente
    )

    assert primeiro.id == segundo.id == id_cliente
    saldo_filamento = estoque_service.obter_saldo(db, empresa_id, filamento.id)
    assert saldo_filamento.fisico == Decimal("100") - Decimal("10.0000")


def test_componentes_de_outra_empresa_nao_sao_encontrados(db):
    primeira = criar_empresa(db)
    segunda = criar_empresa(db)
    kit = criar_kit(db, primeira)

    with pytest.raises(NaoEncontrado):
        composicao_service.listar_componentes(db, segunda, kit.id)


def test_consumo_de_insumos_soma_montagens_e_ajustes_para_baixo(db):
    from datetime import timedelta

    from app.modules.vendas import service as vendas_service

    empresa_id = criar_empresa(db)
    kit = criar_kit(db, empresa_id)
    filamento = criar_simples(db, empresa_id, "Filamento", unidade_codigo="g", vendavel=False, insumo=True)
    terra = criar_simples(db, empresa_id, "Terra", unidade_codigo="kg", vendavel=False, insumo=True)
    pronto = criar_simples(db, empresa_id, "Vaso pronto")  # não é insumo

    composicao_service.adicionar_componente(
        db, empresa_id, kit.id, componente_id=filamento.id,
        quantidade=Decimal("100"), perda_percentual=Decimal("5"),
    )
    for produto, qtd, custo in ((filamento, "1000", "0.10"), (terra, "10", "5"), (pronto, "5", "1")):
        estoque_service.registrar_entrada(
            db, empresa_id, produto.id, quantidade=Decimal(qtd), custo_unitario=Decimal(custo)
        )

    composicao_service.montar(db, empresa_id, kit.id, quantidade=Decimal("2"))  # 210 g de filamento
    estoque_service.registrar_ajuste(db, empresa_id, filamento.id, quantidade_contada=Decimal("780"))  # -10 g
    estoque_service.registrar_ajuste(db, empresa_id, terra.id, quantidade_contada=Decimal("12"))  # ajuste PARA CIMA
    estoque_service.registrar_ajuste(db, empresa_id, pronto.id, quantidade_contada=Decimal("3"))  # não é insumo

    hoje = vendas_service.hoje()
    itens = estoque_service.consumo_de_insumos(db, empresa_id, inicio=hoje, fim=hoje)

    # A terra só teve ajuste positivo e o vaso não é insumo: só o filamento aparece.
    assert [i.produto.nome for i in itens] == ["Filamento"]
    fil = itens[0]
    assert fil.consumido_em_montagens == Decimal("210.0000")
    assert fil.custo_das_montagens == Decimal("21.00")
    assert fil.baixado_por_ajuste == Decimal("10.0000")
    assert fil.custo_dos_ajustes == Decimal("1.00")
    assert fil.custo_total == Decimal("22.00")

    # Fora do período não entra.
    assert estoque_service.consumo_de_insumos(
        db, empresa_id, inicio=hoje - timedelta(days=10), fim=hoje - timedelta(days=5)
    ) == []


def test_consumo_de_insumos_valida_periodo(db):
    from datetime import timedelta

    from app.modules.vendas import service as vendas_service

    empresa_id = criar_empresa(db)
    hoje = vendas_service.hoje()
    with pytest.raises(RegraDeNegocio):
        estoque_service.consumo_de_insumos(db, empresa_id, inicio=hoje, fim=hoje - timedelta(days=1))
