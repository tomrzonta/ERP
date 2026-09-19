import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.core.exceptions import RegraDeNegocio
from app.core.permissions import catalogo
from app.modules.acesso.papeis_padrao import PAPEIS_PADRAO
from app.modules.empresas.service import criar_empresa_com_padroes
from app.modules.estoque import service as estoque_service
from app.modules.produtos import service as produtos_service
from app.modules.usuarios.models import Usuario
from app.modules.vendas import service as vendas_service
from app.modules.vendas.models import FormaPagamento


def criar_empresa(db) -> tuple[uuid.UUID, uuid.UUID]:
    usuario = Usuario(nome="Dona", email=f"{uuid.uuid4().hex[:8]}@exemplo.com", senha_hash="x")
    db.add(usuario)
    db.flush()
    criada = criar_empresa_com_padroes(
        db, nome_fantasia=f"Loja {uuid.uuid4().hex[:6]}", usuario_dono_id=usuario.id
    )
    return criada.empresa.id, usuario.id


def criar_produto(db, empresa_id, nome, preco, custo="20"):
    produto = produtos_service.criar_produto(
        db, empresa_id, nome=nome, unidade_codigo="un", vendavel=True, preco_venda=Decimal(preco)
    )
    estoque_service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("100"), custo_unitario=Decimal(custo)
    )
    return produto


def vender(db, empresa_id, usuario_id, produto, quantidade, forma=FormaPagamento.DINHEIRO, **kw):
    venda = vendas_service.abrir_venda(db, empresa_id, vendedor_usuario_id=usuario_id, **kw)
    vendas_service.adicionar_item(
        db, empresa_id, venda.id, produto_id=produto.id, quantidade=Decimal(quantidade)
    )
    return venda, forma


def fechar(db, empresa_id, venda, forma=FormaPagamento.DINHEIRO):
    total = venda.total
    return vendas_service.fechar_venda(
        db, empresa_id, venda.id, pagamentos=[{"forma": forma, "valor": total}]
    )


def periodo_de_hoje():
    hoje = vendas_service.hoje()
    return hoje, hoje


def test_resumo_soma_so_vendas_fechadas(db):
    empresa_id, usuario_id = criar_empresa(db)
    vaso = criar_produto(db, empresa_id, "Vaso", "50")
    cachepo = criar_produto(db, empresa_id, "Cachepô", "30", custo="10")

    v1, _ = vender(db, empresa_id, usuario_id, vaso, "2")  # 100
    fechar(db, empresa_id, v1, FormaPagamento.DINHEIRO)
    v2, _ = vender(db, empresa_id, usuario_id, cachepo, "1")  # 30
    fechar(db, empresa_id, v2, FormaPagamento.PIX)
    v3, _ = vender(db, empresa_id, usuario_id, vaso, "1")
    vendas_service.cancelar_venda(db, empresa_id, v3.id)
    vender(db, empresa_id, usuario_id, vaso, "1")  # aberta: não conta

    inicio, fim = periodo_de_hoje()
    resumo = vendas_service.resumo_do_periodo(db, empresa_id, inicio=inicio, fim=fim)

    assert resumo.quantidade_vendas == 2
    assert resumo.faturamento == Decimal("130.00")
    assert resumo.ticket_medio == Decimal("65.00")
    assert resumo.cancelamentos == 1
    assert resumo.custo_total == Decimal("50.00")  # 2 × 20 + 1 × 10
    assert [(d.data, d.quantidade, d.faturamento) for d in resumo.por_dia] == [
        (inicio, 2, Decimal("130.00"))
    ]
    assert [(m.produto_id, m.quantidade, m.receita) for m in resumo.mais_vendidos] == [
        (vaso.id, Decimal("2.0000"), Decimal("100.00")),
        (cachepo.id, Decimal("1.0000"), Decimal("30.00")),
    ]
    assert dict(resumo.por_forma_pagamento) == {
        FormaPagamento.DINHEIRO: Decimal("100.00"),
        FormaPagamento.PIX: Decimal("30.00"),
    }


def test_resumo_respeita_o_periodo(db):
    empresa_id, usuario_id = criar_empresa(db)
    vaso = criar_produto(db, empresa_id, "Vaso", "50")
    antiga = datetime.now(UTC) - timedelta(days=10)

    velha, _ = vender(db, empresa_id, usuario_id, vaso, "1", ocorrido_em=antiga)
    fechar(db, empresa_id, velha)
    nova, _ = vender(db, empresa_id, usuario_id, vaso, "1")
    fechar(db, empresa_id, nova)

    hoje = vendas_service.hoje()
    so_hoje = vendas_service.resumo_do_periodo(db, empresa_id, inicio=hoje, fim=hoje)
    assert so_hoje.quantidade_vendas == 1

    tudo = vendas_service.resumo_do_periodo(
        db, empresa_id, inicio=hoje - timedelta(days=30), fim=hoje
    )
    assert tudo.quantidade_vendas == 2
    assert len(tudo.por_dia) == 2


def test_resumo_vazio_nao_quebra(db):
    empresa_id, _ = criar_empresa(db)
    inicio, fim = periodo_de_hoje()

    resumo = vendas_service.resumo_do_periodo(db, empresa_id, inicio=inicio, fim=fim)

    assert resumo.quantidade_vendas == 0
    assert resumo.faturamento == Decimal("0.00")
    assert resumo.ticket_medio is None
    assert resumo.por_dia == [] and resumo.mais_vendidos == []


def test_resumo_nao_mistura_empresas(db):
    empresa_a, usuario_a = criar_empresa(db)
    empresa_b, _ = criar_empresa(db)
    produto = criar_produto(db, empresa_a, "Vaso", "50")
    venda, _ = vender(db, empresa_a, usuario_a, produto, "1")
    fechar(db, empresa_a, venda)

    inicio, fim = periodo_de_hoje()
    assert vendas_service.resumo_do_periodo(db, empresa_b, inicio=inicio, fim=fim).quantidade_vendas == 0
    assert vendas_service.resumo_do_periodo(db, empresa_a, inicio=inicio, fim=fim).quantidade_vendas == 1


def test_resumo_valida_periodo(db):
    empresa_id, _ = criar_empresa(db)
    hoje = vendas_service.hoje()
    with pytest.raises(RegraDeNegocio):
        vendas_service.resumo_do_periodo(db, empresa_id, inicio=hoje, fim=hoje - timedelta(days=1))
    with pytest.raises(RegraDeNegocio):
        vendas_service.resumo_do_periodo(
            db, empresa_id, inicio=hoje - timedelta(days=400), fim=hoje
        )


def test_permissao_de_relatorios_so_no_gerente_e_dono():
    assert "relatorios.ver" in catalogo()
    por_codigo = {papel.codigo: papel for papel in PAPEIS_PADRAO}
    assert "relatorios.ver" in por_codigo["gerente"].permissoes
    assert "relatorios.ver" not in por_codigo["caixa"].permissoes
    assert "relatorios.ver" not in por_codigo["estoquista"].permissoes


def test_endpoint_resumo_pela_api(cliente):
    from tests.test_auth import cabecalho, cadastrar

    dados = cadastrar(cliente)
    cab = cabecalho(dados["tokens"]["access_token"])
    api = "/api/v1"

    produto = cliente.post(
        f"{api}/produtos",
        headers=cab,
        json={"nome": "Vaso", "unidade_codigo": "un", "vendavel": True, "preco_venda": "50"},
    )
    assert produto.status_code == 201, produto.text
    produto_id = produto.json()["id"]
    cliente.post(
        f"{api}/estoque/produtos/{produto_id}/entradas",
        headers=cab,
        json={"quantidade": "10", "custo_unitario": "20"},
    )
    venda = cliente.post(f"{api}/vendas", headers=cab, json={}).json()
    cliente.post(
        f"{api}/vendas/{venda['id']}/itens",
        headers=cab,
        json={"produto_id": produto_id, "quantidade": "2"},
    )
    fechada = cliente.post(
        f"{api}/vendas/{venda['id']}/fechar",
        headers=cab,
        json={"pagamentos": [{"forma": "pix", "valor": "100"}]},
    )
    assert fechada.status_code == 200, fechada.text

    resposta = cliente.get(f"{api}/relatorios/resumo", headers=cab)

    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["quantidade_vendas"] == 1
    assert Decimal(corpo["faturamento"]) == Decimal("100")
    assert Decimal(corpo["lucro_bruto"]) == Decimal("60")  # Dono vê custo
    assert Decimal(corpo["margem_percentual"]) == Decimal("60")
    assert corpo["mais_vendidos"][0]["nome"] == "Vaso"
    assert corpo["por_forma_pagamento"][0]["forma"] == "pix"

    sem_datas_invertidas = cliente.get(
        f"{api}/relatorios/resumo?inicio=2026-10-10&fim=2026-10-01", headers=cab
    )
    assert sem_datas_invertidas.status_code == 422 or sem_datas_invertidas.status_code == 400


def test_clientes_novos_recorrentes_e_sem_cliente(db):
    from app.modules.clientes import service as clientes_service

    empresa_id, usuario_id = criar_empresa(db)
    vaso = criar_produto(db, empresa_id, "Vaso", "50")
    antiga = datetime.now(UTC) - timedelta(days=20)

    ana = clientes_service.criar_cliente(db, empresa_id, nome="Ana")
    bia = clientes_service.criar_cliente(db, empresa_id, nome="Bia")
    caio = clientes_service.criar_cliente(db, empresa_id, nome="Caio")

    # Ana: já comprava antes do período (recorrente) e comprou 2× no período.
    velha, _ = vender(db, empresa_id, usuario_id, vaso, "1", cliente_id=ana.id, ocorrido_em=antiga)
    fechar(db, empresa_id, velha)
    for _ in range(2):
        v, _ = vender(db, empresa_id, usuario_id, vaso, "1", cliente_id=ana.id)
        fechar(db, empresa_id, v)  # 2 × 50
    # Bia: primeira compra no período (nova), 100.
    v, _ = vender(db, empresa_id, usuario_id, vaso, "2", cliente_id=bia.id)
    fechar(db, empresa_id, v)
    # Caio só tem ticket aberto: não conta.
    vender(db, empresa_id, usuario_id, vaso, "1", cliente_id=caio.id)
    # Venda sem cliente identificado.
    v, _ = vender(db, empresa_id, usuario_id, vaso, "1")
    fechar(db, empresa_id, v)

    hoje = vendas_service.hoje()
    r = vendas_service.resumo_de_clientes(db, empresa_id, inicio=hoje - timedelta(days=10), fim=hoje)

    assert r.clientes_que_compraram == 2
    assert (r.novos, r.recorrentes) == (1, 1)
    assert r.compras_de_clientes == 3
    assert r.valor_de_clientes == Decimal("200.00")
    assert r.ticket_medio == Decimal("66.67")
    assert r.compras_por_cliente == Decimal("1.5")
    assert (r.vendas_sem_cliente, r.valor_sem_cliente) == (1, Decimal("50.00"))
    # Empate em valor (100 cada): a ordem entre Ana e Bia não é garantida.
    assert {(m.cliente_id, m.compras, m.valor) for m in r.melhores} == {
        (ana.id, 2, Decimal("100.00")),
        (bia.id, 1, Decimal("100.00")),
    }


def test_clientes_vazio_nao_quebra(db):
    empresa_id, _ = criar_empresa(db)
    hoje = vendas_service.hoje()
    r = vendas_service.resumo_de_clientes(db, empresa_id, inicio=hoje, fim=hoje)
    assert r.clientes_que_compraram == 0 and r.ticket_medio is None and r.melhores == []


def test_impacto_de_descontos(db):
    empresa_id, usuario_id = criar_empresa(db)
    vaso = criar_produto(db, empresa_id, "Vaso", "100", custo="40")

    # 2 vasos com 10% de desconto: tabela 200, desconto 20, final 180, custo 80.
    venda = vendas_service.abrir_venda(db, empresa_id, vendedor_usuario_id=usuario_id)
    vendas_service.adicionar_item(
        db, empresa_id, venda.id, produto_id=vaso.id, quantidade=Decimal("2"),
        desconto_percentual=Decimal("10"),
    )
    fechar(db, empresa_id, venda)
    # 1 vaso sem desconto: tabela 100, final 100, custo 40.
    v2, _ = vender(db, empresa_id, usuario_id, vaso, "1")
    fechar(db, empresa_id, v2)

    hoje = vendas_service.hoje()
    r = vendas_service.resumo_de_descontos(db, empresa_id, inicio=hoje, fim=hoje)

    assert r.receita_de_tabela == Decimal("300.00")
    assert r.descontos == Decimal("20.00")
    assert r.receita_final == Decimal("280.00")
    assert r.percentual_de_desconto == Decimal("6.67")
    assert (r.itens_com_desconto, r.vendas_com_desconto) == (1, 1)
    assert r.lucro_sem_desconto == Decimal("180.00")  # 300 - 120
    assert r.lucro_com_desconto == Decimal("160.00")  # 280 - 120
    assert [(p.produto_id, p.desconto, p.percentual) for p in r.produtos] == [
        (vaso.id, Decimal("20.00"), Decimal("10.00"))
    ]


def test_descontos_sem_vendas_nao_quebra(db):
    empresa_id, _ = criar_empresa(db)
    hoje = vendas_service.hoje()
    r = vendas_service.resumo_de_descontos(db, empresa_id, inicio=hoje, fim=hoje)
    assert r.descontos == Decimal("0.00") and r.percentual_de_desconto is None and r.produtos == []


def test_csv_neutraliza_formulas_e_formata_para_excel_brasileiro():
    from decimal import Decimal as D

    from app.modules.relatorios import exportacao

    assert exportacao.texto("=HYPERLINK(\"x\")") == "'=HYPERLINK(\"x\")"
    assert exportacao.texto("-1+2") == "'-1+2"
    assert exportacao.texto("Vaso") == "Vaso"
    assert exportacao.numero(D("1234.5")) == "1234,50"
    conteudo = exportacao.gerar_csv(["A", "B"], [["ç", "1,00"]])
    assert conteudo.startswith("﻿A;B\r\n") and "ç;1,00" in conteudo


def test_exportar_vendas_em_csv_pela_api(cliente):
    from tests.test_auth import cabecalho, cadastrar

    dados = cadastrar(cliente)
    cab = cabecalho(dados["tokens"]["access_token"])
    api = "/api/v1"

    produto = cliente.post(
        f"{api}/produtos",
        headers=cab,
        json={"nome": "=Vaso", "unidade_codigo": "un", "vendavel": True, "preco_venda": "50"},
    ).json()
    cliente.post(
        f"{api}/estoque/produtos/{produto['id']}/entradas",
        headers=cab,
        json={"quantidade": "10", "custo_unitario": "20"},
    )
    venda = cliente.post(f"{api}/vendas", headers=cab, json={}).json()
    cliente.post(
        f"{api}/vendas/{venda['id']}/itens",
        headers=cab,
        json={"produto_id": produto["id"], "quantidade": "2"},
    )
    cliente.post(
        f"{api}/vendas/{venda['id']}/fechar",
        headers=cab,
        json={
            "pagamentos": [
                {"forma": "cartao_credito", "valor": "60"},
                {"forma": "pix", "valor": "40"},
            ]
        },
    )

    resposta = cliente.get(f"{api}/relatorios/exportar/vendas", headers=cab)

    assert resposta.status_code == 200, resposta.text
    assert resposta.headers["content-type"].startswith("text/csv")
    assert "attachment" in resposta.headers["content-disposition"]
    linhas = resposta.content.decode("utf-8-sig").strip().split("\r\n")
    assert linhas[0].startswith("Venda;Data;Cliente;SKU;Produto")
    assert linhas[0].endswith("Custo unitário;Lucro do item")  # Dono vê custo
    assert len(linhas) == 2
    celulas = linhas[1].split(";")
    assert "'=Vaso" in celulas  # fórmula neutralizada
    assert "2,0000" in celulas and "100,00" in celulas
    assert "Cartão de crédito + Pix" in celulas
    assert celulas[-2] == "20,000000" and celulas[-1] == "60,00"
