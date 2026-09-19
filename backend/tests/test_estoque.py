import uuid
from decimal import Decimal

import pytest

from app.core.exceptions import NaoEncontrado, RegraDeNegocio
from app.modules.empresas.service import criar_empresa_com_padroes
from app.modules.estoque import service
from app.modules.estoque.models import TipoMovimento
from app.modules.estoque.repository import MovimentoRepositorio
from app.modules.produtos import service as produtos_service
from app.modules.usuarios.models import Usuario


def criar_empresa(db):
    usuario = Usuario(nome="Dona", email=f"{uuid.uuid4().hex[:8]}@exemplo.com", senha_hash="x")
    db.add(usuario)
    db.flush()
    criada = criar_empresa_com_padroes(
        db, nome_fantasia=f"Loja {uuid.uuid4().hex[:6]}", usuario_dono_id=usuario.id
    )
    return criada.empresa.id


def criar_produto(db, empresa_id, **kwargs):
    kwargs.setdefault("nome", "Filamento PLA")
    kwargs.setdefault("unidade_codigo", "g")
    kwargs.setdefault("vendavel", False)
    kwargs.setdefault("insumo", True)
    return produtos_service.criar_produto(db, empresa_id, **kwargs)


def test_primeira_entrada_vira_o_custo_do_produto(db):
    empresa_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id)

    movimento = service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("1000"), custo_unitario=Decimal("0.12")
    )

    assert movimento.tipo is TipoMovimento.ENTRADA
    assert movimento.quantidade == Decimal("1000.0000")
    saldo = service.obter_saldo(db, empresa_id, produto.id)
    assert saldo.fisico == Decimal("1000.0000")
    assert saldo.disponivel == Decimal("1000.0000")
    assert produto.custo_medio == Decimal("0.120000")


def test_segunda_entrada_calcula_media_ponderada(db):
    empresa_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id)

    service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("1000"), custo_unitario=Decimal("0.10")
    )
    service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("1000"), custo_unitario=Decimal("0.20")
    )

    saldo = service.obter_saldo(db, empresa_id, produto.id)
    assert saldo.fisico == Decimal("2000.0000")
    # (1000*0.10 + 1000*0.20) / 2000 = 0.15
    assert produto.custo_medio == Decimal("0.150000")


def test_entrada_com_unidade_alternativa_converte_para_a_unidade_base(db):
    empresa_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id)
    rolo = produtos_service.adicionar_unidade(
        db, empresa_id, produto.id, nome="Rolo", fator=Decimal("1000")
    )

    movimento = service.registrar_entrada(
        db,
        empresa_id,
        produto.id,
        quantidade=Decimal("1"),
        custo_unitario=Decimal("120.00"),
        unidade_id=rolo.id,
    )

    assert movimento.quantidade == Decimal("1000.0000")
    assert movimento.custo_unitario == Decimal("0.120000")
    saldo = service.obter_saldo(db, empresa_id, produto.id)
    assert saldo.fisico == Decimal("1000.0000")


def test_saida_usa_custo_vigente_e_nao_altera_a_media(db):
    empresa_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id)
    service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("1000"), custo_unitario=Decimal("0.10")
    )

    movimento = service.registrar_saida(db, empresa_id, produto.id, quantidade=Decimal("300"))

    assert movimento.tipo is TipoMovimento.SAIDA
    assert movimento.quantidade == Decimal("-300.0000")
    assert movimento.custo_unitario == Decimal("0.100000")
    assert produto.custo_medio == Decimal("0.100000")
    saldo = service.obter_saldo(db, empresa_id, produto.id)
    assert saldo.fisico == Decimal("700.0000")


def test_saida_permite_saldo_fisico_negativo(db):
    empresa_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id)

    service.registrar_saida(db, empresa_id, produto.id, quantidade=Decimal("50"))

    saldo = service.obter_saldo(db, empresa_id, produto.id)
    assert saldo.fisico == Decimal("-50.0000")


def test_ajuste_usa_a_quantidade_contada_e_nao_mexe_na_media(db):
    empresa_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id)
    service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("1000"), custo_unitario=Decimal("0.10")
    )

    movimento = service.registrar_ajuste(db, empresa_id, produto.id, quantidade_contada=Decimal("950"))

    assert movimento.tipo is TipoMovimento.AJUSTE
    assert movimento.quantidade == Decimal("-50.0000")
    assert produto.custo_medio == Decimal("0.100000")
    saldo = service.obter_saldo(db, empresa_id, produto.id)
    assert saldo.fisico == Decimal("950.0000")


def test_ajuste_sem_diferenca_nao_cria_movimento(db):
    empresa_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id)
    service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("100"), custo_unitario=Decimal("0.10")
    )

    resultado = service.registrar_ajuste(db, empresa_id, produto.id, quantidade_contada=Decimal("100"))

    assert resultado is None
    assert len(service.listar_movimentos(db, empresa_id, produto_id=produto.id)) == 1


def test_estorno_credita_de_volta_sem_mexer_na_media(db):
    empresa_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id)
    service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("1000"), custo_unitario=Decimal("0.10")
    )
    service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("1000"), custo_unitario=Decimal("0.20")
    )
    service.registrar_saida(db, empresa_id, produto.id, quantidade=Decimal("300"))

    movimento = service.estornar_saida(
        db, empresa_id, produto.id, quantidade=Decimal("300"), custo_unitario=Decimal("0.99")
    )

    assert movimento.tipo is TipoMovimento.ESTORNO
    assert movimento.quantidade == Decimal("300.0000")
    assert movimento.custo_unitario == Decimal("0.990000")
    # Estorno grava o custo histórico da venda cancelada, mas não recalcula
    # a média ponderada do produto (continua a de antes: 0.15).
    assert produto.custo_medio == Decimal("0.150000")
    saldo = service.obter_saldo(db, empresa_id, produto.id)
    assert saldo.fisico == Decimal("2000.0000")


def test_reserva_bloqueia_sem_disponivel_suficiente(db):
    empresa_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id)
    service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("100"), custo_unitario=Decimal("0.10")
    )

    service.reservar(db, empresa_id, produto.id, quantidade=Decimal("60"))
    with pytest.raises(RegraDeNegocio):
        service.reservar(db, empresa_id, produto.id, quantidade=Decimal("50"))


def test_reserva_e_liberacao_alteram_o_reservado(db):
    empresa_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id)
    service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("100"), custo_unitario=Decimal("0.10")
    )

    service.reservar(db, empresa_id, produto.id, quantidade=Decimal("40"))
    saldo = service.obter_saldo(db, empresa_id, produto.id)
    assert saldo.reservado == Decimal("40.0000")
    assert saldo.disponivel == Decimal("60.0000")

    service.liberar_reserva(db, empresa_id, produto.id, quantidade=Decimal("15"))
    saldo = service.obter_saldo(db, empresa_id, produto.id)
    assert saldo.reservado == Decimal("25.0000")
    assert saldo.disponivel == Decimal("75.0000")


def test_liberar_mais_do_que_o_reservado_e_recusado(db):
    empresa_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id)
    service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("100"), custo_unitario=Decimal("0.10")
    )
    service.reservar(db, empresa_id, produto.id, quantidade=Decimal("10"))

    with pytest.raises(RegraDeNegocio):
        service.liberar_reserva(db, empresa_id, produto.id, quantidade=Decimal("20"))


def test_produto_sem_controle_de_estoque_e_recusado(db):
    empresa_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, controla_estoque=False)

    with pytest.raises(RegraDeNegocio):
        service.registrar_entrada(
            db, empresa_id, produto.id, quantidade=Decimal("10"), custo_unitario=Decimal("1")
        )


def test_movimento_de_outra_empresa_nao_e_encontrado(db):
    primeira = criar_empresa(db)
    segunda = criar_empresa(db)
    produto = criar_produto(db, primeira)

    with pytest.raises(NaoEncontrado):
        service.registrar_entrada(
            db, segunda, produto.id, quantidade=Decimal("10"), custo_unitario=Decimal("1")
        )


def test_saldos_e_movimentos_de_outra_empresa_nao_aparecem(db):
    primeira = criar_empresa(db)
    segunda = criar_empresa(db)
    produto = criar_produto(db, primeira)
    service.registrar_entrada(
        db, primeira, produto.id, quantidade=Decimal("100"), custo_unitario=Decimal("0.10")
    )

    assert MovimentoRepositorio(db, segunda).buscar() == []


def test_listar_saldos_inclui_produto_sem_movimento(db):
    empresa_id = criar_empresa(db)
    com_movimento = criar_produto(db, empresa_id, nome="Filamento PLA")
    sem_movimento = criar_produto(db, empresa_id, nome="Filamento ABS")
    servico = criar_produto(
        db, empresa_id, nome="Mão de obra", unidade_codigo="un",
        vendavel=True, insumo=False, controla_estoque=False,
    )
    service.registrar_entrada(
        db, empresa_id, com_movimento.id, quantidade=Decimal("500"), custo_unitario=Decimal("0.10")
    )

    saldos = service.listar_saldos(db, empresa_id)

    por_produto = {item.produto.id: item for item in saldos}
    assert com_movimento.id in por_produto
    assert sem_movimento.id in por_produto
    assert servico.id not in por_produto
    assert por_produto[com_movimento.id].fisico == Decimal("500.0000")
    assert por_produto[sem_movimento.id].fisico == Decimal("0")
    assert por_produto[sem_movimento.id].disponivel == Decimal("0")


def test_id_do_cliente_e_idempotente(db):
    empresa_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id)
    id_cliente = uuid.uuid4()

    primeiro = service.registrar_entrada(
        db,
        empresa_id,
        produto.id,
        quantidade=Decimal("100"),
        custo_unitario=Decimal("0.10"),
        id=id_cliente,
    )
    segundo = service.registrar_entrada(
        db,
        empresa_id,
        produto.id,
        quantidade=Decimal("100"),
        custo_unitario=Decimal("0.10"),
        id=id_cliente,
    )

    assert primeiro.id == segundo.id == id_cliente
    saldo = service.obter_saldo(db, empresa_id, produto.id)
    assert saldo.fisico == Decimal("100.0000")


def test_alertas_de_estoque_negativo_e_baixo(db):
    empresa_id = criar_empresa(db)
    negativo = criar_produto(db, empresa_id, nome="Negativo")
    service.registrar_saida(db, empresa_id, negativo.id, quantidade=Decimal("5"))
    baixo = criar_produto(db, empresa_id, nome="Baixo", estoque_minimo=Decimal("10"))
    service.registrar_entrada(
        db, empresa_id, baixo.id, quantidade=Decimal("10"), custo_unitario=Decimal("1")
    )
    ok = criar_produto(db, empresa_id, nome="Tranquilo", estoque_minimo=Decimal("10"))
    service.registrar_entrada(
        db, empresa_id, ok.id, quantidade=Decimal("11"), custo_unitario=Decimal("1")
    )
    criar_produto(db, empresa_id, nome="Sem mínimo")  # saldo 0, sem mínimo: sem alerta

    alertas = service.alertas_de_estoque(db, empresa_id)

    assert [(a.produto.nome, a.tipo) for a in alertas] == [
        ("Negativo", "negativo"),
        ("Baixo", "baixo"),
    ]


def test_alerta_considera_reserva_no_disponivel(db):
    empresa_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, estoque_minimo=Decimal("5"))
    service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("8"), custo_unitario=Decimal("1")
    )
    assert service.alertas_de_estoque(db, empresa_id) == []

    service.reservar(db, empresa_id, produto.id, quantidade=Decimal("4"))

    assert [a.tipo for a in service.alertas_de_estoque(db, empresa_id)] == ["baixo"]


def test_alertas_nao_misturam_empresas(db):
    empresa_a = criar_empresa(db)
    empresa_b = criar_empresa(db)
    produto = criar_produto(db, empresa_a)
    service.registrar_saida(db, empresa_a, produto.id, quantidade=Decimal("1"))

    assert len(service.alertas_de_estoque(db, empresa_a)) == 1
    assert service.alertas_de_estoque(db, empresa_b) == []
