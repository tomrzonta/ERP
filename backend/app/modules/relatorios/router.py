"""Rotas de relatórios. Compõe os services de vendas e produtos."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import PermissaoNegada
from app.modules.assinaturas.regras import Recurso
from app.modules.auth.dependencias import Contexto, requer_permissao, requer_recurso
from app.modules.clientes import service as clientes_service
from app.modules.produtos import service as produtos_service
from app.modules.estoque import service as estoque_service
from app.modules.relatorios import exportacao
from app.modules.relatorios.schemas import (
    InsumoConsumidoSaida,
    ResumoInsumosSaida,
    ProdutoComDescontoSaida,
    ResumoDescontosSaida,
    ClienteDoPeriodoSaida,
    ResumoClientesSaida,
    DiaVendasSaida,
    FormaPagamentoSaida,
    ProdutoVendidoSaida,
    ResumoSaida,
)
from app.modules.vendas import service as vendas_service
from app.shared.money import to_money

router = APIRouter(prefix="/relatorios", tags=["relatorios"])


@router.get("/resumo", response_model=ResumoSaida)
def resumo(
    inicio: date | None = None,
    fim: date | None = None,
    contexto: Contexto = Depends(requer_permissao("relatorios.ver")),
    db: Session = Depends(get_db),
):
    """Sem datas, devolve os últimos 30 dias (hoje incluído)."""
    hoje = vendas_service.hoje()
    fim = fim or hoje
    inicio = inicio or fim - timedelta(days=29)
    dados = vendas_service.resumo_do_periodo(db, contexto.empresa_id, inicio=inicio, fim=fim)

    mais_vendidos = []
    for item in dados.mais_vendidos:
        produto = produtos_service.obter_produto(db, contexto.empresa_id, item.produto_id)
        mais_vendidos.append(
            ProdutoVendidoSaida(
                produto_id=produto.id,
                nome=produto.nome,
                quantidade=item.quantidade,
                unidade_codigo=produto.unidade_codigo,
                receita=item.receita,
            )
        )

    lucro = margem = None
    if "produtos.ver_custo" in contexto.permissoes:
        lucro = to_money(dados.faturamento - dados.custo_total)
        if dados.faturamento > 0:
            margem = to_money(lucro / dados.faturamento * 100)

    return ResumoSaida(
        inicio=dados.inicio,
        fim=dados.fim,
        quantidade_vendas=dados.quantidade_vendas,
        faturamento=dados.faturamento,
        ticket_medio=dados.ticket_medio,
        descontos=dados.descontos,
        cancelamentos=dados.cancelamentos,
        lucro_bruto=lucro,
        margem_percentual=margem,
        por_dia=[DiaVendasSaida(**vars(dia)) for dia in dados.por_dia],
        mais_vendidos=mais_vendidos,
        por_forma_pagamento=[
            FormaPagamentoSaida(forma=forma, valor=valor)
            for forma, valor in dados.por_forma_pagamento
        ],
    )


@router.get("/clientes", response_model=ResumoClientesSaida)
def resumo_de_clientes(
    inicio: date | None = None,
    fim: date | None = None,
    contexto: Contexto = Depends(requer_recurso(Recurso.RELATORIOS_CLIENTES)),
    db: Session = Depends(get_db),
):
    """Novos vs. recorrentes, ticket médio e melhores clientes (Pro)."""
    if "relatorios.ver" not in contexto.permissoes:
        raise PermissaoNegada("Você não tem permissão para esta ação.")
    fim = fim or vendas_service.hoje()
    inicio = inicio or fim - timedelta(days=29)
    dados = vendas_service.resumo_de_clientes(db, contexto.empresa_id, inicio=inicio, fim=fim)

    melhores = [
        ClienteDoPeriodoSaida(
            cliente_id=item.cliente_id,
            nome=clientes_service.obter_cliente(db, contexto.empresa_id, item.cliente_id).nome,
            compras=item.compras,
            valor=item.valor,
        )
        for item in dados.melhores
    ]
    return ResumoClientesSaida(**{**vars(dados), "melhores": melhores})


@router.get("/descontos", response_model=ResumoDescontosSaida)
def resumo_de_descontos(
    inicio: date | None = None,
    fim: date | None = None,
    contexto: Contexto = Depends(requer_recurso(Recurso.MARGEM_AVANCADA)),
    db: Session = Depends(get_db),
):
    """Impacto dos descontos na margem (Pro)."""
    if "relatorios.ver" not in contexto.permissoes:
        raise PermissaoNegada("Você não tem permissão para esta ação.")
    fim = fim or vendas_service.hoje()
    inicio = inicio or fim - timedelta(days=29)
    dados = vendas_service.resumo_de_descontos(db, contexto.empresa_id, inicio=inicio, fim=fim)

    produtos = [
        ProdutoComDescontoSaida(
            produto_id=item.produto_id,
            nome=produtos_service.obter_produto(db, contexto.empresa_id, item.produto_id).nome,
            desconto=item.desconto,
            percentual=item.percentual,
        )
        for item in dados.produtos
    ]

    sem = com = cedido = None
    if "produtos.ver_custo" in contexto.permissoes:
        sem = to_money(dados.lucro_sem_desconto)
        com = to_money(dados.lucro_com_desconto)
        if sem > 0:
            cedido = to_money(dados.descontos / sem * 100)

    return ResumoDescontosSaida(
        inicio=dados.inicio,
        fim=dados.fim,
        receita_de_tabela=dados.receita_de_tabela,
        descontos=dados.descontos,
        receita_final=dados.receita_final,
        percentual_de_desconto=dados.percentual_de_desconto,
        itens_com_desconto=dados.itens_com_desconto,
        vendas_com_desconto=dados.vendas_com_desconto,
        lucro_sem_desconto=sem,
        lucro_com_desconto=com,
        lucro_cedido_percentual=cedido,
        produtos=produtos,
    )


@router.get("/insumos", response_model=ResumoInsumosSaida)
def resumo_de_insumos(
    inicio: date | None = None,
    fim: date | None = None,
    contexto: Contexto = Depends(requer_recurso(Recurso.MARGEM_AVANCADA)),
    db: Session = Depends(get_db),
):
    """Consumo e perdas de insumos no período (Pro)."""
    if "relatorios.ver" not in contexto.permissoes:
        raise PermissaoNegada("Você não tem permissão para esta ação.")
    fim = fim or vendas_service.hoje()
    inicio = inicio or fim - timedelta(days=29)
    itens = estoque_service.consumo_de_insumos(db, contexto.empresa_id, inicio=inicio, fim=fim)

    ve_custo = "produtos.ver_custo" in contexto.permissoes
    return ResumoInsumosSaida(
        inicio=inicio,
        fim=fim,
        custo_total=to_money(sum((i.custo_total for i in itens), to_money(0))) if ve_custo else None,
        custo_dos_ajustes=(
            to_money(sum((i.custo_dos_ajustes for i in itens), to_money(0))) if ve_custo else None
        ),
        insumos=[
            InsumoConsumidoSaida(
                produto_id=i.produto.id,
                nome=i.produto.nome,
                unidade_codigo=i.produto.unidade_codigo,
                consumido_em_montagens=i.consumido_em_montagens,
                baixado_por_ajuste=i.baixado_por_ajuste,
                custo_das_montagens=i.custo_das_montagens if ve_custo else None,
                custo_dos_ajustes=i.custo_dos_ajustes if ve_custo else None,
                custo_total=i.custo_total if ve_custo else None,
            )
            for i in itens
        ],
    )


@router.get("/exportar/vendas")
def exportar_vendas(
    inicio: date | None = None,
    fim: date | None = None,
    contexto: Contexto = Depends(requer_recurso(Recurso.EXPORTACAO_RELATORIOS)),
    db: Session = Depends(get_db),
):
    """CSV com uma linha por item de venda fechada no período (Pro).
    Custo e lucro só entram pra quem tem `produtos.ver_custo`."""
    if "relatorios.ver" not in contexto.permissoes:
        raise PermissaoNegada("Você não tem permissão para esta ação.")
    fim = fim or vendas_service.hoje()
    inicio = inicio or fim - timedelta(days=29)
    linhas = vendas_service.itens_vendidos_no_periodo(
        db, contexto.empresa_id, inicio=inicio, fim=fim
    )
    ve_custo = "produtos.ver_custo" in contexto.permissoes

    produtos: dict = {}
    clientes: dict = {}

    def produto(produto_id):
        if produto_id not in produtos:
            produtos[produto_id] = produtos_service.obter_produto(
                db, contexto.empresa_id, produto_id
            )
        return produtos[produto_id]

    def cliente(cliente_id):
        if cliente_id is None:
            return ""
        if cliente_id not in clientes:
            clientes[cliente_id] = clientes_service.obter_cliente(
                db, contexto.empresa_id, cliente_id
            ).nome
        return clientes[cliente_id]

    formas = {
        "dinheiro": "Dinheiro",
        "cartao": "Cartão",
        "cartao_credito": "Cartão de crédito",
        "cartao_debito": "Cartão de débito",
        "pix": "Pix",
    }
    cabecalho = [
        "Venda", "Data", "Cliente", "SKU", "Produto", "Unidade", "Quantidade",
        "Preço de tabela", "Desconto por unidade", "Preço final", "Total do item",
        "Pagamento",
    ]  # fmt: skip
    if ve_custo:
        cabecalho += ["Custo unitário", "Lucro do item"]

    corpo = []
    for linha in linhas:
        p = produto(linha.produto_id)
        total = linha.quantidade * linha.preco_final
        registro = [
            linha.venda_numero,
            exportacao.data_hora(linha.ocorrido_em),
            exportacao.texto(cliente(linha.cliente_id)),
            exportacao.texto(p.sku),
            exportacao.texto(p.nome),
            p.unidade_codigo,
            exportacao.numero(linha.quantidade, 4),
            exportacao.numero(linha.preco_tabela),
            exportacao.numero(linha.desconto),
            exportacao.numero(linha.preco_final),
            exportacao.numero(to_money(total)),
            " + ".join(formas.get(f.value, f.value) for f in linha.formas_pagamento),
        ]
        if ve_custo:
            custo = linha.custo_unitario or 0
            registro += [
                exportacao.numero(to_money(custo), 6) if linha.custo_unitario is not None else "",
                exportacao.numero(to_money(total - linha.quantidade * custo)),
            ]
        corpo.append(registro)

    conteudo = exportacao.gerar_csv(cabecalho, corpo)
    nome = f"vendas_{inicio.isoformat()}_a_{fim.isoformat()}.csv"
    return Response(
        content=conteudo,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )
