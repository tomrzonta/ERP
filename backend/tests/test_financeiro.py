import uuid
from decimal import Decimal

import pytest

from app.core.exceptions import LimiteDoPlano, NaoEncontrado, RegraDeNegocio
from app.modules.empresas.service import criar_empresa_com_padroes
from app.modules.estoque import service as estoque_service
from app.modules.financeiro import service
from app.modules.financeiro.models import StatusCaixa, TipoLancamento
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


def criar_produto(db, empresa_id, nome="Vaso", **kwargs):
    kwargs.setdefault("unidade_codigo", "un")
    kwargs.setdefault("vendavel", True)
    kwargs.setdefault("preco_venda", Decimal("50"))
    return produtos_service.criar_produto(db, empresa_id, nome=nome, **kwargs)


def pagamento(valor: str, forma: FormaPagamento = FormaPagamento.DINHEIRO) -> dict:
    return {"forma": forma, "valor": Decimal(valor)}


def test_abrir_caixa_cria_sessao_aberta(db):
    empresa_id, usuario_id = criar_empresa(db)

    caixa = service.abrir_caixa(db, empresa_id, usuario_id=usuario_id, valor_inicial=Decimal("100"))

    assert caixa.status is StatusCaixa.ABERTO
    assert caixa.valor_inicial == Decimal("100.00")
    assert service.caixa_aberto(db, empresa_id).id == caixa.id


def test_nao_pode_abrir_dois_caixas_no_limite_do_plano(db):
    from app.modules.assinaturas.models import PlanoRegra, TipoRegra
    from app.modules.assinaturas.repository import plano_por_codigo
    from app.modules.assinaturas.regras import PLANO_PRO

    empresa_id, usuario_id = criar_empresa(db)
    pro = plano_por_codigo(db, PLANO_PRO)
    regra = db.get(PlanoRegra, (pro.id, "max_caixas_offline"))
    assert regra.tipo is TipoRegra.LIMITE
    regra.valor = 1
    db.flush()

    service.abrir_caixa(db, empresa_id, usuario_id=usuario_id, valor_inicial=Decimal("100"))
    with pytest.raises(LimiteDoPlano):
        service.abrir_caixa(db, empresa_id, usuario_id=usuario_id, valor_inicial=Decimal("50"))


def test_fechar_caixa_sem_diferenca(db):
    empresa_id, usuario_id = criar_empresa(db)
    caixa = service.abrir_caixa(db, empresa_id, usuario_id=usuario_id, valor_inicial=Decimal("100"))
    service.lancar_manual(
        db,
        empresa_id,
        caixa.id,
        usuario_id=usuario_id,
        tipo=TipoLancamento.ENTRADA,
        valor=Decimal("30"),
        forma_pagamento=FormaPagamento.DINHEIRO,
    )

    fechado = service.fechar_caixa(
        db, empresa_id, caixa.id, usuario_id=usuario_id, valor_contado=Decimal("130")
    )

    assert fechado.status is StatusCaixa.FECHADO
    resumo = service.resumo_caixa(db, fechado)
    assert resumo.saldo_esperado_dinheiro == Decimal("130.00")
    assert resumo.diferenca == Decimal("0.00")


def test_fechar_caixa_com_diferenca(db):
    empresa_id, usuario_id = criar_empresa(db)
    caixa = service.abrir_caixa(db, empresa_id, usuario_id=usuario_id, valor_inicial=Decimal("100"))

    fechado = service.fechar_caixa(
        db, empresa_id, caixa.id, usuario_id=usuario_id, valor_contado=Decimal("95")
    )

    resumo = service.resumo_caixa(db, fechado)
    assert resumo.diferenca == Decimal("-5.00")


def test_resumo_so_conta_dinheiro_no_saldo_esperado(db):
    empresa_id, usuario_id = criar_empresa(db)
    caixa = service.abrir_caixa(db, empresa_id, usuario_id=usuario_id, valor_inicial=Decimal("100"))
    service.lancar_manual(
        db,
        empresa_id,
        caixa.id,
        usuario_id=usuario_id,
        tipo=TipoLancamento.ENTRADA,
        valor=Decimal("200"),
        forma_pagamento=FormaPagamento.CARTAO,
    )

    resumo = service.resumo_caixa(db, caixa)

    # Total entradas conta tudo; saldo esperado em dinheiro ignora o cartão.
    assert resumo.total_entradas == Decimal("200.00")
    assert resumo.saldo_esperado_dinheiro == Decimal("100.00")


def test_nao_pode_lancar_em_caixa_fechado(db):
    empresa_id, usuario_id = criar_empresa(db)
    caixa = service.abrir_caixa(db, empresa_id, usuario_id=usuario_id, valor_inicial=Decimal("100"))
    service.fechar_caixa(db, empresa_id, caixa.id, usuario_id=usuario_id, valor_contado=Decimal("100"))

    with pytest.raises(RegraDeNegocio):
        service.lancar_manual(
            db,
            empresa_id,
            caixa.id,
            usuario_id=usuario_id,
            tipo=TipoLancamento.SAIDA,
            valor=Decimal("10"),
            forma_pagamento=FormaPagamento.DINHEIRO,
        )


def test_venda_fechada_com_caixa_aberto_gera_lancamento_automatico(db):
    empresa_id, usuario_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))
    estoque_service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("10"), custo_unitario=Decimal("20")
    )
    caixa = service.abrir_caixa(db, empresa_id, usuario_id=usuario_id, valor_inicial=Decimal("0"))

    venda = vendas_service.abrir_venda(db, empresa_id, vendedor_usuario_id=usuario_id)
    vendas_service.adicionar_item(
        db, empresa_id, venda.id, produto_id=produto.id, quantidade=Decimal("1")
    )
    vendas_service.fechar_venda(db, empresa_id, venda.id, pagamentos=[pagamento("50")])

    lancamentos = service.listar_lancamentos(db, caixa.id)
    assert len(lancamentos) == 1
    assert lancamentos[0].valor == Decimal("50.00")
    assert lancamentos[0].venda_id == venda.id


def test_venda_fechada_sem_caixa_aberto_nao_gera_lancamento(db):
    empresa_id, usuario_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))
    estoque_service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("10"), custo_unitario=Decimal("20")
    )

    venda = vendas_service.abrir_venda(db, empresa_id, vendedor_usuario_id=usuario_id)
    vendas_service.adicionar_item(
        db, empresa_id, venda.id, produto_id=produto.id, quantidade=Decimal("1")
    )
    # Não deve estourar erro nenhum mesmo sem caixa aberto.
    vendas_service.fechar_venda(db, empresa_id, venda.id, pagamentos=[pagamento("50")])

    assert service.caixa_aberto(db, empresa_id) is None


def test_venda_offline_sincronizada_tambem_gera_lancamento(db):
    empresa_id, usuario_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("50"))
    caixa = service.abrir_caixa(db, empresa_id, usuario_id=usuario_id, valor_inicial=Decimal("0"))

    from datetime import UTC, datetime

    vendas_service.sincronizar_venda_offline(
        db,
        empresa_id,
        id=uuid.uuid4(),
        vendedor_usuario_id=usuario_id,
        itens=[
            {
                "produto_id": produto.id,
                "quantidade": Decimal("1"),
                "unidade_id": None,
                "preco_tabela": Decimal("50"),
                "desconto_percentual": Decimal("0"),
            }
        ],
        pagamentos=[pagamento("50")],
        ocorrido_em=datetime.now(UTC),
    )

    lancamentos = service.listar_lancamentos(db, caixa.id)
    assert len(lancamentos) == 1


def test_caixa_de_outra_empresa_nao_e_encontrado(db):
    primeira, usuario_id = criar_empresa(db)
    segunda, _ = criar_empresa(db)
    caixa = service.abrir_caixa(db, primeira, usuario_id=usuario_id, valor_inicial=Decimal("0"))

    with pytest.raises(NaoEncontrado):
        service.obter_caixa(db, segunda, caixa.id)


def test_sincronizar_lancamento_offline_entra_no_caixa_aberto_e_e_idempotente(db):
    from datetime import UTC, datetime

    empresa_id, usuario_id = criar_empresa(db)
    caixa = service.abrir_caixa(db, empresa_id, usuario_id=usuario_id, valor_inicial=Decimal("0"))
    id_local = uuid.uuid4()
    dados = dict(
        id=id_local,
        usuario_id=usuario_id,
        tipo=TipoLancamento.SAIDA,
        valor=Decimal("20"),
        forma_pagamento=FormaPagamento.DINHEIRO,
        ocorrido_em=datetime.now(UTC),
        descricao="sangria",
    )

    primeiro = service.sincronizar_lancamento_offline(db, empresa_id, **dados)
    segundo = service.sincronizar_lancamento_offline(db, empresa_id, **dados)

    assert primeiro.id == segundo.id == id_local
    assert len(service.listar_lancamentos(db, caixa.id)) == 1


def test_sincronizar_lancamento_offline_sem_caixa_aberto_recusa(db):
    from datetime import UTC, datetime

    empresa_id, usuario_id = criar_empresa(db)

    with pytest.raises(RegraDeNegocio):
        service.sincronizar_lancamento_offline(
            db,
            empresa_id,
            id=uuid.uuid4(),
            usuario_id=usuario_id,
            tipo=TipoLancamento.ENTRADA,
            valor=Decimal("10"),
            forma_pagamento=FormaPagamento.DINHEIRO,
            ocorrido_em=datetime.now(UTC),
        )


# --- Contas a pagar e a receber (Pro) -----------------------------------


def test_conta_nasce_aberta_e_dá_baixa(db):
    from datetime import date

    from app.modules.financeiro.models import StatusConta, TipoConta

    empresa_id, usuario_id = criar_empresa(db)
    conta = service.criar_conta(
        db, empresa_id, usuario_id=usuario_id, tipo=TipoConta.PAGAR,
        descricao="Aluguel", valor=Decimal("800"), vencimento=date(2026, 10, 5),
        contraparte="Imobiliária",
    )
    assert conta.status is StatusConta.ABERTA

    paga = service.marcar_paga(db, empresa_id, conta.id, pago_em=date(2026, 10, 4))
    assert paga.status is StatusConta.PAGA
    assert paga.pago_em == date(2026, 10, 4)

    with pytest.raises(RegraDeNegocio):
        service.marcar_paga(db, empresa_id, conta.id)
    with pytest.raises(RegraDeNegocio):
        service.cancelar_conta(db, empresa_id, conta.id)


def test_conta_valida_valor_e_descricao(db):
    from datetime import date

    from app.modules.financeiro.models import TipoConta

    empresa_id, usuario_id = criar_empresa(db)
    base = dict(usuario_id=usuario_id, tipo=TipoConta.RECEBER, vencimento=date(2026, 10, 5))
    with pytest.raises(RegraDeNegocio):
        service.criar_conta(db, empresa_id, descricao="X", valor=Decimal("0"), **base)
    with pytest.raises(RegraDeNegocio):
        service.criar_conta(db, empresa_id, descricao="  ", valor=Decimal("10"), **base)


def test_conta_de_outra_empresa_nao_e_encontrada(db):
    from datetime import date

    from app.modules.financeiro.models import TipoConta

    empresa_a, usuario_a = criar_empresa(db)
    empresa_b, _ = criar_empresa(db)
    conta = service.criar_conta(
        db, empresa_a, usuario_id=usuario_a, tipo=TipoConta.PAGAR,
        descricao="Luz", valor=Decimal("90"), vencimento=date(2026, 10, 5),
    )
    with pytest.raises(NaoEncontrado):
        service.obter_conta(db, empresa_b, conta.id)
    assert service.listar_contas(db, empresa_b) == []


def test_listar_filtra_por_tipo_e_status(db):
    from datetime import date

    from app.modules.financeiro.models import StatusConta, TipoConta

    empresa_id, usuario_id = criar_empresa(db)
    for tipo, dia in ((TipoConta.PAGAR, 10), (TipoConta.RECEBER, 5)):
        service.criar_conta(
            db, empresa_id, usuario_id=usuario_id, tipo=tipo,
            descricao=tipo.value, valor=Decimal("10"), vencimento=date(2026, 10, dia),
        )
    cancelada = service.criar_conta(
        db, empresa_id, usuario_id=usuario_id, tipo=TipoConta.PAGAR,
        descricao="x", valor=Decimal("1"), vencimento=date(2026, 10, 1),
    )
    service.cancelar_conta(db, empresa_id, cancelada.id)

    assert len(service.listar_contas(db, empresa_id)) == 3
    assert len(service.listar_contas(db, empresa_id, tipo=TipoConta.PAGAR)) == 2
    abertas = service.listar_contas(db, empresa_id, status=StatusConta.ABERTA)
    assert [c.descricao for c in abertas] == ["receber", "pagar"]  # por vencimento


def test_fluxo_projetado_acumula_e_separa_atrasadas(db):
    from datetime import date

    from app.modules.financeiro.models import TipoConta

    empresa_id, usuario_id = criar_empresa(db)
    hoje = date(2026, 10, 10)

    def conta(tipo, valor, dia):
        service.criar_conta(
            db, empresa_id, usuario_id=usuario_id, tipo=tipo,
            descricao="c", valor=Decimal(valor), vencimento=date(2026, 10, dia),
        )

    conta(TipoConta.PAGAR, "100", 8)      # atrasada
    conta(TipoConta.RECEBER, "30", 9)     # atrasada
    conta(TipoConta.RECEBER, "200", 10)   # hoje
    conta(TipoConta.PAGAR, "50", 11)      # amanhã
    conta(TipoConta.PAGAR, "999", 20)     # fora do período de 3 dias

    fluxo = service.fluxo_projetado(db, empresa_id, dias=3, a_partir_de=hoje)

    assert fluxo.atrasadas_a_pagar == Decimal("100.00")
    assert fluxo.atrasadas_a_receber == Decimal("30.00")
    assert [d.data.day for d in fluxo.dias] == [10, 11, 12]
    # -100 + 30 (atrasadas) + 200 = 130; depois -50 = 80; dia 12 sem movimento
    assert [d.saldo_acumulado for d in fluxo.dias] == [
        Decimal("130.00"), Decimal("80.00"), Decimal("80.00"),
    ]


def test_fluxo_projetado_valida_periodo(db):
    empresa_id, _ = criar_empresa(db)
    with pytest.raises(RegraDeNegocio):
        service.fluxo_projetado(db, empresa_id, dias=0)


def test_recurso_de_contas_e_do_pro_e_nao_do_base(db):
    from app.modules.assinaturas.models import PlanoRegra
    from app.modules.assinaturas.regras import PLANO_BASE, PLANO_PRO
    from app.modules.assinaturas.repository import plano_por_codigo

    pro = plano_por_codigo(db, PLANO_PRO)
    base = plano_por_codigo(db, PLANO_BASE)
    assert db.get(PlanoRegra, (pro.id, "contas_pagar_receber")) is not None
    assert db.get(PlanoRegra, (base.id, "contas_pagar_receber")) is None


def test_historico_guarda_quem_abriu_e_quem_fechou(cliente):
    from tests.test_auth import cabecalho, cadastrar

    dados = cadastrar(cliente)
    cab = cabecalho(dados["tokens"]["access_token"])

    aberto = cliente.post("/api/v1/caixa/abrir", headers=cab, json={"valor_inicial": "50"})
    assert aberto.status_code == 201, aberto.text
    assert aberto.json()["aberto_por_nome"] == "Maria"
    assert aberto.json()["fechado_por_nome"] is None

    fechado = cliente.post(
        f"/api/v1/caixa/{aberto.json()['id']}/fechar", headers=cab, json={"valor_contado": "50"}
    )
    assert fechado.status_code == 200, fechado.text
    assert fechado.json()["aberto_por_nome"] == "Maria"
    assert fechado.json()["fechado_por_nome"] == "Maria"

    historico = cliente.get("/api/v1/caixa", headers=cab).json()
    assert historico[0]["fechado_por_nome"] == "Maria"


def test_cartao_credito_e_debito_como_formas_de_pagamento(db):
    empresa_id, usuario_id = criar_empresa(db)
    produto = criar_produto(db, empresa_id, preco_venda=Decimal("100"))
    estoque_service.registrar_entrada(
        db, empresa_id, produto.id, quantidade=Decimal("5"), custo_unitario=Decimal("10")
    )
    caixa = service.abrir_caixa(db, empresa_id, usuario_id=usuario_id, valor_inicial=Decimal("0"))

    venda = vendas_service.abrir_venda(db, empresa_id, vendedor_usuario_id=usuario_id)
    vendas_service.adicionar_item(
        db, empresa_id, venda.id, produto_id=produto.id, quantidade=Decimal("1")
    )
    vendas_service.fechar_venda(
        db,
        empresa_id,
        venda.id,
        pagamentos=[
            pagamento("60", FormaPagamento.CARTAO_CREDITO),
            pagamento("40", FormaPagamento.CARTAO_DEBITO),
        ],
    )

    formas = {p.forma for p in vendas_service.pagamentos_da_venda(db, venda.id)}
    assert formas == {FormaPagamento.CARTAO_CREDITO, FormaPagamento.CARTAO_DEBITO}
    lancados = {(l.forma_pagamento, l.valor) for l in service.listar_lancamentos(db, caixa.id)}
    assert lancados == {
        (FormaPagamento.CARTAO_CREDITO, Decimal("60.00")),
        (FormaPagamento.CARTAO_DEBITO, Decimal("40.00")),
    }
    # Cartão não entra na gaveta: o esperado em dinheiro segue só com o troco inicial.
    assert service.resumo_caixa(db, caixa).saldo_esperado_dinheiro == Decimal("0.00")
