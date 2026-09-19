import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.core.exceptions import NaoEncontrado, PermissaoNegada, RegraDeNegocio
from app.modules.clientes import service as clientes_service
from app.modules.composicao import service as composicao_service
from app.modules.empresas.service import criar_empresa_com_padroes
from app.modules.estoque import service as estoque_service
from app.modules.produtos import service as produtos_service
from app.modules.produtos.models import TipoProduto
from app.modules.usuarios.models import Usuario
from app.modules.vendas import service
from app.modules.vendas.models import FormaPagamento, StatusVenda
from app.modules.vendas.repository import VendaRepositorio


def criar_empresa(db) -> tuple[uuid.UUID, uuid.UUID]:
    usuario = Usuario(nome="Dona", email=f"{uuid.uuid4().hex[:8]}@exemplo.com", senha_hash="x")
    db.add(usuario)
    db.flush()
    criada = criar_empresa_com_padroes(
        db, nome_fantasia=f"Loja {uuid.uuid4().hex[:6]}", usuario_dono_id=usuario.id
    )
    return criada.empresa.id, usuario.id


def criar_produto(db, empresa_id, nome="Vaso", **kwargs):
    kwargs.setdefault("unidade_codigo", "un")
    kwargs.setdefault("vendavel", True)
    kwargs.setdefault("preco_venda", Decimal("50"))
    return produtos_service.criar_produto(db, empresa_id, nome=nome, **kwargs)


def pagamento(valor: str, forma: FormaPagamento = FormaPagamento.DINHEIRO) -> dict:
    return {"forma": forma, "valor": Decimal(valor)}


def test_abrir_venda_cria_ticket_aberto_sem_itens(db):
    empresa_id, vendedor_id = criar_empresa(db)

    venda = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id)

    assert venda.numero == "VD-0001"
    assert venda.status is StatusVenda.ABERTO
    assert venda.total == Decimal("0.00")


def test_adicionar_item_reserva_estoque_sem_debitar(db):
    empresa_id, vendedor_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))
    estoque_service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("10"), custo_unitario=Decimal("20")
    )
    venda = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id)

    service.adicionar_item(
        db, empresa_id, venda.id, produto_id=produto.id, quantidade=Decimal("2")
    )

    saldo = estoque_service.obter_saldo(db, empresa_id, produto.id)
    assert saldo.fisico == Decimal("10.0000")
    assert saldo.reservado == Decimal("2.0000")
    assert saldo.disponivel == Decimal("8.0000")

    venda = service.obter_venda(db, empresa_id, venda.id)
    assert venda.total == Decimal("100.00")


def test_adicionar_item_sem_estoque_suficiente_falha(db):
    empresa_id, vendedor_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))
    venda = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id)

    with pytest.raises(RegraDeNegocio):
        service.adicionar_item(
            db, empresa_id, venda.id, produto_id=produto.id, quantidade=Decimal("1")
        )


def test_remover_item_libera_a_reserva(db):
    empresa_id, vendedor_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))
    estoque_service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("10"), custo_unitario=Decimal("20")
    )
    venda = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id)
    item = service.adicionar_item(
        db, empresa_id, venda.id, produto_id=produto.id, quantidade=Decimal("2")
    )

    service.remover_item(db, empresa_id, venda.id, item.id)

    saldo = estoque_service.obter_saldo(db, empresa_id, produto.id)
    assert saldo.reservado == Decimal("0.0000")
    venda = service.obter_venda(db, empresa_id, venda.id)
    assert venda.total == Decimal("0.00")
    assert service.itens_da_venda(db, venda.id) == []


def test_fechar_venda_converte_reserva_em_saida_e_grava_pagamento(db):
    empresa_id, vendedor_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))
    estoque_service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("10"), custo_unitario=Decimal("20")
    )
    venda = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id)
    service.adicionar_item(db, empresa_id, venda.id, produto_id=produto.id, quantidade=Decimal("2"))

    fechada = service.fechar_venda(db, empresa_id, venda.id, pagamentos=[pagamento("100")])

    assert fechada.status is StatusVenda.FECHADO
    assert fechada.fechado_em is not None

    saldo = estoque_service.obter_saldo(db, empresa_id, produto.id)
    assert saldo.fisico == Decimal("8.0000")
    assert saldo.reservado == Decimal("0.0000")

    itens = service.itens_da_venda(db, venda.id)
    assert itens[0].movimento_estoque_id is not None
    assert itens[0].custo_unitario == Decimal("20.000000")

    pagamentos = service.pagamentos_da_venda(db, venda.id)
    assert len(pagamentos) == 1


def test_fechar_venda_sem_item_falha(db):
    empresa_id, vendedor_id = criar_empresa(db)
    venda = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id)

    with pytest.raises(RegraDeNegocio):
        service.fechar_venda(db, empresa_id, venda.id, pagamentos=[pagamento("10")])


def test_fechar_venda_com_soma_de_pagamentos_errada_falha(db):
    empresa_id, vendedor_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))
    estoque_service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("10"), custo_unitario=Decimal("20")
    )
    venda = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id)
    service.adicionar_item(
        db, empresa_id, venda.id, produto_id=produto.id, quantidade=Decimal("1")
    )

    with pytest.raises(RegraDeNegocio):
        service.fechar_venda(db, empresa_id, venda.id, pagamentos=[pagamento("30")])


def test_pagamento_dividido_em_duas_formas(db):
    empresa_id, vendedor_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))
    estoque_service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("10"), custo_unitario=Decimal("20")
    )
    venda = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id)
    service.adicionar_item(
        db, empresa_id, venda.id, produto_id=produto.id, quantidade=Decimal("1")
    )

    service.fechar_venda(
        db, empresa_id, venda.id, pagamentos=[pagamento("30"), pagamento("20", FormaPagamento.PIX)]
    )

    pagamentos = service.pagamentos_da_venda(db, venda.id)
    assert len(pagamentos) == 2
    assert sum(p.valor for p in pagamentos) == Decimal("50.00")


def test_cancelar_venda_libera_reservas(db):
    empresa_id, vendedor_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))
    estoque_service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("10"), custo_unitario=Decimal("20")
    )
    venda = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id)
    service.adicionar_item(db, empresa_id, venda.id, produto_id=produto.id, quantidade=Decimal("2"))

    cancelada = service.cancelar_venda(db, empresa_id, venda.id)

    assert cancelada.status is StatusVenda.CANCELADO
    saldo = estoque_service.obter_saldo(db, empresa_id, produto.id)
    assert saldo.reservado == Decimal("0.0000")
    assert saldo.fisico == Decimal("10.0000")


def test_nao_pode_mexer_em_venda_fechada_ou_cancelada(db):
    empresa_id, vendedor_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))
    venda = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id)
    service.cancelar_venda(db, empresa_id, venda.id)

    with pytest.raises(RegraDeNegocio):
        service.adicionar_item(
            db, empresa_id, venda.id, produto_id=produto.id, quantidade=Decimal("1")
        )
    with pytest.raises(RegraDeNegocio):
        service.cancelar_venda(db, empresa_id, venda.id)


def test_produto_sem_controle_de_estoque_nao_reserva_nem_debita(db):
    empresa_id, vendedor_id = criar_empresa(db)
    servico = criar_produto(
        db, empresa_id, nome="Mão de obra", preco_venda=Decimal("30"), controla_estoque=False
    )
    venda = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id)

    item = service.adicionar_item(
        db, empresa_id, venda.id, produto_id=servico.id, quantidade=Decimal("1")
    )
    assert item.movimento_reserva_id is None

    fechada = service.fechar_venda(db, empresa_id, venda.id, pagamentos=[pagamento("30")])
    assert fechada.status is StatusVenda.FECHADO
    itens = service.itens_da_venda(db, venda.id)
    assert itens[0].movimento_estoque_id is None
    assert itens[0].custo_unitario is None


def test_kit_reserva_e_debita_so_o_proprio_saldo(db):
    empresa_id, vendedor_id = criar_empresa(db)
    componente = criar_produto(
        db, empresa_id, nome="Suculenta", vendavel=False, insumo=True, preco_venda=Decimal("0")
    )
    kit = criar_produto(
        db, empresa_id, nome="Kit vaso", tipo=TipoProduto.KIT, preco_venda=Decimal("80")
    )
    estoque_service.registrar_entrada(
        db, empresa_id, componente.id, quantidade=Decimal("10"), custo_unitario=Decimal("5")
    )
    composicao_service.adicionar_componente(
        db, empresa_id, kit.id, componente_id=componente.id, quantidade=Decimal("1")
    )
    composicao_service.montar(db, empresa_id, kit.id, quantidade=Decimal("3"))

    venda = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id)
    service.adicionar_item(db, empresa_id, venda.id, produto_id=kit.id, quantidade=Decimal("1"))
    service.fechar_venda(db, empresa_id, venda.id, pagamentos=[pagamento("80")])

    saldo_kit = estoque_service.obter_saldo(db, empresa_id, kit.id)
    saldo_componente = estoque_service.obter_saldo(db, empresa_id, componente.id)
    assert saldo_kit.fisico == Decimal("2.0000")
    # A montagem já debitou o componente; a venda do kit não mexe nele de novo.
    assert saldo_componente.fisico == Decimal("7.0000")


def test_desconto_acima_do_limite_sem_permissao_falha(db):
    empresa_id, vendedor_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))
    venda = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id)

    with pytest.raises(RegraDeNegocio):
        service.adicionar_item(
            db,
            empresa_id,
            venda.id,
            produto_id=produto.id,
            quantidade=Decimal("1"),
            desconto_percentual=Decimal("20"),
            limite_desconto_percentual=Decimal("10"),
            pode_exceder_limite=False,
        )


def test_desconto_acima_do_limite_com_permissao_funciona(db):
    empresa_id, vendedor_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))
    estoque_service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("10"), custo_unitario=Decimal("20")
    )
    venda = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id)

    item = service.adicionar_item(
        db,
        empresa_id,
        venda.id,
        produto_id=produto.id,
        quantidade=Decimal("1"),
        desconto_percentual=Decimal("20"),
        limite_desconto_percentual=Decimal("10"),
        pode_exceder_limite=True,
    )

    assert item.preco_final == Decimal("40.00")


def test_abrir_venda_com_cliente_novo_inline(db):
    empresa_id, vendedor_id = criar_empresa(db)

    venda = service.abrir_venda(
        db, empresa_id, vendedor_usuario_id=vendedor_id, cliente_novo={"nome": "Maria"}
    )

    assert venda.cliente_id is not None
    clientes = clientes_service.listar_clientes(db, empresa_id)
    assert clientes[0].nome == "Maria"


def test_atualizar_cliente_da_venda_aberta(db):
    empresa_id, vendedor_id = criar_empresa(db)
    cliente = clientes_service.criar_cliente(db, empresa_id, nome="João")
    venda = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id)

    atualizada = service.atualizar_cliente_da_venda(
        db, empresa_id, venda.id, cliente_id=cliente.id
    )

    assert atualizada.cliente_id == cliente.id


def test_reenviar_o_mesmo_id_nao_duplica(db):
    empresa_id, vendedor_id = criar_empresa(db)
    id_da_venda = uuid.uuid4()

    primeira = service.abrir_venda(
        db, empresa_id, id=id_da_venda, vendedor_usuario_id=vendedor_id
    )
    segunda = service.abrir_venda(
        db, empresa_id, id=id_da_venda, vendedor_usuario_id=vendedor_id
    )

    assert primeira.id == segunda.id
    assert primeira.numero == segunda.numero


def test_venda_de_outra_empresa_nao_e_encontrada(db):
    primeira, vendedor_id = criar_empresa(db)
    segunda, _ = criar_empresa(db)
    venda = service.abrir_venda(db, primeira, vendedor_usuario_id=vendedor_id)

    assert VendaRepositorio(db, segunda).buscar() == []
    with pytest.raises(NaoEncontrado):
        service.obter_venda(db, segunda, venda.id)


def test_cancelar_venda_fechada_sem_permissao_falha(db):
    empresa_id, vendedor_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))
    estoque_service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("10"), custo_unitario=Decimal("20")
    )
    venda = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id)
    service.adicionar_item(db, empresa_id, venda.id, produto_id=produto.id, quantidade=Decimal("2"))
    service.fechar_venda(db, empresa_id, venda.id, pagamentos=[pagamento("100")])

    with pytest.raises(PermissaoNegada):
        service.cancelar_venda(db, empresa_id, venda.id, pode_cancelar_fechada=False)


def test_cancelar_venda_fechada_estorna_estoque(db):
    empresa_id, vendedor_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))
    estoque_service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("10"), custo_unitario=Decimal("20")
    )
    venda = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id)
    service.adicionar_item(db, empresa_id, venda.id, produto_id=produto.id, quantidade=Decimal("2"))
    service.fechar_venda(db, empresa_id, venda.id, pagamentos=[pagamento("100")])

    cancelada = service.cancelar_venda(db, empresa_id, venda.id, pode_cancelar_fechada=True)

    assert cancelada.status is StatusVenda.CANCELADO
    assert cancelada.cancelado_em is not None

    saldo = estoque_service.obter_saldo(db, empresa_id, produto.id)
    # 10 - 2 (saída no fechamento) + 2 (estorno no cancelamento) = 10
    assert saldo.fisico == Decimal("10.0000")
    # O estorno não recalcula a média ponderada do produto.
    assert produto.custo_medio == Decimal("20.000000")

    itens = service.itens_da_venda(db, venda.id)
    assert itens[0].movimento_estorno_id is not None


def test_cancelar_venda_ja_cancelada_falha(db):
    empresa_id, vendedor_id = criar_empresa(db)
    venda = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id)
    service.cancelar_venda(db, empresa_id, venda.id)

    with pytest.raises(RegraDeNegocio):
        service.cancelar_venda(db, empresa_id, venda.id)


def test_listar_vendas_filtra_por_status(db):
    empresa_id, vendedor_id = criar_empresa(db)
    aberta = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id)
    cancelada = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id)
    service.cancelar_venda(db, empresa_id, cancelada.id)

    abertas = service.listar_vendas(db, empresa_id, status=StatusVenda.ABERTO)
    canceladas = service.listar_vendas(db, empresa_id, status=StatusVenda.CANCELADO)

    assert [v.id for v in abertas] == [aberta.id]
    assert [v.id for v in canceladas] == [cancelada.id]


def test_metricas_do_cliente_so_conta_vendas_fechadas(db):
    empresa_id, vendedor_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))
    estoque_service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("10"), custo_unitario=Decimal("20")
    )
    cliente = clientes_service.criar_cliente(db, empresa_id, nome="Maria")

    fechada = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id, cliente_id=cliente.id)
    service.adicionar_item(db, empresa_id, fechada.id, produto_id=produto.id, quantidade=Decimal("1"))
    service.fechar_venda(db, empresa_id, fechada.id, pagamentos=[pagamento("50")])

    aberta = service.abrir_venda(db, empresa_id, vendedor_usuario_id=vendedor_id, cliente_id=cliente.id)
    service.adicionar_item(db, empresa_id, aberta.id, produto_id=produto.id, quantidade=Decimal("1"))

    metricas = service.metricas_do_cliente(db, empresa_id, cliente.id)

    assert metricas.quantidade_compras == 1
    assert metricas.valor_total == Decimal("50.00")
    assert metricas.ticket_medio == Decimal("50.00")
    assert metricas.primeira_compra is not None
    assert metricas.ultima_compra is not None


def test_metricas_de_cliente_sem_compra_fechada(db):
    empresa_id, _ = criar_empresa(db)
    cliente = clientes_service.criar_cliente(db, empresa_id, nome="Maria")

    metricas = service.metricas_do_cliente(db, empresa_id, cliente.id)

    assert metricas.quantidade_compras == 0
    assert metricas.valor_total == Decimal("0.00")
    assert metricas.ticket_medio is None


def test_reatribuir_cliente_move_as_vendas_do_duplicado(db):
    empresa_id, vendedor_id = criar_empresa(db)
    sobrevivente = clientes_service.criar_cliente(db, empresa_id, nome="Maria")
    duplicado = clientes_service.criar_cliente(db, empresa_id, nome="Maria S.")
    venda = service.abrir_venda(
        db, empresa_id, vendedor_usuario_id=vendedor_id, cliente_id=duplicado.id
    )

    service.reatribuir_cliente(
        db, empresa_id, de_cliente_id=duplicado.id, para_cliente_id=sobrevivente.id
    )

    atualizada = service.obter_venda(db, empresa_id, venda.id)
    assert atualizada.cliente_id == sobrevivente.id


def item_offline(produto_id, **kwargs) -> dict:
    dados = {
        "produto_id": produto_id,
        "quantidade": Decimal("1"),
        "unidade_id": None,
        "preco_tabela": Decimal("50"),
        "desconto_percentual": Decimal("0"),
    }
    dados.update(kwargs)
    return dados


def test_sincronizar_venda_offline_debita_direto_permitindo_negativo(db):
    empresa_id, vendedor_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))
    ocorrido_em = datetime.now(UTC) - timedelta(hours=2)

    venda = service.sincronizar_venda_offline(
        db,
        empresa_id,
        id=uuid.uuid4(),
        vendedor_usuario_id=vendedor_id,
        itens=[item_offline(produto.id, quantidade=Decimal("3"))],
        pagamentos=[pagamento("150")],
        ocorrido_em=ocorrido_em,
    )

    assert venda.status is StatusVenda.FECHADO
    assert venda.ocorrido_em == ocorrido_em
    assert venda.fechado_em == ocorrido_em
    assert venda.total == Decimal("150.00")

    # Não havia estoque nenhum: fica negativo, sem bloquear a venda.
    saldo = estoque_service.obter_saldo(db, empresa_id, produto.id)
    assert saldo.fisico == Decimal("-3.0000")
    assert saldo.reservado == Decimal("0.0000")

    itens = service.itens_da_venda(db, venda.id)
    assert itens[0].movimento_reserva_id is None
    assert itens[0].movimento_estoque_id is not None


def test_sincronizar_venda_offline_usa_preco_enviado_pelo_dispositivo(db):
    empresa_id, vendedor_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))

    # O preço no catálogo mudou depois que o dispositivo ficou offline.
    produtos_service.atualizar_produto(db, empresa_id, produto.id, {"preco_venda": Decimal("80")})

    venda = service.sincronizar_venda_offline(
        db,
        empresa_id,
        id=uuid.uuid4(),
        vendedor_usuario_id=vendedor_id,
        itens=[item_offline(produto.id, preco_tabela=Decimal("50"))],
        pagamentos=[pagamento("50")],
        ocorrido_em=datetime.now(UTC),
    )

    itens = service.itens_da_venda(db, venda.id)
    assert itens[0].preco_tabela == Decimal("50.00")
    assert venda.total == Decimal("50.00")


def test_sincronizar_venda_offline_reenviar_o_mesmo_id_nao_duplica(db):
    empresa_id, vendedor_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))
    id_da_venda = uuid.uuid4()
    ocorrido_em = datetime.now(UTC)

    primeira = service.sincronizar_venda_offline(
        db,
        empresa_id,
        id=id_da_venda,
        vendedor_usuario_id=vendedor_id,
        itens=[item_offline(produto.id)],
        pagamentos=[pagamento("50")],
        ocorrido_em=ocorrido_em,
    )
    segunda = service.sincronizar_venda_offline(
        db,
        empresa_id,
        id=id_da_venda,
        vendedor_usuario_id=vendedor_id,
        itens=[item_offline(produto.id)],
        pagamentos=[pagamento("50")],
        ocorrido_em=ocorrido_em,
    )

    assert primeira.id == segunda.id
    saldo = estoque_service.obter_saldo(db, empresa_id, produto.id)
    assert saldo.fisico == Decimal("-1.0000")


def test_sincronizar_venda_offline_kit_debita_so_o_proprio_saldo(db):
    empresa_id, vendedor_id = criar_empresa(db)
    componente = criar_produto(
        db, empresa_id, nome="Suculenta", vendavel=False, insumo=True, preco_venda=Decimal("0")
    )
    kit = criar_produto(
        db, empresa_id, nome="Kit vaso", tipo=TipoProduto.KIT, preco_venda=Decimal("80")
    )
    estoque_service.registrar_entrada(
        db, empresa_id, componente.id, quantidade=Decimal("10"), custo_unitario=Decimal("5")
    )
    composicao_service.adicionar_componente(
        db, empresa_id, kit.id, componente_id=componente.id, quantidade=Decimal("1")
    )
    composicao_service.montar(db, empresa_id, kit.id, quantidade=Decimal("3"))

    service.sincronizar_venda_offline(
        db,
        empresa_id,
        id=uuid.uuid4(),
        vendedor_usuario_id=vendedor_id,
        itens=[item_offline(kit.id, preco_tabela=Decimal("80"))],
        pagamentos=[pagamento("80")],
        ocorrido_em=datetime.now(UTC),
    )

    saldo_kit = estoque_service.obter_saldo(db, empresa_id, kit.id)
    saldo_componente = estoque_service.obter_saldo(db, empresa_id, componente.id)
    assert saldo_kit.fisico == Decimal("2.0000")
    assert saldo_componente.fisico == Decimal("7.0000")


def test_sincronizar_venda_offline_desconto_acima_do_limite_sem_permissao_falha(db):
    empresa_id, vendedor_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))

    with pytest.raises(RegraDeNegocio):
        service.sincronizar_venda_offline(
            db,
            empresa_id,
            id=uuid.uuid4(),
            vendedor_usuario_id=vendedor_id,
            itens=[item_offline(produto.id, desconto_percentual=Decimal("20"))],
            pagamentos=[pagamento("40")],
            ocorrido_em=datetime.now(UTC),
            limite_desconto_percentual=Decimal("10"),
            pode_exceder_limite=False,
        )


def test_sincronizar_venda_offline_com_cliente_novo_inline(db):
    empresa_id, vendedor_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))

    venda = service.sincronizar_venda_offline(
        db,
        empresa_id,
        id=uuid.uuid4(),
        vendedor_usuario_id=vendedor_id,
        cliente_novo={"nome": "Maria"},
        itens=[item_offline(produto.id)],
        pagamentos=[pagamento("50")],
        ocorrido_em=datetime.now(UTC),
    )

    assert venda.cliente_id is not None
    clientes = clientes_service.listar_clientes(db, empresa_id)
    assert clientes[0].nome == "Maria"
