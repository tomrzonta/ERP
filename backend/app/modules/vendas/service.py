"""Regras de negócio de vendas (tickets).

Uma venda nasce ABERTA: o caixa vai adicionando itens (cada um reserva o
estoque na hora — evita vender o que não tem) até fechar (paga, converte as
reservas em baixa de verdade) ou cancelar (descarta, libera as reservas).
Kit reserva e debita só o próprio saldo — os componentes já foram debitados
na montagem. Produto que não controla estoque (serviço, mão de obra) entra
no ticket sem reservar nem debitar nada.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import TypedDict

from sqlalchemy.orm import Session

from app.core.exceptions import NaoEncontrado, PermissaoNegada, RegraDeNegocio
from app.modules.clientes import service as clientes_service
from app.modules.estoque import service as estoque_service
from app.modules.financeiro import service as financeiro_service
from app.modules.produtos import service as produtos_service
from app.modules.vendas import repository
from app.modules.vendas.models import (
    CanalVenda,
    FormaPagamento,
    ItemVenda,
    PagamentoVenda,
    StatusVenda,
    Venda,
)
from app.modules.vendas.repository import VendaRepositorio
from app.shared.money import to_money
from app.shared.quantidade import to_quantidade


class PagamentoEntrada(TypedDict):
    forma: str
    valor: Decimal


class ItemOfflineEntrada(TypedDict):
    produto_id: uuid.UUID
    quantidade: Decimal
    unidade_id: uuid.UUID | None
    preco_tabela: Decimal
    desconto_percentual: Decimal


@dataclass(frozen=True)
class MetricasCliente:
    quantidade_compras: int
    valor_total: Decimal
    ticket_medio: Decimal | None
    primeira_compra: datetime | None
    ultima_compra: datetime | None


def proximo_numero(repo: VendaRepositorio) -> str:
    """Sugere VD-0001, VD-0002... pulando os que já existem."""
    proximo = repo.contar() + 1
    while True:
        numero = f"VD-{proximo:04d}"
        if not repo.numero_em_uso(numero):
            return numero
        proximo += 1


def _quantidade_base(
    db: Session,
    empresa_id: uuid.UUID,
    produto_id: uuid.UUID,
    *,
    quantidade: Decimal,
    unidade_id: uuid.UUID | None,
) -> Decimal:
    if unidade_id is None:
        return to_quantidade(quantidade)
    unidade = produtos_service.obter_unidade_para_venda(db, empresa_id, produto_id, unidade_id)
    return to_quantidade(quantidade * unidade.fator)


def _resolver_cliente(
    db: Session,
    empresa_id: uuid.UUID,
    *,
    cliente_id: uuid.UUID | None,
    cliente_novo: dict | None,
) -> uuid.UUID | None:
    if cliente_id is not None:
        clientes_service.obter_cliente(db, empresa_id, cliente_id)
        return cliente_id
    if cliente_novo is not None:
        return clientes_service.criar_cliente(db, empresa_id, **cliente_novo).id
    return None


def _recalcular_totais(db: Session, venda: Venda) -> None:
    itens = repository.itens_da_venda(db, venda.id)
    subtotal = Decimal("0")
    desconto_total = Decimal("0")
    total = Decimal("0")
    for item in itens:
        subtotal += item.preco_tabela * item.quantidade
        desconto_total += item.desconto * item.quantidade
        total += item.preco_final * item.quantidade

    venda.subtotal = to_money(subtotal)
    venda.desconto_total = to_money(desconto_total)
    venda.total = to_money(total)
    db.flush()


def _venda_aberta(db: Session, empresa_id: uuid.UUID, venda_id: uuid.UUID) -> Venda:
    venda = VendaRepositorio(db, empresa_id).obter_ou_erro(venda_id)
    if venda.status is not StatusVenda.ABERTO:
        raise RegraDeNegocio("Esta venda não está mais aberta.")
    return venda


def abrir_venda(
    db: Session,
    empresa_id: uuid.UUID,
    *,
    vendedor_usuario_id: uuid.UUID,
    cliente_id: uuid.UUID | None = None,
    cliente_novo: dict | None = None,
    canal: CanalVenda = CanalVenda.PDV,
    ocorrido_em: datetime | None = None,
    id: uuid.UUID | None = None,
) -> Venda:
    repo = VendaRepositorio(db, empresa_id)

    if id is not None:
        existente = repo.obter(id)
        if existente is not None:
            return existente

    cliente_id = _resolver_cliente(db, empresa_id, cliente_id=cliente_id, cliente_novo=cliente_novo)

    venda = Venda(
        numero=proximo_numero(repo),
        cliente_id=cliente_id,
        vendedor_usuario_id=vendedor_usuario_id,
        canal=canal,
        status=StatusVenda.ABERTO,
        subtotal=Decimal("0"),
        desconto_total=Decimal("0"),
        total=Decimal("0"),
        ocorrido_em=ocorrido_em if ocorrido_em is not None else datetime.now(UTC),
    )
    if id is not None:
        venda.id = id
    return repo.adicionar(venda)


def atualizar_cliente_da_venda(
    db: Session,
    empresa_id: uuid.UUID,
    venda_id: uuid.UUID,
    *,
    cliente_id: uuid.UUID | None = None,
    cliente_novo: dict | None = None,
) -> Venda:
    venda = _venda_aberta(db, empresa_id, venda_id)
    venda.cliente_id = _resolver_cliente(
        db, empresa_id, cliente_id=cliente_id, cliente_novo=cliente_novo
    )
    db.flush()
    return venda


def adicionar_item(
    db: Session,
    empresa_id: uuid.UUID,
    venda_id: uuid.UUID,
    *,
    produto_id: uuid.UUID,
    quantidade: Decimal,
    unidade_id: uuid.UUID | None = None,
    desconto_percentual: Decimal = Decimal("0"),
    limite_desconto_percentual: Decimal | None = None,
    pode_exceder_limite: bool = False,
) -> ItemVenda:
    venda = _venda_aberta(db, empresa_id, venda_id)
    produto = produtos_service.obter_produto(db, empresa_id, produto_id)
    if not produto.vendavel:
        raise RegraDeNegocio(f"{produto.nome} não está marcado como vendável.")

    quantidade_base = _quantidade_base(
        db, empresa_id, produto.id, quantidade=quantidade, unidade_id=unidade_id
    )

    if (
        desconto_percentual > 0
        and limite_desconto_percentual is not None
        and desconto_percentual > limite_desconto_percentual
        and not pode_exceder_limite
    ):
        raise RegraDeNegocio(
            f"Desconto de {desconto_percentual}% em {produto.nome} acima do limite do "
            f"seu papel ({limite_desconto_percentual}%)."
        )

    preco_tabela = to_money(produto.preco_venda)
    desconto_unitario = to_money(preco_tabela * desconto_percentual / Decimal("100"))
    preco_final = preco_tabela - desconto_unitario

    movimento_reserva_id = None
    if produto.controla_estoque:
        reserva = estoque_service.reservar(
            db, empresa_id, produto.id, quantidade=quantidade_base, origem=f"venda:{venda.numero}"
        )
        movimento_reserva_id = reserva.id

    item = ItemVenda(
        venda_id=venda.id,
        produto_id=produto.id,
        movimento_reserva_id=movimento_reserva_id,
        quantidade=quantidade_base,
        preco_tabela=preco_tabela,
        desconto=desconto_unitario,
        preco_final=preco_final,
    )
    db.add(item)
    db.flush()
    _recalcular_totais(db, venda)
    return item


def remover_item(
    db: Session, empresa_id: uuid.UUID, venda_id: uuid.UUID, item_id: uuid.UUID
) -> None:
    venda = _venda_aberta(db, empresa_id, venda_id)
    item = repository.item_da_venda(db, venda.id, item_id)
    if item is None:
        raise NaoEncontrado("Item não encontrado nesta venda.")

    if item.movimento_reserva_id is not None:
        estoque_service.liberar_reserva(
            db, empresa_id, item.produto_id, quantidade=item.quantidade
        )

    db.delete(item)
    db.flush()
    _recalcular_totais(db, venda)


def fechar_venda(
    db: Session,
    empresa_id: uuid.UUID,
    venda_id: uuid.UUID,
    *,
    pagamentos: list[PagamentoEntrada],
) -> Venda:
    venda = _venda_aberta(db, empresa_id, venda_id)
    itens = repository.itens_da_venda(db, venda.id)
    if not itens:
        raise RegraDeNegocio("Adicione pelo menos um item antes de fechar a venda.")
    if not pagamentos:
        raise RegraDeNegocio("Informe pelo menos uma forma de pagamento.")

    soma_pagamentos = sum((to_money(p["valor"]) for p in pagamentos), Decimal("0"))
    if soma_pagamentos != venda.total:
        raise RegraDeNegocio(
            f"A soma dos pagamentos ({soma_pagamentos}) não bate com o total da venda "
            f"({venda.total})."
        )

    for item in itens:
        if item.movimento_reserva_id is not None:
            estoque_service.liberar_reserva(
                db, empresa_id, item.produto_id, quantidade=item.quantidade
            )
            saida = estoque_service.registrar_saida(
                db,
                empresa_id,
                item.produto_id,
                quantidade=item.quantidade,
                origem=f"venda:{venda.numero}",
            )
            item.movimento_estoque_id = saida.id
            item.custo_unitario = saida.custo_unitario

    for pagamento in pagamentos:
        db.add(
            PagamentoVenda(
                venda_id=venda.id, forma=pagamento["forma"], valor=to_money(pagamento["valor"])
            )
        )

    venda.status = StatusVenda.FECHADO
    venda.fechado_em = datetime.now(UTC)

    financeiro_service.registrar_lancamentos_de_venda(
        db,
        empresa_id,
        venda_id=venda.id,
        usuario_id=venda.vendedor_usuario_id,
        pagamentos=pagamentos,
        ocorrido_em=venda.fechado_em,
    )

    db.flush()
    return venda


def sincronizar_venda_offline(
    db: Session,
    empresa_id: uuid.UUID,
    *,
    id: uuid.UUID,
    vendedor_usuario_id: uuid.UUID,
    itens: list[ItemOfflineEntrada],
    pagamentos: list[PagamentoEntrada],
    ocorrido_em: datetime,
    cliente_id: uuid.UUID | None = None,
    cliente_novo: dict | None = None,
    limite_desconto_percentual: Decimal | None = None,
    pode_exceder_limite: bool = False,
) -> Venda:
    """Venda feita offline, sincronizada já completa (itens + pagamento) ao
    reconectar. Diferente do fluxo online: não passa por reserva — o
    dispositivo não tinha visibilidade em tempo real do estoque enquanto
    offline, então debita direto, permitindo saldo negativo (regra do modo
    offline, seção 5.4 do ROADMAP). O preço de cada item vem do que o
    dispositivo tinha em cache no momento da venda, não do catálogo atual —
    um reajuste de preço enquanto o caixa estava offline não afeta o que já
    foi cobrado. `id` é obrigatório e garante que reenviar depois de uma
    falha de rede não duplica a venda."""
    repo = VendaRepositorio(db, empresa_id)

    existente = repo.obter(id)
    if existente is not None:
        return existente

    cliente_id = _resolver_cliente(db, empresa_id, cliente_id=cliente_id, cliente_novo=cliente_novo)

    venda = Venda(
        numero=proximo_numero(repo),
        cliente_id=cliente_id,
        vendedor_usuario_id=vendedor_usuario_id,
        canal=CanalVenda.PDV,
        status=StatusVenda.ABERTO,
        subtotal=Decimal("0"),
        desconto_total=Decimal("0"),
        total=Decimal("0"),
        ocorrido_em=ocorrido_em,
    )
    venda.id = id
    venda = repo.adicionar(venda)

    subtotal = Decimal("0")
    desconto_total = Decimal("0")
    total = Decimal("0")

    for item_dados in itens:
        produto = produtos_service.obter_produto(db, empresa_id, item_dados["produto_id"])
        if not produto.vendavel:
            raise RegraDeNegocio(f"{produto.nome} não está marcado como vendável.")

        quantidade_base = _quantidade_base(
            db,
            empresa_id,
            produto.id,
            quantidade=item_dados["quantidade"],
            unidade_id=item_dados.get("unidade_id"),
        )

        desconto_percentual = item_dados.get("desconto_percentual") or Decimal("0")
        if (
            desconto_percentual > 0
            and limite_desconto_percentual is not None
            and desconto_percentual > limite_desconto_percentual
            and not pode_exceder_limite
        ):
            raise RegraDeNegocio(
                f"Desconto de {desconto_percentual}% em {produto.nome} acima do limite do "
                f"seu papel ({limite_desconto_percentual}%)."
            )

        preco_tabela = to_money(item_dados["preco_tabela"])
        desconto_unitario = to_money(preco_tabela * desconto_percentual / Decimal("100"))
        preco_final = preco_tabela - desconto_unitario

        movimento_estoque_id = None
        custo_unitario = None
        if produto.controla_estoque:
            saida = estoque_service.registrar_saida(
                db,
                empresa_id,
                produto.id,
                quantidade=quantidade_base,
                origem=f"venda offline:{venda.numero}",
                ocorrido_em=ocorrido_em,
            )
            movimento_estoque_id = saida.id
            custo_unitario = saida.custo_unitario

        db.add(
            ItemVenda(
                venda_id=venda.id,
                produto_id=produto.id,
                movimento_estoque_id=movimento_estoque_id,
                quantidade=quantidade_base,
                preco_tabela=preco_tabela,
                desconto=desconto_unitario,
                preco_final=preco_final,
                custo_unitario=custo_unitario,
            )
        )

        subtotal += preco_tabela * quantidade_base
        desconto_total += desconto_unitario * quantidade_base
        total += preco_final * quantidade_base

    total = to_money(total)
    soma_pagamentos = sum((to_money(p["valor"]) for p in pagamentos), Decimal("0"))
    if soma_pagamentos != total:
        raise RegraDeNegocio(
            f"A soma dos pagamentos ({soma_pagamentos}) não bate com o total da venda "
            f"({total})."
        )

    for pagamento in pagamentos:
        db.add(
            PagamentoVenda(
                venda_id=venda.id, forma=pagamento["forma"], valor=to_money(pagamento["valor"])
            )
        )

    venda.subtotal = to_money(subtotal)
    venda.desconto_total = to_money(desconto_total)
    venda.total = total
    venda.status = StatusVenda.FECHADO
    venda.fechado_em = ocorrido_em

    financeiro_service.registrar_lancamentos_de_venda(
        db,
        empresa_id,
        venda_id=venda.id,
        usuario_id=vendedor_usuario_id,
        pagamentos=pagamentos,
        ocorrido_em=ocorrido_em,
    )

    db.flush()
    return venda


def _cancelar_ticket_aberto(db: Session, empresa_id: uuid.UUID, venda: Venda) -> Venda:
    itens = repository.itens_da_venda(db, venda.id)
    for item in itens:
        if item.movimento_reserva_id is not None:
            estoque_service.liberar_reserva(
                db, empresa_id, item.produto_id, quantidade=item.quantidade
            )
    venda.status = StatusVenda.CANCELADO
    venda.cancelado_em = datetime.now(UTC)
    db.flush()
    return venda


def _cancelar_venda_fechada(db: Session, empresa_id: uuid.UUID, venda: Venda) -> Venda:
    itens = repository.itens_da_venda(db, venda.id)
    for item in itens:
        if item.movimento_estoque_id is not None:
            estorno = estoque_service.estornar_saida(
                db,
                empresa_id,
                item.produto_id,
                quantidade=item.quantidade,
                custo_unitario=item.custo_unitario or Decimal("0"),
                origem=f"cancelamento:{venda.numero}",
            )
            item.movimento_estorno_id = estorno.id
    venda.status = StatusVenda.CANCELADO
    venda.cancelado_em = datetime.now(UTC)
    db.flush()
    return venda


def cancelar_venda(
    db: Session,
    empresa_id: uuid.UUID,
    venda_id: uuid.UUID,
    *,
    pode_cancelar_fechada: bool = False,
) -> Venda:
    venda = VendaRepositorio(db, empresa_id).obter_ou_erro(venda_id)

    if venda.status is StatusVenda.CANCELADO:
        raise RegraDeNegocio("Esta venda já está cancelada.")

    if venda.status is StatusVenda.FECHADO:
        if not pode_cancelar_fechada:
            raise PermissaoNegada("Você não tem permissão para cancelar uma venda já fechada.")
        return _cancelar_venda_fechada(db, empresa_id, venda)

    return _cancelar_ticket_aberto(db, empresa_id, venda)


def obter_venda(db: Session, empresa_id: uuid.UUID, venda_id: uuid.UUID) -> Venda:
    return VendaRepositorio(db, empresa_id).obter_ou_erro(venda_id)


def listar_vendas(
    db: Session,
    empresa_id: uuid.UUID,
    *,
    status: StatusVenda | None = None,
    cliente_id: uuid.UUID | None = None,
    limite: int = 50,
    deslocamento: int = 0,
) -> list[Venda]:
    return VendaRepositorio(db, empresa_id).buscar(
        status=status, cliente_id=cliente_id, limite=limite, deslocamento=deslocamento
    )


def itens_da_venda(db: Session, venda_id: uuid.UUID) -> list[ItemVenda]:
    return repository.itens_da_venda(db, venda_id)


def pagamentos_da_venda(db: Session, venda_id: uuid.UUID) -> list[PagamentoVenda]:
    return repository.pagamentos_da_venda(db, venda_id)


def metricas_do_cliente(
    db: Session, empresa_id: uuid.UUID, cliente_id: uuid.UUID
) -> MetricasCliente:
    """Só considera vendas FECHADAS — histórico de verdade, não tickets em
    aberto ou cancelados."""
    quantidade, valor_total, primeira, ultima = VendaRepositorio(
        db, empresa_id
    ).metricas_do_cliente(cliente_id)
    valor_total = to_money(valor_total)
    ticket_medio = to_money(valor_total / quantidade) if quantidade > 0 else None
    return MetricasCliente(
        quantidade_compras=quantidade,
        valor_total=valor_total,
        ticket_medio=ticket_medio,
        primeira_compra=primeira,
        ultima_compra=ultima,
    )


def reatribuir_cliente(
    db: Session, empresa_id: uuid.UUID, *, de_cliente_id: uuid.UUID, para_cliente_id: uuid.UUID
) -> None:
    """Usado na mesclagem de clientes (módulo clientes chama isto do
    router, pra não criar import circular entre os dois services)."""
    VendaRepositorio(db, empresa_id).reatribuir_cliente(
        de_cliente_id=de_cliente_id, para_cliente_id=para_cliente_id
    )


# --- Resumo do período (relatórios, Fase 6) ------------------------------

_FUSO_NOME = "America/Sao_Paulo"
_BRASILIA = timezone(timedelta(hours=-3))


def hoje() -> date:
    """Data de hoje no horário de Brasília (o servidor roda em UTC)."""
    return datetime.now(_BRASILIA).date()


@dataclass
class DiaVendas:
    data: date
    quantidade: int
    faturamento: Decimal


@dataclass
class ProdutoVendido:
    produto_id: uuid.UUID
    quantidade: Decimal
    receita: Decimal


@dataclass
class ResumoVendas:
    inicio: date
    fim: date
    quantidade_vendas: int
    faturamento: Decimal
    ticket_medio: Decimal | None
    descontos: Decimal
    cancelamentos: int
    # Custo das mercadorias vendidas. Quem expõe decide se mostra (custo é
    # restrito por permissão).
    custo_total: Decimal
    por_dia: list[DiaVendas]
    mais_vendidos: list[ProdutoVendido]
    por_forma_pagamento: list[tuple[FormaPagamento, Decimal]]


def resumo_do_periodo(
    db: Session,
    empresa_id: uuid.UUID,
    *,
    inicio: date,
    fim: date,
    limite_produtos: int = 5,
) -> ResumoVendas:
    """Resumo das vendas FECHADAS entre `inicio` e `fim` (inclusive), em
    dias do horário de Brasília. Cancelada não conta como faturamento."""
    if fim < inicio:
        raise RegraDeNegocio("A data final não pode ser anterior à inicial.")
    if (fim - inicio).days >= 366:
        raise RegraDeNegocio("O período máximo é de um ano.")

    de = datetime.combine(inicio, time.min, tzinfo=_BRASILIA)
    ate = datetime.combine(fim + timedelta(days=1), time.min, tzinfo=_BRASILIA)
    repo = VendaRepositorio(db, empresa_id)

    quantidade, faturamento, descontos = repo.totais_do_periodo(de, ate)
    faturamento = to_money(faturamento)
    return ResumoVendas(
        inicio=inicio,
        fim=fim,
        quantidade_vendas=quantidade,
        faturamento=faturamento,
        ticket_medio=to_money(faturamento / quantidade) if quantidade > 0 else None,
        descontos=to_money(descontos),
        cancelamentos=repo.cancelamentos_do_periodo(de, ate),
        custo_total=to_money(repo.custo_do_periodo(de, ate)),
        por_dia=[
            DiaVendas(dia, qtd, to_money(total))
            for dia, qtd, total in repo.faturamento_por_dia(de, ate, _FUSO_NOME)
        ],
        mais_vendidos=[
            ProdutoVendido(produto_id, to_quantidade(qtd), to_money(receita))
            for produto_id, qtd, receita in repo.produtos_mais_vendidos(de, ate, limite_produtos)
        ],
        por_forma_pagamento=[
            (forma, to_money(valor)) for forma, valor in repo.recebido_por_forma(de, ate)
        ],
    )


@dataclass
class ClienteDoPeriodo:
    cliente_id: uuid.UUID
    compras: int
    valor: Decimal


@dataclass
class ResumoClientes:
    inicio: date
    fim: date
    clientes_que_compraram: int
    novos: int
    recorrentes: int
    compras_de_clientes: int
    valor_de_clientes: Decimal
    ticket_medio: Decimal | None
    compras_por_cliente: Decimal | None
    vendas_sem_cliente: int
    valor_sem_cliente: Decimal
    melhores: list[ClienteDoPeriodo]


def resumo_de_clientes(
    db: Session,
    empresa_id: uuid.UUID,
    *,
    inicio: date,
    fim: date,
    limite: int = 5,
) -> ResumoClientes:
    """Novo = a primeira compra fechada dele (de sempre) caiu no período;
    recorrente = já tinha comprado antes. Só vendas fechadas de clientes
    identificados entram nas médias; o resto aparece como "sem cliente"."""
    if fim < inicio:
        raise RegraDeNegocio("A data final não pode ser anterior à inicial.")
    if (fim - inicio).days >= 366:
        raise RegraDeNegocio("O período máximo é de um ano.")

    de = datetime.combine(inicio, time.min, tzinfo=_BRASILIA)
    ate = datetime.combine(fim + timedelta(days=1), time.min, tzinfo=_BRASILIA)
    repo = VendaRepositorio(db, empresa_id)

    linhas = repo.compras_por_cliente(de, ate)
    primeiras = repo.primeira_compra_de([cliente_id for cliente_id, _, _ in linhas])
    novos = sum(1 for cliente_id, _, _ in linhas if primeiras[cliente_id] >= de)
    compras = sum(qtd for _, qtd, _ in linhas)
    valor = to_money(sum((v for _, _, v in linhas), Decimal("0")))
    sem_cliente, valor_sem_cliente = repo.vendas_sem_cliente(de, ate)

    melhores = sorted(linhas, key=lambda linha: linha[2], reverse=True)[:limite]
    return ResumoClientes(
        inicio=inicio,
        fim=fim,
        clientes_que_compraram=len(linhas),
        novos=novos,
        recorrentes=len(linhas) - novos,
        compras_de_clientes=compras,
        valor_de_clientes=valor,
        ticket_medio=to_money(valor / compras) if compras > 0 else None,
        compras_por_cliente=(
            (Decimal(compras) / Decimal(len(linhas))).quantize(Decimal("0.1")) if linhas else None
        ),
        vendas_sem_cliente=sem_cliente,
        valor_sem_cliente=to_money(valor_sem_cliente),
        melhores=[ClienteDoPeriodo(cid, qtd, to_money(v)) for cid, qtd, v in melhores],
    )


@dataclass
class ProdutoComDesconto:
    produto_id: uuid.UUID
    desconto: Decimal
    percentual: Decimal


@dataclass
class ResumoDescontos:
    inicio: date
    fim: date
    receita_de_tabela: Decimal
    descontos: Decimal
    receita_final: Decimal
    custo_total: Decimal
    percentual_de_desconto: Decimal | None
    itens_com_desconto: int
    vendas_com_desconto: int
    produtos: list[ProdutoComDesconto]

    @property
    def lucro_sem_desconto(self) -> Decimal:
        return self.receita_de_tabela - self.custo_total

    @property
    def lucro_com_desconto(self) -> Decimal:
        return self.receita_final - self.custo_total


def resumo_de_descontos(
    db: Session,
    empresa_id: uuid.UUID,
    *,
    inicio: date,
    fim: date,
    limite: int = 5,
) -> ResumoDescontos:
    """Quanto do que se venderia a preço de tabela foi cedido em desconto.
    O custo é o gravado nos itens no fechamento; quem expõe decide se mostra."""
    if fim < inicio:
        raise RegraDeNegocio("A data final não pode ser anterior à inicial.")
    if (fim - inicio).days >= 366:
        raise RegraDeNegocio("O período máximo é de um ano.")

    de = datetime.combine(inicio, time.min, tzinfo=_BRASILIA)
    ate = datetime.combine(fim + timedelta(days=1), time.min, tzinfo=_BRASILIA)
    repo = VendaRepositorio(db, empresa_id)

    tabela, descontos, final, custo, itens, vendas = repo.itens_com_desconto(de, ate)
    tabela, descontos = to_money(tabela), to_money(descontos)
    return ResumoDescontos(
        inicio=inicio,
        fim=fim,
        receita_de_tabela=tabela,
        descontos=descontos,
        receita_final=to_money(final),
        custo_total=to_money(custo),
        percentual_de_desconto=to_money(descontos / tabela * 100) if tabela > 0 else None,
        itens_com_desconto=itens,
        vendas_com_desconto=vendas,
        produtos=[
            ProdutoComDesconto(pid, to_money(desc), to_money(desc / tab * 100) if tab > 0 else Decimal("0.00"))
            for pid, desc, tab in repo.produtos_com_mais_desconto(de, ate, limite)
        ],
    )


LIMITE_LINHAS_EXPORTACAO = 50_000


@dataclass
class LinhaVendida:
    """Um item de uma venda fechada, pronto pra exportar."""

    venda_numero: str
    ocorrido_em: datetime
    cliente_id: uuid.UUID | None
    produto_id: uuid.UUID
    quantidade: Decimal
    preco_tabela: Decimal
    desconto: Decimal
    preco_final: Decimal
    custo_unitario: Decimal | None
    formas_pagamento: list[FormaPagamento]


def itens_vendidos_no_periodo(
    db: Session, empresa_id: uuid.UUID, *, inicio: date, fim: date
) -> list[LinhaVendida]:
    """Itens de vendas fechadas no período (dias em horário de Brasília),
    em ordem cronológica, até `LIMITE_LINHAS_EXPORTACAO` linhas."""
    if fim < inicio:
        raise RegraDeNegocio("A data final não pode ser anterior à inicial.")
    if (fim - inicio).days >= 366:
        raise RegraDeNegocio("O período máximo é de um ano.")

    de = datetime.combine(inicio, time.min, tzinfo=_BRASILIA)
    ate = datetime.combine(fim + timedelta(days=1), time.min, tzinfo=_BRASILIA)
    repo = VendaRepositorio(db, empresa_id)
    pares = repo.itens_para_exportar(de, ate, LIMITE_LINHAS_EXPORTACAO)
    formas = repo.formas_por_venda(list({venda.id for _, venda in pares}))
    return [
        LinhaVendida(
            venda_numero=venda.numero,
            ocorrido_em=venda.ocorrido_em,
            cliente_id=venda.cliente_id,
            produto_id=item.produto_id,
            quantidade=item.quantidade,
            preco_tabela=item.preco_tabela,
            desconto=item.desconto,
            preco_final=item.preco_final,
            custo_unitario=item.custo_unitario,
            formas_pagamento=formas.get(venda.id, []),
        )
        for item, venda in pares
    ]
